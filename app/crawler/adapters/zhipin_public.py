from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import httpx

from app.crawler.adapters.http_common import resolve_cookies
from app.crawler.base import SiteAdapter
from app.crawler.types import NormalizedJob, RawJob
from app.utils.normalizers import normalize_job

logger = logging.getLogger(__name__)


class ZhiPinPublicAdapter(SiteAdapter):
    source_code = "zhipin_public"
    default_api_url = "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config=config)
        self.api_url = str(self.config.get("api_url") or self.default_api_url)
        self.city = str(self.config.get("city") or "101280600")
        self.keywords = self._load_keywords(self.config.get("keywords"))
        self.page_size = max(1, min(30, int(self.config.get("page_size") or 30)))
        self.max_pages = max(1, int(self.config.get("max_pages") or 10))
        self.fail_on_empty = bool(self.config.get("fail_on_empty", True))
        self.retry_count = max(1, int(self.config.get("retry_count") or 3))
        self.timeout_seconds = float(self.config.get("timeout_seconds") or 20.0)
        self.request_interval_seconds = max(0.0, float(self.config.get("request_interval_seconds") or 0.25))
        self.trust_env = bool(self.config.get("trust_env", False))
        self.proxy_url = str(self.config.get("proxy_url") or self.config.get("proxy") or "").strip() or None
        self.cookies = resolve_cookies(self.config, env_keys=("BOSS_COOKIE", "APP_BOSS_COOKIE"))
        self.last_crawl_meta: dict[str, object] = {}

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
        }
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
        items: list[dict] = []
        seen_ids: set[str] = set()
        by_keyword: list[dict[str, object]] = []

        for keyword in self.keywords:
            pages_fetched = 0
            seen_count = 0
            for page in range(1, self.max_pages + 1):
                payload = await self._get_json_with_retry(
                    self.api_url,
                    params={
                        "query": keyword,
                        "city": self.city,
                        "page": page,
                        "pageSize": self.page_size,
                    },
                )
                code = payload.get("code")
                message = str(payload.get("message") or "")
                if int(code or 0) == 37 or "异常" in message or "captcha" in message.lower():
                    raise RuntimeError(
                        "zhipin blocked/captcha, please login in browser and provide BOSS cookie "
                        f"(code={code}, message={message})"
                    )

                zp_data = payload.get("zpData")
                if not isinstance(zp_data, dict):
                    break
                page_items = zp_data.get("jobList") or zp_data.get("jobListItems") or []
                if not isinstance(page_items, list) or not page_items:
                    break

                pages_fetched += 1
                for item in page_items:
                    if not isinstance(item, dict):
                        continue
                    external_id = str(item.get("encryptJobId") or item.get("jobId") or item.get("id") or "").strip()
                    if not external_id or external_id in seen_ids:
                        continue
                    seen_ids.add(external_id)
                    items.append(item)
                    seen_count += 1

                logger.info("zhipin_public page_fetched keyword=%s page=%s items=%s", keyword, page, len(page_items))
                if self.request_interval_seconds > 0:
                    await asyncio.sleep(self.request_interval_seconds)

            by_keyword.append({"keyword": keyword, "pages_fetched": pages_fetched, "unique_items_added": seen_count})

        self.last_crawl_meta = {
            "source_code": self.source_code,
            "keywords": self.keywords,
            "city": self.city,
            "page_size": self.page_size,
            "max_pages": self.max_pages,
            "fetched_items": len(items),
            "by_keyword": by_keyword,
        }
        if not items and self.fail_on_empty:
            raise RuntimeError("zhipin blocked/empty response, please login and provide BOSS cookie")
        return items

    async def fetch_detail(self, list_item: dict) -> dict:
        return list_item

    def parse_raw_job(self, list_item: dict, detail: dict | str) -> RawJob:
        if not isinstance(detail, dict):
            raise ValueError("zhipin adapter expects dict detail")

        external_id = str(detail.get("encryptJobId") or detail.get("jobId") or detail.get("id") or "").strip()
        title = str(detail.get("jobName") or detail.get("name") or detail.get("jobTitle") or "").strip()
        company_name = str(detail.get("brandName") or detail.get("companyName") or "").strip()
        if not external_id or not title or not company_name:
            raise ValueError("zhipin item missing required fields")

        source_url = str(detail.get("jobUrl") or "").strip()
        if not source_url:
            source_url = f"https://www.zhipin.com/job_detail/{external_id}.html"

        tags = []
        labels = detail.get("skills") or detail.get("labels") or []
        if isinstance(labels, list):
            tags = [str(x).strip() for x in labels if str(x).strip()]

        return RawJob(
            source_code=self.source_code,
            external_job_id=external_id,
            source_url=source_url,
            title=title[:255],
            company_name=company_name[:255],
            city=str(detail.get("cityName") or detail.get("city") or "").strip() or None,
            salary_text=str(detail.get("salaryDesc") or detail.get("salary") or "").strip() or None,
            job_category=str(detail.get("jobType") or detail.get("positionName") or "").strip() or None,
            seniority=str(detail.get("experienceName") or detail.get("jobExperience") or "").strip() or None,
            education_requirement=str(detail.get("degreeName") or detail.get("jobDegree") or "").strip() or None,
            responsibilities=str(detail.get("jobDesc") or "").strip() or None,
            qualifications=str(detail.get("jobDesc") or "").strip() or None,
            description=str(detail.get("jobDesc") or "").strip() or None,
            tags=tags,
            benefits=[],
            job_type=str(detail.get("jobType") or "").strip() or None,
            remote_type=None,
            skills_text=",".join(tags),
            published_at=self._parse_datetime(detail.get("createTime") or detail.get("time")),
            updated_at_source=self._parse_datetime(detail.get("updateTime") or detail.get("time")),
        )

    def normalize(self, raw: RawJob) -> NormalizedJob:
        return normalize_job(raw)

    async def crawl(self) -> list[NormalizedJob]:
        try:
            return await super().crawl()
        finally:
            await self.client.aclose()

    async def _get_json_with_retry(self, url: str, params: dict) -> dict:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    return {}
                return payload
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry_count:
                    break
                await asyncio.sleep(min(1.5 * attempt, 5.0))
        raise RuntimeError(f"zhipin request failed: {url}") from last_error

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m-%d", "%H:%M"):
            try:
                parsed = datetime.strptime(text, fmt)
                if fmt in {"%m-%d", "%H:%M"}:
                    return None
                return parsed
            except ValueError:
                continue
        return None

    @staticmethod
    def _load_keywords(value: object) -> list[str]:
        if isinstance(value, list):
            items = [str(x).strip() for x in value if str(x).strip()]
            if items:
                return items
        return ["校招", "后端"]
