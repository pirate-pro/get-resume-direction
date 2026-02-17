from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.crawler.base import SiteAdapter
from app.crawler.types import NormalizedJob, RawJob
from app.utils.normalizers import normalize_job

logger = logging.getLogger(__name__)

EXPERIENCE_RANGE_YEAR_RE = re.compile(r"(?P<low>\d+)\s*-\s*(?P<high>\d+)\s*年")
EXPERIENCE_SINGLE_YEAR_RE = re.compile(r"(?P<year>\d+)\s*年")
EXPERIENCE_RANGE_MONTH_RE = re.compile(r"(?P<low>\d+)\s*-\s*(?P<high>\d+)\s*月")
EXPERIENCE_SINGLE_MONTH_RE = re.compile(r"(?P<month>\d+)\s*月")


class IGuoPinJobsAdapter(SiteAdapter):
    source_code = "iguopin_jobs"
    default_base_url = "https://gp-api.iguopin.com"
    default_site_url = "https://www.iguopin.com"
    default_job_natures = ["113Fc6wc", "114BeBeq", "115xW5oQ", "11bTac9"]
    default_headers = {
        "User-Agent": "Mozilla/5.0",
        "Device": "pc",
        "Version": "5.2.300",
        "Subsite": "iguopin",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config=config)
        self.base_url = str(self.config.get("base_url") or self.default_base_url).rstrip("/")
        self.site_url = str(self.config.get("site_url") or self.default_site_url).rstrip("/")
        self.list_path = str(self.config.get("list_path") or "/api/jobs/v1/list")
        self.detail_path = str(self.config.get("detail_path") or "/api/jobs/v1/info")
        self.page_size = max(1, min(100, int(self.config.get("page_size") or 30)))
        self.max_pages = max(1, int(self.config.get("max_pages") or 30))
        self.max_items = max(1, int(self.config.get("max_items") or 5000))
        self.retry_count = max(1, int(self.config.get("retry_count") or 4))
        self.timeout_seconds = float(self.config.get("timeout_seconds") or 20.0)
        self.request_interval_seconds = max(0.0, float(self.config.get("request_interval_seconds") or 0.2))
        self.fetch_detail_enabled = bool(self.config.get("fetch_detail", False))
        self.query_city = str(self.config.get("query_city") or "").strip() or None
        self.query_keyword = str(self.config.get("query_keyword") or "").strip() or None
        self.trust_env = bool(self.config.get("trust_env", False))
        self.proxy_url = str(self.config.get("proxy_url") or self.config.get("proxy") or "").strip() or None
        config_cookies = self.config.get("cookies")
        self.cookies = (
            {str(k): str(v) for k, v in config_cookies.items() if v is not None}
            if isinstance(config_cookies, dict)
            else None
        )
        self.last_crawl_meta: dict[str, object] = {}

        natures = self.config.get("job_natures")
        if isinstance(natures, list) and natures:
            self.job_natures = [str(x).strip() for x in natures if str(x).strip()]
        else:
            self.job_natures = self.default_job_natures

        headers = dict(self.default_headers)
        config_headers = self.config.get("headers")
        if isinstance(config_headers, dict):
            headers.update({str(k): str(v) for k, v in config_headers.items() if v is not None})
        client_kwargs: dict[str, object] = {
            "timeout": self.timeout_seconds,
            "headers": headers,
            "trust_env": self.trust_env,
        }
        if self.cookies:
            client_kwargs["cookies"] = self.cookies
        if self.proxy_url:
            client_kwargs["proxy"] = self.proxy_url
        self.client = httpx.AsyncClient(**client_kwargs)

    async def fetch_list(self) -> list[dict]:
        items, _ = await self._collect_list_items()
        return items

    async def fetch_detail(self, list_item: dict) -> dict:
        if not self.fetch_detail_enabled:
            return list_item

        external_id = str(list_item.get("job_id") or list_item.get("id") or "").strip()
        if not external_id:
            return list_item

        detail_payload = await self._get_json_with_retry(self.detail_path, params={"id": external_id})
        if detail_payload.get("code") == 200 and isinstance(detail_payload.get("data"), dict):
            merged = dict(list_item)
            merged.update(detail_payload["data"])
            return merged
        return list_item

    def parse_raw_job(self, list_item: dict, detail: dict | str) -> RawJob:
        if not isinstance(detail, dict):
            raise ValueError("iguopin jobs adapter expects detail dict")

        external_id = str(detail.get("job_id") or detail.get("id") or list_item.get("job_id") or "").strip()
        if not external_id:
            raise ValueError("missing job_id")

        title = str(detail.get("job_name") or list_item.get("job_name") or "").strip()
        company_name = str(detail.get("company_name") or list_item.get("company_name") or "").strip()
        if not title or not company_name:
            raise ValueError("missing required title/company_name")

        responsibilities = self._clean_text(detail.get("contents"))
        qualifications = self._clean_text(detail.get("apply_instruction"))
        notes = self._clean_text(detail.get("notes"))
        description = "\n".join([x for x in [responsibilities, qualifications, notes] if x]) or None
        salary_text = self._build_salary_text(detail)
        education_text = self._clean_text(detail.get("education_cn"))
        experience_text = self._clean_text(detail.get("experience_cn"))
        exp_min, exp_max = self._parse_experience_months(experience_text)

        tags: list[str] = []
        for value in [detail.get("recruitment_type_cn"), detail.get("nature_cn"), detail.get("category_cn")]:
            text = self._clean_text(value)
            if text:
                tags.append(text)
        tag_group = detail.get("tag_group_code_cn")
        if isinstance(tag_group, list):
            tags.extend([self._clean_text(tag) for tag in tag_group if self._clean_text(tag)])
        elif isinstance(tag_group, str):
            tags.extend([token.strip() for token in tag_group.replace("，", ",").split(",") if token.strip()])

        source_url = str(detail.get("link_url") or detail.get("source_url") or "").strip()
        if not source_url:
            source_url = f"{self.site_url}/job?id={external_id}"

        city = self._build_location_text(detail)
        remote_type = "remote" if "远程" in (description or "") else None
        job_type_hint = self._clean_text(detail.get("nature_cn") or detail.get("recruitment_type_cn"))

        return RawJob(
            source_code=self.source_code,
            external_job_id=external_id,
            source_url=source_url,
            title=title[:255],
            company_name=company_name[:255],
            city=city,
            salary_text=salary_text,
            job_category=self._clean_text(detail.get("category_cn")),
            seniority=experience_text,
            department=self._clean_text(detail.get("department_cn")),
            education_requirement=education_text,
            experience_min_months=exp_min,
            experience_max_months=exp_max,
            responsibilities=responsibilities,
            qualifications=qualifications,
            description=description,
            tags=list(dict.fromkeys(tags)),
            benefits=[],
            job_type=job_type_hint,
            remote_type=remote_type,
            skills_text=",".join([x for x in [title, self._clean_text(detail.get("category_cn")), description] if x]),
            published_at=self._parse_datetime(
                detail.get("refresh_time") or detail.get("start_time") or detail.get("create_time")
            ),
            updated_at_source=self._parse_datetime(detail.get("update_time") or detail.get("refresh_time")),
        )

    def normalize(self, raw: RawJob) -> NormalizedJob:
        return normalize_job(raw)

    async def crawl(self) -> list[NormalizedJob]:
        normalized_jobs: list[NormalizedJob] = []
        seen_ids: set[str] = set()
        seen_fingerprints: set[str] = set()

        try:
            items, nature_summaries = await self._collect_list_items()
            for index, item in enumerate(items, start=1):
                external_id = str(item.get("job_id") or item.get("id") or "").strip()
                if not external_id or external_id in seen_ids:
                    continue
                seen_ids.add(external_id)

                detail = await self.fetch_detail(item)
                try:
                    raw = self.parse_raw_job(item, detail)
                    normalized = self.normalize(raw)
                    if normalized.dedup_fingerprint in seen_fingerprints:
                        continue
                    seen_fingerprints.add(normalized.dedup_fingerprint)
                    normalized_jobs.append(normalized)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("iguopin_jobs parse_failed id=%s error=%s", external_id, str(exc))
                    continue

                if index % 20 == 0 and self.request_interval_seconds > 0:
                    await asyncio.sleep(self.request_interval_seconds)
                if len(normalized_jobs) >= self.max_items:
                    break

            self.last_crawl_meta = {
                "source_code": self.source_code,
                "base_url": self.base_url,
                "job_natures": self.job_natures,
                "page_size": self.page_size,
                "max_pages": self.max_pages,
                "max_items": self.max_items,
                "trust_env": int(self.trust_env),
                "proxy_enabled": int(bool(self.proxy_url)),
                "fetched_items": len(items),
                "normalized_items": len(normalized_jobs),
                "by_nature": nature_summaries,
            }
            logger.info("iguopin_jobs crawl_summary %s", self.last_crawl_meta)
            return normalized_jobs
        finally:
            await self.client.aclose()

    async def _collect_list_items(self) -> tuple[list[dict], list[dict[str, int | str]]]:
        items: list[dict] = []
        summaries: list[dict[str, int | str]] = []
        seen_ids: set[str] = set()

        for job_nature in self.job_natures:
            pages_fetched = 0
            list_count = 0
            unique_added = 0
            total_hint = 0

            for page in range(1, self.max_pages + 1):
                payload = {
                    "page": page,
                    "page_size": self.page_size,
                    "job_nature": job_nature,
                }
                if self.query_city:
                    payload["city"] = self.query_city
                if self.query_keyword:
                    payload["keyword"] = self.query_keyword

                page_json = await self._post_json_with_retry(self.list_path, payload)
                code = self._to_int(page_json.get("code"))
                message = str(page_json.get("msg") or "")
                if code != 200:
                    raise RuntimeError(f"iguopin jobs list api failed code={code} msg={message}")

                data = page_json.get("data")
                if not isinstance(data, dict):
                    break
                page_items = data.get("list")
                if not isinstance(page_items, list) or not page_items:
                    break

                total_hint = max(total_hint, self._to_int(data.get("total")))
                pages_fetched += 1
                list_count += len(page_items)
                for item in page_items:
                    if not isinstance(item, dict):
                        continue
                    external_id = str(item.get("job_id") or item.get("id") or "").strip()
                    if not external_id or external_id in seen_ids:
                        continue
                    seen_ids.add(external_id)
                    items.append(item)
                    unique_added += 1
                    if len(items) >= self.max_items:
                        break

                logger.info(
                    "iguopin_jobs page_fetched nature=%s page=%s size=%s total=%s",
                    job_nature,
                    page,
                    len(page_items),
                    total_hint,
                )

                if len(items) >= self.max_items:
                    break
                if total_hint > 0 and page * self.page_size >= total_hint:
                    break
                if self.request_interval_seconds > 0:
                    await asyncio.sleep(self.request_interval_seconds)

            summaries.append(
                {
                    "job_nature": job_nature,
                    "pages_fetched": pages_fetched,
                    "total_count_hint": total_hint,
                    "list_items_count": list_count,
                    "unique_items_added": unique_added,
                }
            )

            if len(items) >= self.max_items:
                break

        return items, summaries

    async def _post_json_with_retry(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    return {}
                message = str(data.get("msg") or data.get("message") or "")
                if self._is_rate_limited_message(message):
                    raise RuntimeError(f"iguopin_jobs rate_limited: {message}")
                return data
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry_count:
                    break
                await asyncio.sleep(min(1.5 * attempt, 6.0))
        raise RuntimeError(f"iguopin_jobs request failed: {url}") from last_error

    async def _get_json_with_retry(self, path: str, params: dict[str, str]) -> dict:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, dict) else {}
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry_count:
                    break
                await asyncio.sleep(min(1.5 * attempt, 6.0))
        raise RuntimeError(f"iguopin_jobs detail request failed: {url}") from last_error

    @staticmethod
    def _clean_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        return text

    @staticmethod
    def _to_int(value: object, default: int = 0) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            return default

    @staticmethod
    def _is_rate_limited_message(message: str) -> bool:
        msg = message.lower()
        return any(token in msg for token in ["访问人数过多", "too many", "rate", "限流"])

    def _build_salary_text(self, detail: dict) -> str | None:
        low = self._to_int(detail.get("min_wage"))
        high = self._to_int(detail.get("max_wage"))
        if low <= 0 and high <= 0:
            return None
        if high <= 0:
            high = low
        if low <= 0:
            low = high
        if high < low:
            low, high = high, low

        low_k = low / 1000
        high_k = high / 1000
        unit_cn = str(detail.get("wage_unit_cn") or "月")
        if "年" in unit_cn:
            return f"{low_k:g}k-{high_k:g}k/年"
        return f"{low_k:g}k-{high_k:g}k/月"

    def _build_location_text(self, detail: dict) -> str | None:
        # Prefer full city path from company info: 中国-广东-深圳-南山区 -> 广东-深圳-南山区
        company_info = detail.get("company_info") if isinstance(detail.get("company_info"), dict) else {}
        district_sources = []
        if isinstance(company_info, dict):
            district_sources.append(company_info.get("district_list"))
        district_sources.append(detail.get("district_list"))

        for district_list in district_sources:
            if not isinstance(district_list, list) or not district_list:
                continue
            first = district_list[0]
            if not isinstance(first, dict):
                continue
            area_cn = str(first.get("area_cn") or "").strip()
            if not area_cn:
                continue
            parts = [x.strip() for x in area_cn.replace("/", "-").split("-") if x.strip()]
            if parts and parts[0] in {"中国", "China"}:
                parts = parts[1:]
            if len(parts) >= 3:
                return "-".join(parts[:3])
            if parts:
                return "-".join(parts)
        return None

    @staticmethod
    def _parse_experience_months(experience_text: str | None) -> tuple[int | None, int | None]:
        if not experience_text:
            return None, None
        text = experience_text.strip()
        if not text or "不限" in text:
            return None, None

        m = EXPERIENCE_RANGE_YEAR_RE.search(text)
        if m:
            return int(m.group("low")) * 12, int(m.group("high")) * 12
        m = EXPERIENCE_SINGLE_YEAR_RE.search(text)
        if m:
            year = int(m.group("year")) * 12
            if "以上" in text:
                return year, None
            return year, year
        m = EXPERIENCE_RANGE_MONTH_RE.search(text)
        if m:
            return int(m.group("low")), int(m.group("high"))
        m = EXPERIENCE_SINGLE_MONTH_RE.search(text)
        if m:
            month = int(m.group("month"))
            if "以上" in text:
                return month, None
            return month, month
        return None, None

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(text, fmt)
                return dt.replace(tzinfo=ZoneInfo("Asia/Shanghai")).astimezone(ZoneInfo("UTC"))
            except ValueError:
                continue
        return None
