from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.crawler.adapters.http_common import resolve_cookies
from app.crawler.base import SiteAdapter
from app.crawler.types import NormalizedJob, RawJob
from app.utils.normalizers import normalize_job

logger = logging.getLogger(__name__)

EXPERIENCE_RANGE_YEAR_RE = re.compile(r"(?P<low>\d+)\s*-\s*(?P<high>\d+)\s*年")
EXPERIENCE_SINGLE_YEAR_RE = re.compile(r"(?P<year>\d+)\s*年")
EXPERIENCE_RANGE_MONTH_RE = re.compile(r"(?P<low>\d+)\s*-\s*(?P<high>\d+)\s*月")
EXPERIENCE_SINGLE_MONTH_RE = re.compile(r"(?P<month>\d+)\s*月")
SECURITY_HINTS = ("security verification", "captcha", "验证", "滑动")


class ZhaopinPublicAdapter(SiteAdapter):
    source_code = "zhaopin_public"
    default_api_url = "https://fe-api.zhaopin.com/c/i/sou"
    default_base_params = {
        "cityId": "530",
        "workExperience": "-1",
        "education": "-1",
        "companyType": "-1",
        "employmentType": "-1",
        "jobWelfareTag": "-1",
    }

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config=config)
        self.api_url = str(self.config.get("api_url") or self.default_api_url).strip()
        self.keywords = self._load_keywords(self.config.get("keywords"))
        self.page_size = max(1, min(90, int(self.config.get("page_size") or 30)))
        self.max_pages = max(1, int(self.config.get("max_pages") or 10))
        self.retry_count = max(1, int(self.config.get("retry_count") or 3))
        self.timeout_seconds = float(self.config.get("timeout_seconds") or 20.0)
        self.request_interval_seconds = max(0.0, float(self.config.get("request_interval_seconds") or 0.3))
        self.fail_on_empty = bool(self.config.get("fail_on_empty", True))
        self.trust_env = bool(self.config.get("trust_env", False))
        self.proxy_url = str(self.config.get("proxy_url") or self.config.get("proxy") or "").strip() or None
        self.cookies = resolve_cookies(self.config, env_keys=("ZHAOPIN_COOKIE", "APP_ZHAOPIN_COOKIE"))
        self.last_crawl_meta: dict[str, object] = {}

        base_params = self.config.get("base_params")
        if isinstance(base_params, dict):
            self.base_params = {
                str(k): str(v) for k, v in base_params.items() if k and v is not None
            }
        else:
            self.base_params = dict(self.default_base_params)

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://sou.zhaopin.com/",
        }
        config_headers = self.config.get("headers")
        if isinstance(config_headers, dict):
            headers.update({str(k): str(v) for k, v in config_headers.items() if v is not None})
        client_kwargs: dict[str, object] = {
            "timeout": self.timeout_seconds,
            "headers": headers,
            "trust_env": self.trust_env,
            "follow_redirects": True,
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
                params: dict[str, str | int] = dict(self.base_params)
                params["kw"] = keyword
                params["start"] = (page - 1) * self.page_size
                params["pageSize"] = self.page_size

                payload = await self._get_json_with_retry(self.api_url, params=params)
                data = payload.get("data")
                if not isinstance(data, dict):
                    break

                if int(data.get("isVerification") or 0) == 1:
                    raise RuntimeError("zhaopin requires verification/login cookie")

                page_items = data.get("results") or []
                if not isinstance(page_items, list) or not page_items:
                    break

                pages_fetched += 1
                for item in page_items:
                    if not isinstance(item, dict):
                        continue
                    external_id = self._extract_external_id(item)
                    if not external_id or external_id in seen_ids:
                        continue
                    seen_ids.add(external_id)
                    items.append(item)
                    seen_count += 1

                logger.info("zhaopin_public page_fetched keyword=%s page=%s items=%s", keyword, page, len(page_items))
                if self.request_interval_seconds > 0:
                    await asyncio.sleep(self.request_interval_seconds)

                total = self._to_int(data.get("numFound")) or self._to_int(data.get("numTotal"))
                if total > 0 and page * self.page_size >= total:
                    break

            by_keyword.append({"keyword": keyword, "pages_fetched": pages_fetched, "unique_items_added": seen_count})

        self.last_crawl_meta = {
            "source_code": self.source_code,
            "keywords": self.keywords,
            "page_size": self.page_size,
            "max_pages": self.max_pages,
            "fetched_items": len(items),
            "by_keyword": by_keyword,
        }
        if not items and self.fail_on_empty:
            raise RuntimeError("zhaopin blocked/empty response, please login and provide Zhaopin cookie")
        return items

    async def fetch_detail(self, list_item: dict) -> dict:
        return list_item

    def parse_raw_job(self, list_item: dict, detail: dict | str) -> RawJob:
        if not isinstance(detail, dict):
            raise ValueError("zhaopin adapter expects dict detail")

        external_id = self._extract_external_id(detail)
        title = self._clean_text(
            detail.get("jobName")
            or detail.get("positionName")
            or detail.get("name")
            or list_item.get("jobName")
            or list_item.get("positionName")
        )
        company_name = self._extract_company_name(detail)
        if not external_id or not title or not company_name:
            raise ValueError("zhaopin item missing required fields")

        source_url = self._clean_text(detail.get("positionURL") or detail.get("jobUrl"))
        if not source_url:
            source_url = f"https://jobs.zhaopin.com/{external_id}.htm"

        education = self._extract_named_value(detail.get("eduLevel")) or self._clean_text(detail.get("education"))
        experience = self._extract_named_value(detail.get("workingExp")) or self._clean_text(detail.get("workingExp"))
        exp_min, exp_max = self._parse_experience_months(experience)

        description = self._clean_text(
            detail.get("positionDetail")
            or detail.get("jobSummary")
            or detail.get("jobDesc")
            or detail.get("jobDescription")
        )
        qualifications = self._clean_text(detail.get("jobKnowledge") or detail.get("positionRequirements"))

        tags = self._extract_tags(detail)
        salary_text = self._extract_salary_text(detail)
        city = self._extract_city(detail)
        remote_type = "remote" if any("远程" in text for text in [title, description or "", ",".join(tags)]) else None

        return RawJob(
            source_code=self.source_code,
            external_job_id=external_id,
            source_url=source_url,
            title=title[:255],
            company_name=company_name[:255],
            city=city,
            salary_text=salary_text,
            job_category=self._clean_text(
                detail.get("jobType")
                or detail.get("positionLabel")
                or detail.get("industry")
            ),
            seniority=experience,
            department=None,
            education_requirement=education,
            experience_min_months=exp_min,
            experience_max_months=exp_max,
            responsibilities=description,
            qualifications=qualifications,
            description=description,
            tags=tags,
            benefits=[],
            job_type=self._clean_text(detail.get("employmentType") or detail.get("jobType")),
            remote_type=remote_type,
            skills_text=",".join([x for x in [title, description, ",".join(tags)] if x]),
            published_at=self._parse_datetime(
                detail.get("publishTime")
                or detail.get("updateDate")
                or detail.get("createDate")
            ),
            updated_at_source=self._parse_datetime(
                detail.get("updateDate")
                or detail.get("publishTime")
            ),
        )

    def normalize(self, raw: RawJob) -> NormalizedJob:
        return normalize_job(raw)

    async def crawl(self) -> list[NormalizedJob]:
        try:
            return await super().crawl()
        finally:
            await self.client.aclose()

    async def _get_json_with_retry(self, url: str, params: dict[str, str | int]) -> dict:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                content_type = (response.headers.get("content-type") or "").lower()
                text = response.text
                if "json" not in content_type:
                    lowered = text.lower()
                    if any(token in lowered for token in SECURITY_HINTS):
                        raise RuntimeError("zhaopin blocked by verification page, login cookie required")
                payload = response.json()
                if not isinstance(payload, dict):
                    return {}
                return payload
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry_count:
                    break
                await asyncio.sleep(min(1.5 * attempt, 5.0))
        raise RuntimeError(f"zhaopin request failed: {url}, reason={last_error}") from last_error

    @staticmethod
    def _extract_external_id(item: dict) -> str:
        for key in ("number", "jobNumber", "positionNumber", "jobId", "positionId", "id"):
            value = item.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    @staticmethod
    def _extract_company_name(item: dict) -> str:
        company = item.get("company")
        if isinstance(company, dict):
            for key in ("name", "companyName", "fullName"):
                text = ZhaopinPublicAdapter._clean_text(company.get(key))
                if text:
                    return text
        return ZhaopinPublicAdapter._clean_text(item.get("companyName") or item.get("company")) or ""

    @staticmethod
    def _extract_named_value(value: object) -> str | None:
        if isinstance(value, dict):
            for key in ("name", "display", "label"):
                text = ZhaopinPublicAdapter._clean_text(value.get(key))
                if text:
                    return text
        return ZhaopinPublicAdapter._clean_text(value)

    @staticmethod
    def _extract_salary_text(item: dict) -> str | None:
        salary = item.get("salary")
        if isinstance(salary, dict):
            min_v = salary.get("min")
            max_v = salary.get("max")
            unit = ZhaopinPublicAdapter._clean_text(salary.get("unit") or salary.get("unitName")) or "月"
            if min_v is not None and max_v is not None:
                return f"{min_v}-{max_v}/{unit}"
            return ZhaopinPublicAdapter._clean_text(salary.get("name") or salary.get("text"))
        return ZhaopinPublicAdapter._clean_text(salary)

    @staticmethod
    def _extract_city(item: dict) -> str | None:
        city = item.get("city")
        if isinstance(city, dict):
            for key in ("display", "name", "items"):
                value = city.get(key)
                if isinstance(value, list):
                    joined = "-".join([str(x).strip() for x in value if str(x).strip()])
                    if joined:
                        return joined
                text = ZhaopinPublicAdapter._clean_text(value)
                if text:
                    return text
        return ZhaopinPublicAdapter._clean_text(item.get("workCity") or item.get("cityDisplay") or item.get("cityName"))

    @staticmethod
    def _extract_tags(item: dict) -> list[str]:
        tags: list[str] = []
        for key in ("welfare", "positionLabel", "jobWelfare", "skillLabel"):
            value = item.get(key)
            if isinstance(value, list):
                tags.extend([str(x).strip() for x in value if str(x).strip()])
            elif isinstance(value, str):
                tags.extend([x.strip() for x in value.replace("，", ",").split(",") if x.strip()])
        return list(dict.fromkeys(tags))

    @staticmethod
    def _clean_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _to_int(value: object, default: int = 0) -> int:
        try:
            return int(value)  # type: ignore[arg-type]
        except Exception:  # noqa: BLE001
            return default

    @staticmethod
    def _parse_experience_months(experience_text: str | None) -> tuple[int | None, int | None]:
        if not experience_text:
            return None, None
        text = experience_text.strip()
        if not text or "不限" in text:
            return None, None
        match = EXPERIENCE_RANGE_YEAR_RE.search(text)
        if match:
            return int(match.group("low")) * 12, int(match.group("high")) * 12
        match = EXPERIENCE_SINGLE_YEAR_RE.search(text)
        if match:
            year = int(match.group("year")) * 12
            if "以上" in text:
                return year, None
            return year, year
        match = EXPERIENCE_RANGE_MONTH_RE.search(text)
        if match:
            return int(match.group("low")), int(match.group("high"))
        match = EXPERIENCE_SINGLE_MONTH_RE.search(text)
        if match:
            month = int(match.group("month"))
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
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ):
            try:
                dt = datetime.strptime(text, fmt)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=ZoneInfo("Asia/Shanghai")).astimezone(ZoneInfo("UTC"))
                return dt.astimezone(ZoneInfo("UTC"))
            except ValueError:
                continue
        return None

    @staticmethod
    def _load_keywords(value: object) -> list[str]:
        if isinstance(value, list):
            items = [str(x).strip() for x in value if str(x).strip()]
            if items:
                return items
        return ["后端", "Java", "校招"]
