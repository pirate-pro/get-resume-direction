from __future__ import annotations

import asyncio
import hashlib
import hmac
import html
import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.crawler.campus_base import CampusEventAdapter
from app.crawler.types_event import NormalizedCampusEvent
from app.utils.hash import sha1_hex
from app.utils.time import now_utc

logger = logging.getLogger(__name__)

SIGN_KEY_RE = re.compile(r'young_sign_key:"(?P<key>[^"]+)"')
FROM_DOMAIN_RE = re.compile(r'from_domain:"(?P<domain>[^"]+)"')
TAG_RE = re.compile(r"<[^>]+>")
DETAIL_PAGE_URL = "https://m.yingjiesheng.com/xuanjianghui/detail/xjh_{event_id}"
LEGACY_LIST_URL_TEMPLATE = (
    "https://my.yingjiesheng.com/index.php/personal/xjhinfo.htm/"
    "?page={page}&cid=&city=0&word=&province=0&schoolid=&sdate=&hyid=0"
)
LEGACY_ROW_RE = re.compile(r"<tr[^>]*>(?P<row>.*?)</tr>", re.IGNORECASE | re.DOTALL)
LEGACY_EVENT_ID_RE = re.compile(r"r_comments_e(?P<event_id>\d+)")
LEGACY_DETAIL_URL_RE = re.compile(r'href="(?P<href>/xjh-\d+-\d+-\d+\.html)"')
LEGACY_DETAIL_ID_RE = re.compile(r"/xjh-(?P<a>\d+)-(?P<b>\d+)-(?P<c>\d+)\.html")
LEGACY_CITY_RE = re.compile(r'class="i i_gray">(?P<city>[^<]+)</a>')
LEGACY_DATE_RE = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})<br")
LEGACY_COMPANY_RE = re.compile(
    r'id="r_comments_e\d+">\s*<a[^>]*>(?P<company>.*?)</a>', re.IGNORECASE | re.DOTALL
)
LEGACY_SCHOOL_RE = re.compile(r"/xuanjianghui_school_\d+\.html\"[^>]*>(?P<school>.*?)</a>", re.IGNORECASE | re.DOTALL)
LEGACY_VENUE_RE = re.compile(r'<td width="290"><span class="i">(?P<venue>.*?)</span>', re.IGNORECASE | re.DOTALL)


class YingJieShengXjhAdapter(CampusEventAdapter):
    source_code = "yingjiesheng_xjh"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config=config)
        self.api_base_url = str(self.config.get("api_base_url") or "https://youngapi.yingjiesheng.com").rstrip("/")
        self.landing_url = str(self.config.get("landing_url") or "https://www.yingjiesheng.com/")
        self.api_version = str(self.config.get("api_version") or "2.3.5")
        self.api_key = str(self.config.get("api_key") or "xy")
        self.from_domain = str(self.config.get("from_domain") or "yjs_web")
        self.partner = str(self.config.get("partner") or "")
        self.timeout_seconds = float(self.config.get("timeout_seconds") or 20.0)
        self.retry_count = max(1, int(self.config.get("retry_count") or 3))
        self.page_size = max(1, min(500, int(self.config.get("page_size") or 200)))
        self.max_pages = max(1, int(self.config.get("max_pages") or 50))
        self.fetch_detail = bool(self.config.get("fetch_detail", True))
        self.request_interval_seconds = max(0.0, float(self.config.get("request_interval_seconds") or 0.1))
        self.kx_types = self._load_kx_types(self.config.get("kx_types"))
        self.static_sign_key = str(self.config.get("young_sign_key") or "")
        self.user_agent = str(self.config.get("user_agent") or "Mozilla/5.0")
        self.include_legacy_html = bool(self.config.get("include_legacy_html", True))
        self.legacy_list_url_template = str(self.config.get("legacy_list_url_template") or LEGACY_LIST_URL_TEMPLATE)
        self.legacy_max_pages = max(1, int(self.config.get("legacy_max_pages") or 30))
        self.legacy_request_interval_seconds = max(
            0.0, float(self.config.get("legacy_request_interval_seconds") or self.request_interval_seconds)
        )
        self.trust_env = bool(self.config.get("trust_env", False))
        self.proxy_url = str(self.config.get("proxy_url") or self.config.get("proxy") or "").strip() or None
        self.last_crawl_meta: dict[str, object] = {}

        client_kwargs: dict[str, object] = {
            "timeout": self.timeout_seconds,
            "headers": {
                "User-Agent": self.user_agent,
                "Accept": "application/json,text/plain,*/*",
                "Content-Type": "application/json; charset=utf-8",
            },
            "trust_env": self.trust_env,
        }
        if self.proxy_url:
            client_kwargs["proxy"] = self.proxy_url
        self.client = httpx.AsyncClient(**client_kwargs)
        self._sign_key: str | None = self.static_sign_key or None

    async def crawl(self) -> list[NormalizedCampusEvent]:
        now = now_utc()
        try:
            await self._ensure_sign_key()
            events: list[NormalizedCampusEvent] = []
            seen_ids: set[str] = set()
            kx_summaries: list[dict[str, int]] = []
            legacy_summary: dict[str, object] | None = None

            for kx_type in self.kx_types:
                page = 1
                pages_fetched = 0
                total_count_hint = 0
                list_items_count = 0
                unique_events_added = 0

                while page <= self.max_pages:
                    list_payload = {
                        "pageSize": self.page_size,
                        "pageNum": page,
                        "kxType": kx_type,
                    }
                    list_resp = await self._signed_json_request(
                        method="POST",
                        path="open/noauth/yjs/xjh/list",
                        json_payload=list_payload,
                    )
                    xjh = ((list_resp.get("resultbody") or {}).get("xjh") or {}) if isinstance(list_resp, dict) else {}
                    items = xjh.get("items") if isinstance(xjh, dict) else None
                    if not isinstance(items, list) or not items:
                        logger.info(
                            "yingjiesheng_xjh page_empty kx_type=%s page=%s pages_fetched=%s",
                            kx_type,
                            page,
                            pages_fetched,
                        )
                        break

                    total_count = self._to_int(xjh.get("totalCount"))
                    pages_fetched += 1
                    total_count_hint = max(total_count_hint, total_count)
                    list_items_count += len(items)
                    logger.info(
                        "yingjiesheng_xjh page_fetched kx_type=%s page=%s items=%s total_count=%s",
                        kx_type,
                        page,
                        len(items),
                        total_count,
                    )
                    for item in items:
                        if not isinstance(item, dict):
                            continue

                        event_id = self._to_int(item.get("id"))
                        if event_id <= 0:
                            continue

                        detail: dict = item
                        if self.fetch_detail:
                            detail_resp = await self._signed_json_request(
                                method="GET",
                                path=f"open/noauth/yjs/xjh/{event_id}",
                            )
                            detail_body = detail_resp.get("resultbody")
                            if isinstance(detail_body, dict):
                                detail = detail_body

                        event = self._build_event(
                            now=now,
                            list_item=item,
                            detail=detail,
                            kx_type=kx_type,
                        )
                        if event is None:
                            continue
                        if event.external_event_id in seen_ids:
                            continue
                        seen_ids.add(event.external_event_id)
                        events.append(event)
                        unique_events_added += 1

                    if total_count > 0 and page * self.page_size >= total_count:
                        break
                    page += 1

                kx_summaries.append(
                    {
                        "kx_type": kx_type,
                        "pages_fetched": pages_fetched,
                        "total_count_hint": total_count_hint,
                        "list_items_count": list_items_count,
                        "unique_events_added": unique_events_added,
                    }
                )

            if self.include_legacy_html:
                try:
                    legacy_summary = await self._crawl_legacy_html(now=now, seen_ids=seen_ids, events=events)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("yingjiesheng_xjh legacy_html_failed error=%s", str(exc))
                    legacy_summary = {
                        "enabled": 1,
                        "failed": 1,
                        "error": str(exc)[:200],
                        "pages_fetched": 0,
                        "rows_seen": 0,
                        "unique_events_added": 0,
                    }

            self.last_crawl_meta = {
                "source_code": self.source_code,
                "page_size": self.page_size,
                "max_pages": self.max_pages,
                "kx_types": self.kx_types,
                "total_unique_events": len(events),
                "by_kx_type": kx_summaries,
            }
            if legacy_summary is not None:
                self.last_crawl_meta["legacy_html"] = legacy_summary
            logger.info("yingjiesheng_xjh crawl_summary %s", self.last_crawl_meta)
            return events
        finally:
            await self.client.aclose()

    async def _crawl_legacy_html(
        self,
        *,
        now: datetime,
        seen_ids: set[str],
        events: list[NormalizedCampusEvent],
    ) -> dict[str, int]:
        pages_fetched = 0
        rows_seen = 0
        unique_events_added = 0
        previous_signature: tuple[str, ...] | None = None

        for page in range(1, self.legacy_max_pages + 1):
            page_url = self.legacy_list_url_template.format(page=page)
            page_text = await self._fetch_legacy_page_with_retry(page_url)
            rows = self._parse_legacy_rows(page_text)
            if not rows:
                logger.info("yingjiesheng_xjh legacy_page_empty page=%s", page)
                break

            signature = tuple(row["external_event_id"] for row in rows[:12])
            if previous_signature is not None and signature == previous_signature:
                logger.info("yingjiesheng_xjh legacy_page_repeat page=%s", page)
                break
            previous_signature = signature

            pages_fetched += 1
            rows_seen += len(rows)
            logger.info("yingjiesheng_xjh legacy_page_fetched page=%s rows=%s", page, len(rows))
            for row in rows:
                event = self._build_event_from_legacy_row(now=now, row=row)
                if event is None:
                    continue
                if event.external_event_id in seen_ids:
                    continue
                seen_ids.add(event.external_event_id)
                events.append(event)
                unique_events_added += 1

            if self.legacy_request_interval_seconds > 0:
                await asyncio.sleep(self.legacy_request_interval_seconds)

        return {
            "enabled": 1,
            "pages_fetched": pages_fetched,
            "rows_seen": rows_seen,
            "unique_events_added": unique_events_added,
        }

    async def _fetch_legacy_page_with_retry(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                response = await self.client.get(url, follow_redirects=True)
                response.raise_for_status()
                response.encoding = "gbk"
                return response.text
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry_count:
                    break
                await asyncio.sleep(min(2.0 * attempt, 6.0))
        raise RuntimeError(f"legacy page request failed after retries: {url}") from last_error

    def _parse_legacy_rows(self, page_text: str) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for row_html in LEGACY_ROW_RE.findall(page_text):
            event_id_match = LEGACY_EVENT_ID_RE.search(row_html)
            detail_match = LEGACY_DETAIL_URL_RE.search(row_html)
            if event_id_match is None and detail_match is None:
                continue

            external_event_id = ""
            if event_id_match is not None:
                external_event_id = event_id_match.group("event_id")
            elif detail_match is not None:
                detail_id_match = LEGACY_DETAIL_ID_RE.search(detail_match.group("href"))
                if detail_id_match is not None:
                    external_event_id = str(
                        int(detail_id_match.group("a")) * 1_000_000
                        + int(detail_id_match.group("b")) * 1_000
                        + int(detail_id_match.group("c"))
                    )
            if not external_event_id:
                continue

            city_match = LEGACY_CITY_RE.search(row_html)
            date_match = LEGACY_DATE_RE.search(row_html)
            company_match = LEGACY_COMPANY_RE.search(row_html)
            school_match = LEGACY_SCHOOL_RE.search(row_html)
            venue_match = LEGACY_VENUE_RE.search(row_html)

            detail_href = detail_match.group("href") if detail_match is not None else ""
            rows.append(
                {
                    "external_event_id": external_event_id,
                    "date_text": date_match.group("date") if date_match is not None else "",
                    "city": self._clean_text(city_match.group("city") if city_match is not None else ""),
                    "title": self._clean_text(company_match.group("company") if company_match is not None else ""),
                    "school_name": self._clean_text(school_match.group("school") if school_match is not None else ""),
                    "venue": self._clean_text(venue_match.group("venue") if venue_match is not None else ""),
                    "source_url": f"https://my.yingjiesheng.com{detail_href}" if detail_href else "",
                }
            )
        return rows

    def _build_event_from_legacy_row(self, *, now: datetime, row: dict[str, str]) -> NormalizedCampusEvent | None:
        external_event_id = row.get("external_event_id", "").strip()
        title = row.get("title", "").strip()
        source_url = row.get("source_url", "").strip()
        if not external_event_id or not title or not source_url:
            return None

        starts_at = self._parse_legacy_date(row.get("date_text"))
        event_status = "upcoming"
        if starts_at and starts_at <= now:
            event_status = "done"

        city = self._none_if_empty(row.get("city", "").strip())
        school_name = self._none_if_empty(row.get("school_name", "").strip())
        venue = self._none_if_empty(row.get("venue", "").strip())

        inferred_job_fair = ("双选会" in title) or ("招聘会" in title)
        inferred_online = ("空中" in title) or ("线上" in title) or ("直播" in title)
        event_type = "job_fair" if inferred_job_fair else ("online_talk" if inferred_online else "talk")

        company_name: str | None = title
        if inferred_job_fair and len(title) > 12:
            company_name = None

        tags = ["应届生", "legacy_html"]
        if city:
            tags.append(city[:24])
        if school_name:
            tags.append(school_name[:24])
        if inferred_job_fair:
            tags.append("双选会")
        elif inferred_online:
            tags.append("空中宣讲")
        else:
            tags.append("线下宣讲")

        dedup_fingerprint = sha1_hex("|".join([self.source_code, external_event_id, title]))
        raw_payload = {"legacy_row": row}

        return NormalizedCampusEvent(
            source_code=self.source_code,
            external_event_id=external_event_id,
            source_url=source_url,
            title=title[:255],
            company_name=company_name,
            school_name=school_name,
            province=None,
            city=city,
            venue=venue,
            starts_at=starts_at,
            ends_at=None,
            event_type=event_type,
            event_status=event_status,
            description=None,
            tags=tags,
            registration_url=None,
            raw_payload=raw_payload,
            dedup_fingerprint=dedup_fingerprint,
            first_crawled_at=now,
            last_crawled_at=now,
        )

    async def _ensure_sign_key(self) -> None:
        if self._sign_key:
            return

        page_text = await self._fetch_text_with_retry(self.landing_url)
        key_match = SIGN_KEY_RE.search(page_text)
        if key_match is None:
            raise RuntimeError("failed to extract young_sign_key from landing page")

        self._sign_key = key_match.group("key")
        domain_match = FROM_DOMAIN_RE.search(page_text)
        if domain_match is not None and domain_match.group("domain"):
            self.from_domain = domain_match.group("domain")

    async def _fetch_text_with_retry(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                response = await self.client.get(url, follow_redirects=True)
                response.raise_for_status()
                return response.text
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry_count:
                    break
                await asyncio.sleep(min(2.0 * attempt, 6.0))
        raise RuntimeError(f"request failed after retries: {url}") from last_error

    async def _signed_json_request(
        self,
        *,
        method: str,
        path: str,
        json_payload: dict | None = None,
    ) -> dict:
        if not self._sign_key:
            raise RuntimeError("missing sign key")

        method_upper = method.upper()
        timestamp = int(datetime.now(tz=timezone.utc).timestamp())
        query_items: list[tuple[str, str]] = [
            ("version", self.api_version),
            ("api_key", self.api_key),
            ("timestamp", str(timestamp)),
        ]
        if self.partner:
            query_items.append(("partner", self.partner))

        query_string = urlencode(query_items)
        relative_url = f"{path}?{query_string}"
        body_text = ""
        if method_upper != "GET":
            body_text = json.dumps(json_payload or {}, ensure_ascii=False, separators=(",", ":"))

        sign_message = f"/{relative_url}{body_text}"
        sign = hmac.new(
            self._sign_key.encode("utf-8"),
            sign_message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        headers = {
            "sign": sign,
            "From-Domain": self.from_domain,
            "uuid": uuid.uuid4().hex,
            "partner": self.partner,
            "property": "%7B%7D",
            "user-token": "",
            "account-id": "",
        }
        request_url = f"{self.api_base_url}/{relative_url}"

        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                if method_upper == "GET":
                    response = await self.client.get(request_url, headers=headers)
                else:
                    response = await self.client.post(
                        request_url,
                        content=body_text.encode("utf-8"),
                        headers=headers,
                    )
                response.raise_for_status()
                payload = response.json()
                status = str(payload.get("status", ""))
                if status != "1":
                    raise RuntimeError(f"yingjiesheng api status={status}, message={payload.get('message')}")

                if self.request_interval_seconds > 0:
                    await asyncio.sleep(self.request_interval_seconds)
                return payload
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry_count:
                    break
                await asyncio.sleep(min(2.0 * attempt, 6.0))
        raise RuntimeError(f"api request failed: {method_upper} {path}") from last_error

    def _build_event(
        self,
        *,
        now: datetime,
        list_item: dict,
        detail: dict,
        kx_type: int,
    ) -> NormalizedCampusEvent | None:
        event_id = self._to_int(detail.get("id") or list_item.get("id"))
        if event_id <= 0:
            return None

        title = self._clean_text(detail.get("title") or list_item.get("title"))
        if not title:
            return None

        company_name = self._none_if_empty(self._clean_text(detail.get("coName") or list_item.get("coName")))
        school_name = self._none_if_empty(self._clean_text(detail.get("schoolName") or list_item.get("schoolName")))
        city = self._none_if_empty(self._clean_text(detail.get("cityName") or list_item.get("cityName")))
        venue = self._none_if_empty(self._clean_text(detail.get("address") or list_item.get("address")))

        starts_at = self._parse_unix_timestamp(detail.get("startTime") or list_item.get("startTime"))
        ends_at = self._parse_unix_timestamp(detail.get("endTime") or list_item.get("endTime"))

        is_online = self._to_int(detail.get("isKx") or list_item.get("isKx")) == 1 or kx_type == 1
        is_job_fair = self._to_int(detail.get("isZph") or list_item.get("isZph")) == 1
        event_type = "job_fair" if is_job_fair else ("online_talk" if is_online else "talk")

        event_status = "upcoming"
        if starts_at and starts_at <= now:
            event_status = "ongoing"
        if ends_at and ends_at <= now:
            event_status = "done"

        detail_html = detail.get("detail")
        description = None
        if isinstance(detail_html, str) and detail_html.strip():
            description = self._truncate(self._clean_text(detail_html), 8000)

        industry_name = self._none_if_empty(self._clean_text(detail.get("industryName") or list_item.get("industryName")))
        kx_data = detail.get("kxData")
        if not isinstance(kx_data, dict):
            kx_data = list_item.get("kxData")
        registration_url = None
        if isinstance(kx_data, dict):
            registration_url = self._none_if_empty(
                self._clean_text(kx_data.get("xyKxLink") or kx_data.get("kxLink") or kx_data.get("link"))
            )

        source_url = DETAIL_PAGE_URL.format(event_id=event_id)
        tags = ["应届生"]
        if is_job_fair:
            tags.append("双选会")
        elif is_online:
            tags.append("空中宣讲")
        else:
            tags.append("线下宣讲")
        if city:
            tags.append(city[:24])
        if school_name:
            tags.append(school_name[:24])
        if industry_name:
            tags.append(industry_name[:24])

        external_event_id = str(event_id)
        dedup_fingerprint = sha1_hex("|".join([self.source_code, external_event_id, title]))
        raw_payload = {"list_item": list_item, "detail": detail}

        return NormalizedCampusEvent(
            source_code=self.source_code,
            external_event_id=external_event_id,
            source_url=source_url,
            title=title[:255],
            company_name=company_name,
            school_name=school_name,
            province=None,
            city=city,
            venue=venue,
            starts_at=starts_at,
            ends_at=ends_at,
            event_type=event_type,
            event_status=event_status,
            description=description,
            tags=tags,
            registration_url=registration_url,
            raw_payload=raw_payload,
            dedup_fingerprint=dedup_fingerprint,
            first_crawled_at=now,
            last_crawled_at=now,
        )

    @staticmethod
    def _to_int(value: object) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_unix_timestamp(value: object) -> datetime | None:
        ts = YingJieShengXjhAdapter._to_int(value)
        if ts <= 0:
            return None
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    @staticmethod
    def _parse_legacy_date(value: object) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None
        text = value.strip()
        try:
            local_dt = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone(timedelta(hours=8)))
            return local_dt.astimezone(timezone.utc)
        except ValueError:
            return None

    @staticmethod
    def _clean_text(text: object) -> str:
        if not isinstance(text, str):
            return ""
        cleaned = TAG_RE.sub(" ", text)
        cleaned = html.unescape(cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def _none_if_empty(text: str) -> str | None:
        return text or None

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return text[:max_len]

    @staticmethod
    def _load_kx_types(raw_value: object) -> list[int]:
        if isinstance(raw_value, list):
            values = []
            for item in raw_value:
                try:
                    kx_type = int(item)  # type: ignore[arg-type]
                    if kx_type in (0, 1):
                        values.append(kx_type)
                except (TypeError, ValueError):
                    continue
            if values:
                return sorted(set(values))
        return [0, 1]
