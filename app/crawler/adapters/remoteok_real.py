from __future__ import annotations

import html
import re
from datetime import datetime

from app.crawler.base import SiteAdapter
from app.crawler.client import CrawlerClient
from app.crawler.types import NormalizedJob, RawJob
from app.utils.normalizers import normalize_job

TAG_RE = re.compile(r"<[^>]+>")


class RemoteOKRealAdapter(SiteAdapter):
    source_code = "remoteok_real"
    api_url = "https://remoteok.com/api"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config=config)
        timeout_seconds = int(self.config.get("timeout_seconds") or 20)
        retry_count = int(self.config.get("retry_count") or 3)
        throttle = self.config.get("throttle") if isinstance(self.config.get("throttle"), dict) else {}
        qps = float(throttle.get("qps") or 0.5)
        jitter_ms = int(throttle.get("jitter_ms") or 200)
        allow_paths = self.config.get("allow_paths") if isinstance(self.config.get("allow_paths"), list) else ["/api"]
        deny_paths = self.config.get("deny_paths") if isinstance(self.config.get("deny_paths"), list) else []
        headers = self.config.get("headers") if isinstance(self.config.get("headers"), dict) else None
        proxy_url = str(self.config.get("proxy_url") or self.config.get("proxy") or "").strip() or None
        trust_env = bool(self.config.get("trust_env", False))
        self.client = CrawlerClient(
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
            qps=qps,
            jitter_ms=jitter_ms,
            allow_paths=allow_paths,
            deny_paths=deny_paths,
            proxy=proxy_url,
            trust_env=trust_env,
            headers=headers
            or {
                "User-Agent": "JobAggregatorBot/0.1 (+https://example.com)",
                "Accept": "application/json",
            },
        )

    async def fetch_list(self) -> list[dict]:
        response = await self.client.get(self.api_url)
        payload = response.json()
        if not isinstance(payload, list):
            return []

        # The first object contains terms metadata; real jobs have numeric id.
        jobs = [item for item in payload if isinstance(item, dict) and item.get("id")]
        return jobs[:100]

    async def fetch_detail(self, list_item: dict) -> dict:
        # RemoteOK API list already includes detail fields.
        return list_item

    def parse_raw_job(self, list_item: dict, detail: dict | str) -> RawJob:
        if not isinstance(detail, dict):
            raise ValueError("RemoteOK adapter expects dict detail")

        tags = [str(tag) for tag in detail.get("tags", []) if isinstance(tag, str)]
        description = self._clean_html(detail.get("description"))

        salary_text = self._salary_text(detail.get("salary_min"), detail.get("salary_max"))
        return RawJob(
            source_code=self.source_code,
            external_job_id=str(detail.get("id") or ""),
            source_url=detail.get("apply_url") or detail.get("url") or "https://remoteok.com",
            title=str(detail.get("position") or "Unknown Position"),
            company_name=str(detail.get("company") or "Unknown Company"),
            city=self._normalize_city(detail.get("location")),
            salary_text=salary_text,
            job_category=tags[0] if tags else "Software Engineering",
            seniority="senior" if "senior" in [t.lower() for t in tags] else None,
            education_requirement="unknown",
            responsibilities=description,
            description=description,
            tags=tags,
            benefits=[],
            job_type="full_time",
            remote_type="remote",
            skills_text=",".join(tags),
            published_at=self._parse_datetime(detail.get("date")),
            updated_at_source=self._parse_datetime(detail.get("date")),
        )

    def normalize(self, raw: RawJob) -> NormalizedJob:
        return normalize_job(raw)

    async def crawl(self) -> list[NormalizedJob]:
        try:
            return await super().crawl()
        finally:
            await self.client.close()

    @staticmethod
    def _clean_html(value: str | None) -> str | None:
        if not value:
            return None
        text = html.unescape(value)
        text = TAG_RE.sub(" ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:5000]

    @staticmethod
    def _salary_text(salary_min: int | float | None, salary_max: int | float | None) -> str | None:
        if not salary_min or not salary_max:
            return None
        low = int(float(salary_min) / 1000)
        high = int(float(salary_max) / 1000)
        if low <= 0 or high <= 0:
            return None
        return f"{low}k-{high}k/year"

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _normalize_city(value: str | None) -> str:
        if not value:
            return "Remote"

        text = str(value).strip()
        for sep in [";", "/", "|", "，", ",", "·"]:
            if sep in text:
                text = text.split(sep, 1)[0].strip()

        if not text:
            return "Remote"
        if len(text) > 60:
            return "Remote"
        return text
