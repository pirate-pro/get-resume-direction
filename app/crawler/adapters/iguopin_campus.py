from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.crawler.campus_base import CampusEventAdapter
from app.crawler.types_event import NormalizedCampusEvent
from app.utils.hash import sha1_hex
from app.utils.time import now_utc

logger = logging.getLogger(__name__)


class IGuoPinCampusAdapter(CampusEventAdapter):
    source_code = "iguopin_campus"
    base_url = "https://api4.iguopin.com"
    aliases = ["GP_index", "brqw2022", "huoju2022", "dfgzw2022", "dzcs2022"]

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config=config)
        self.base_url = str(self.config.get("base_url") or self.base_url)
        self.trust_env = bool(self.config.get("trust_env", False))
        self.proxy_url = str(self.config.get("proxy_url") or self.config.get("proxy") or "").strip() or None
        aliases = self.config.get("aliases")
        if isinstance(aliases, list) and aliases:
            self.aliases = [str(alias).strip() for alias in aliases if str(alias).strip()]
        client_kwargs: dict[str, object] = {
            "timeout": 20.0,
            "headers": {
                "User-Agent": "JobAggregatorBot/0.1 (+https://example.com)",
                "Device": "h5",
                "Version": "5.0.0",
                "Subsite": "iguopin",
            },
            "trust_env": self.trust_env,
        }
        if self.proxy_url:
            client_kwargs["proxy"] = self.proxy_url
        self.client = httpx.AsyncClient(**client_kwargs)

    async def crawl(self) -> list[NormalizedCampusEvent]:
        now = now_utc()
        items: list[NormalizedCampusEvent] = []

        for alias in self.aliases:
            payload = {"alias": alias, "page": 1, "page_size": 30}
            for path, event_type in [
                ("/api/activity/activity/v1/jobfair", "job_fair"),
                ("/api/activity/activity/v1/interchoice", "interchoice"),
                ("/api/activity/activity/v1/conference", "talk"),
                ("/api/activity/activity/v1/company", "company_event"),
            ]:
                data = await self._post_json(path, payload)
                list_data = self._extract_list(data)
                for item in list_data:
                    event_id = str(item.get("id") or "")
                    if not event_id:
                        continue
                    title = str(item.get("short_title") or item.get("title") or "国聘校园活动").strip()
                    if not title:
                        continue

                    source_url = f"https://zp.iguopin.com/detail?id={event_id}"
                    company_name = item.get("company_name") or item.get("company_cn")
                    school_name = item.get("school_name") or item.get("school_cn")
                    city = item.get("city_name") or item.get("city")
                    venue = item.get("address") or item.get("show_place")
                    starts_at = self._parse_datetime(item.get("start_time") or item.get("hold_time"))
                    ends_at = self._parse_datetime(item.get("end_time"))

                    dedup = sha1_hex("|".join([self.source_code, event_id, title]))
                    items.append(
                        NormalizedCampusEvent(
                            source_code=self.source_code,
                            external_event_id=event_id,
                            source_url=source_url,
                            title=title[:255],
                            company_name=str(company_name) if company_name else None,
                            school_name=str(school_name) if school_name else None,
                            province=None,
                            city=str(city) if city else None,
                            venue=str(venue) if venue else None,
                            starts_at=starts_at,
                            ends_at=ends_at,
                            event_type=event_type,
                            event_status="upcoming",
                            description=str(item.get("desc") or "") or None,
                            tags=["国聘", alias],
                            registration_url=str(item.get("apply_url") or "") or None,
                            raw_payload=item if isinstance(item, dict) else None,
                            dedup_fingerprint=dedup,
                            first_crawled_at=now,
                            last_crawled_at=now,
                        )
                    )

        await self.client.aclose()
        return items

    async def _post_json(self, path: str, payload: dict) -> dict | list | None:
        url = f"{self.base_url}{path}"
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data.get("data")
            return data
        except Exception:
            logger.exception("iguopin campus call failed", extra={"url": url})
            return None

    @staticmethod
    def _extract_list(data: dict | list | None) -> list[dict]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            list_data = data.get("list")
            if isinstance(list_data, list):
                return [item for item in list_data if isinstance(item, dict)]
        return []

    @staticmethod
    def _parse_datetime(value: str | list | None) -> datetime | None:
        if isinstance(value, list) and value:
            value = str(value[0])
        if not isinstance(value, str) or not value:
            return None
        text = value.strip().replace("/", "-")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(text, fmt)
                return dt.replace(tzinfo=ZoneInfo("Asia/Shanghai")).astimezone(ZoneInfo("UTC"))
            except ValueError:
                continue
        return None
