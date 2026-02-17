from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.crawler.adapters.http_common import resolve_cookies
from app.crawler.base import SiteAdapter
from app.crawler.types import NormalizedJob, RawJob
from app.utils.hash import sha1_hex
from app.utils.normalizers import normalize_job

logger = logging.getLogger(__name__)

EXPERIENCE_RANGE_YEAR_RE = re.compile(r"(?P<low>\d+)\s*-\s*(?P<high>\d+)\s*年")
EXPERIENCE_SINGLE_YEAR_RE = re.compile(r"(?P<year>\d+)\s*年")
EXPERIENCE_RANGE_MONTH_RE = re.compile(r"(?P<low>\d+)\s*-\s*(?P<high>\d+)\s*月")
EXPERIENCE_SINGLE_MONTH_RE = re.compile(r"(?P<month>\d+)\s*月")
CHALLENGE_HINTS = ("滑动验证", "aliyunwaf", "acw_sc__v2", "security verification", "captcha")


class Job51PublicAdapter(SiteAdapter):
    source_code = "job51_public"
    default_api_url = "https://we.51job.com/api/job/search-pc"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config=config)
        self.api_url = str(self.config.get("api_url") or self.default_api_url).strip()
        self.keywords = self._load_keywords(self.config.get("keywords"))
        self.page_size = max(1, min(50, int(self.config.get("page_size") or 20)))
        self.max_pages = max(1, int(self.config.get("max_pages") or 10))
        self.start_page = max(1, int(self.config.get("start_page") or 1))
        self.retry_count = max(1, int(self.config.get("retry_count") or 3))
        self.timeout_seconds = float(self.config.get("timeout_seconds") or 20.0)
        self.request_interval_seconds = max(0.0, float(self.config.get("request_interval_seconds") or 0.4))
        self.fail_on_empty = bool(self.config.get("fail_on_empty", True))
        self.request_method = str(self.config.get("request_method") or "GET").upper()
        self.body_type = str(self.config.get("body_type") or "none").lower()
        self.keyword_field = str(self.config.get("keyword_field") or "keyword")
        self.page_field = str(self.config.get("page_field") or "pageNum")
        self.page_size_field = str(self.config.get("page_size_field") or "pageSize")
        self.offset_field = str(self.config.get("offset_field") or "start")
        self.pagination_mode = str(self.config.get("pagination_mode") or "page")
        self.browser_mode = bool(self.config.get("browser_mode", False))
        self.browser_wait_ms = max(800, int(self.config.get("browser_wait_ms") or 3200))
        self.browser_headless = bool(self.config.get("browser_headless", True))
        self.signed_url_entries = self._load_signed_url_entries(self.config.get("signed_urls"))
        self.signed_urls = [entry["url"] for entry in self.signed_url_entries]
        self.trust_env = bool(self.config.get("trust_env", False))
        self.proxy_url = str(self.config.get("proxy_url") or self.config.get("proxy") or "").strip() or None
        self.cookies = resolve_cookies(self.config, env_keys=("JOB51_COOKIE", "APP_JOB51_COOKIE"))
        self.last_crawl_meta: dict[str, object] = {}

        base_params = self.config.get("base_params")
        if isinstance(base_params, dict):
            self.base_params = {
                str(k): str(v) for k, v in base_params.items() if k and v is not None
            }
        else:
            self.base_params = {
                "searchType": "2",
                "sortType": "0",
            }
        query_params = self.config.get("query_params")
        self.query_params = (
            {str(k): str(v) for k, v in query_params.items() if k and v is not None}
            if isinstance(query_params, dict)
            else {}
        )
        form_data = self.config.get("form_data")
        self.form_data = (
            {str(k): str(v) for k, v in form_data.items() if k and v is not None}
            if isinstance(form_data, dict)
            else {}
        )
        json_data = self.config.get("json_data")
        self.json_data = (
            {str(k): v for k, v in json_data.items() if k and v is not None}
            if isinstance(json_data, dict)
            else {}
        )

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://we.51job.com/pc/search",
            "Origin": "https://we.51job.com",
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
        if self.browser_mode:
            return await self._fetch_list_from_browser()
        if self.signed_url_entries:
            return await self._fetch_list_from_signed_urls()

        items: list[dict] = []
        seen_ids: set[str] = set()
        by_keyword: list[dict[str, object]] = []

        for keyword in self.keywords:
            pages_fetched = 0
            seen_count = 0
            for page in range(self.start_page, self.start_page + self.max_pages):
                payload = await self._request_page_with_retry(keyword=keyword, page=page)
                page_items = self._extract_items(payload)
                if not page_items:
                    break

                pages_fetched += 1
                for item in page_items:
                    external_id = self._extract_external_id(item)
                    if not external_id or external_id in seen_ids:
                        continue
                    seen_ids.add(external_id)
                    items.append(item)
                    seen_count += 1

                logger.info("job51_public page_fetched keyword=%s page=%s items=%s", keyword, page, len(page_items))
                if self.request_interval_seconds > 0:
                    await asyncio.sleep(self.request_interval_seconds)

                total = self._extract_total(payload)
                if total > 0 and (page - self.start_page + 1) * self.page_size >= total:
                    break

            by_keyword.append({"keyword": keyword, "pages_fetched": pages_fetched, "unique_items_added": seen_count})

        self.last_crawl_meta = {
            "source_code": self.source_code,
            "keywords": self.keywords,
            "page_size": self.page_size,
            "max_pages": self.max_pages,
            "request_method": self.request_method,
            "body_type": self.body_type,
            "pagination_mode": self.pagination_mode,
            "fetched_items": len(items),
            "by_keyword": by_keyword,
        }
        if not items and self.fail_on_empty:
            raise RuntimeError("51job blocked/empty response, provide valid cookie and request template")
        return items

    async def _fetch_list_from_signed_urls(self) -> list[dict]:
        items: list[dict] = []
        seen_ids: set[str] = set()
        by_url: list[dict[str, object]] = []
        failed_urls: list[str] = []

        for entry in self.signed_url_entries:
            raw_url = entry["url"]
            try:
                payload = await self._request_json_with_retry(
                    url=raw_url,
                    params=None,
                    data=None,
                    json_payload=None,
                    method_override="GET",
                    headers_override=entry.get("headers"),
                )
            except Exception as exc:  # noqa: BLE001
                failed_urls.append(raw_url)
                by_url.append(
                    {
                        "url": raw_url,
                        "has_headers_override": bool(entry.get("headers")),
                        "items_count": 0,
                        "unique_items_added": 0,
                        "error": str(exc),
                    }
                )
                logger.warning("job51_public signed_url_failed url=%s error=%s", raw_url, str(exc))
                continue

            page_items = self._extract_items(payload)
            added = 0
            for item in page_items:
                external_id = self._extract_external_id(item)
                if not external_id or external_id in seen_ids:
                    continue
                seen_ids.add(external_id)
                items.append(item)
                added += 1
            by_url.append(
                {
                    "url": raw_url,
                    "has_headers_override": bool(entry.get("headers")),
                    "items_count": len(page_items),
                    "unique_items_added": added,
                }
            )
            if self.request_interval_seconds > 0:
                await asyncio.sleep(self.request_interval_seconds)

        self.last_crawl_meta = {
            "source_code": self.source_code,
            "mode": "signed_urls",
            "signed_url_count": len(self.signed_url_entries),
            "fetched_items": len(items),
            "failed_url_count": len(failed_urls),
            "by_signed_url": by_url,
        }
        if not items and self.fail_on_empty:
            raise RuntimeError(
                "51job signed_urls mode returned empty, refresh signed URL and headers"
                f", failed_url_count={len(failed_urls)}"
            )
        return items

    async def _fetch_list_from_browser(self) -> list[dict]:
        try:
            from playwright.async_api import BrowserContext, Page, async_playwright
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("browser_mode requires playwright installed") from exc

        seen_ids: set[str] = set()
        items: list[dict] = []
        by_keyword: list[dict[str, object]] = []
        captured_payloads = 0
        response_tasks: list[asyncio.Task[None]] = []

        async def flush_response_tasks() -> None:
            if not response_tasks:
                return
            pending = list(response_tasks)
            response_tasks.clear()
            await asyncio.gather(*pending, return_exceptions=True)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.browser_headless)
            context_kwargs: dict[str, Any] = {}
            browser_user_agent = self.config.get("browser_user_agent")
            if browser_user_agent:
                context_kwargs["user_agent"] = str(browser_user_agent)
            context: BrowserContext = await browser.new_context(**context_kwargs)
            page: Page = await context.new_page()

            async def process_response(resp) -> None:
                nonlocal captured_payloads
                if "/api/job/search-pc?" not in resp.url:
                    return
                if resp.status != 200:
                    return
                try:
                    payload = await resp.json()
                except Exception:  # noqa: BLE001
                    return
                if not isinstance(payload, dict):
                    return
                page_items = self._extract_items(payload)
                if not page_items:
                    return
                captured_payloads += 1
                for item in page_items:
                    external_id = self._extract_external_id(item)
                    if not external_id or external_id in seen_ids:
                        continue
                    seen_ids.add(external_id)
                    items.append(item)

            def on_response(resp) -> None:
                response_tasks.append(asyncio.create_task(process_response(resp)))

            page.on("response", on_response)

            await page.goto("https://we.51job.com/pc/search", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(self.browser_wait_ms)
            await flush_response_tasks()

            for keyword in self.keywords:
                before = len(items)
                await page.fill("#keywordInput", keyword)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(self.browser_wait_ms)
                await flush_response_tasks()

                pages_fetched = 1
                for page_no in range(2, self.max_pages + 1):
                    next_btn = page.locator(".btn-next").first
                    if await next_btn.count() == 0:
                        break
                    disabled = await next_btn.get_attribute("disabled")
                    class_name = (await next_btn.get_attribute("class")) or ""
                    if disabled is not None or "is-disabled" in class_name:
                        break
                    await next_btn.click()
                    await page.wait_for_timeout(self.browser_wait_ms)
                    await flush_response_tasks()
                    pages_fetched = page_no

                added = len(items) - before
                by_keyword.append(
                    {
                        "keyword": keyword,
                        "pages_fetched": pages_fetched,
                        "unique_items_added": added,
                    }
                )

            await flush_response_tasks()
            await browser.close()

        self.last_crawl_meta = {
            "source_code": self.source_code,
            "mode": "browser_mode",
            "keywords": self.keywords,
            "max_pages": self.max_pages,
            "captured_payloads": captured_payloads,
            "fetched_items": len(items),
            "by_keyword": by_keyword,
        }
        if not items and self.fail_on_empty:
            raise RuntimeError("51job browser_mode returned empty, likely blocked by anti-bot")
        return items

    async def fetch_detail(self, list_item: dict) -> dict:
        return list_item

    def parse_raw_job(self, list_item: dict, detail: dict | str) -> RawJob:
        if not isinstance(detail, dict):
            raise ValueError("job51 adapter expects dict detail")

        external_id = self._extract_external_id(detail)
        title = self._clean_text(
            detail.get("jobName")
            or detail.get("jobname")
            or detail.get("positionName")
            or detail.get("name")
            or detail.get("job_title")
        )
        company_name = self._extract_company_name(detail)
        if not external_id or not title or not company_name:
            raise ValueError("51job item missing required fields")

        source_url = self._clean_text(
            detail.get("jobHref")
            or detail.get("job_url")
            or detail.get("jobUrl")
            or detail.get("href")
            or detail.get("job_href")
        )
        if not source_url:
            source_url = f"https://jobs.51job.com/all/co{external_id}.html"

        education = self._clean_text(detail.get("degreeString") or detail.get("degree") or detail.get("education"))
        experience = self._clean_text(detail.get("workYearString") or detail.get("workYear") or detail.get("experience"))
        exp_min, exp_max = self._parse_experience_months(experience)

        description = self._clean_text(
            detail.get("jobSummary")
            or detail.get("jobDesc")
            or detail.get("jobDescription")
            or detail.get("description")
        )
        city = self._clean_text(
            detail.get("jobAreaString")
            or detail.get("workareaText")
            or detail.get("jobArea")
            or detail.get("jobarea")
            or detail.get("city")
        )
        salary_text = self._clean_text(
            detail.get("provideSalaryString")
            or detail.get("salary")
            or detail.get("salaryString")
            or detail.get("salaryDesc")
        )
        tags = self._extract_tags(detail)
        remote_type = "remote" if any("远程" in text for text in [title, description or "", ",".join(tags)]) else None

        return RawJob(
            source_code=self.source_code,
            external_job_id=external_id,
            source_url=source_url,
            title=title[:255],
            company_name=company_name[:255],
            city=city,
            salary_text=salary_text,
            job_category=self._clean_text(detail.get("jobType") or detail.get("funtype")),
            seniority=experience,
            department=None,
            education_requirement=education,
            experience_min_months=exp_min,
            experience_max_months=exp_max,
            responsibilities=description,
            qualifications=None,
            description=description,
            tags=tags,
            benefits=[],
            job_type=self._clean_text(detail.get("jobType") or detail.get("jobKind")),
            remote_type=remote_type,
            skills_text=",".join([x for x in [title, description, ",".join(tags)] if x]),
            published_at=self._parse_datetime(
                detail.get("issueDate")
                or detail.get("publishTime")
                or detail.get("updatedDate")
            ),
            updated_at_source=self._parse_datetime(
                detail.get("updatedDate")
                or detail.get("issueDate")
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

    async def _request_page_with_retry(self, *, keyword: str, page: int) -> dict:
        context = {
            "keyword": keyword,
            "page": page,
            "page_size": self.page_size,
            "offset": max(0, (page - self.start_page) * self.page_size),
        }

        if self.request_method == "GET":
            params = self._build_query(context)
            return await self._request_json_with_retry(url=self.api_url, params=params, data=None, json_payload=None)

        params = self._build_query(context)
        if self.body_type == "json":
            payload = self._build_json_body(context)
            return await self._request_json_with_retry(url=self.api_url, params=params, data=None, json_payload=payload)

        # default POST form
        form = self._build_form_body(context)
        return await self._request_json_with_retry(url=self.api_url, params=params, data=form, json_payload=None)

    def _build_query(self, context: dict[str, object]) -> dict[str, str | int]:
        if self.request_method == "GET" and not self.query_params:
            params: dict[str, str | int] = dict(self.base_params)
            params[self.keyword_field] = str(context["keyword"])
            if self.pagination_mode == "offset":
                params[self.offset_field] = int(context["offset"])
            else:
                params[self.page_field] = int(context["page"])
            params[self.page_size_field] = int(context["page_size"])
            return params

        source = self.query_params
        params: dict[str, str | int] = {}
        for key, value in source.items():
            params[key] = self._format_template_value(value, context)
        return params

    def _build_form_body(self, context: dict[str, object]) -> dict[str, str]:
        source = self.form_data
        if not source:
            form: dict[str, str] = {}
            form[self.keyword_field] = str(context["keyword"])
            if self.pagination_mode == "offset":
                form[self.offset_field] = str(context["offset"])
            else:
                form[self.page_field] = str(context["page"])
            form[self.page_size_field] = str(context["page_size"])
            return form

        form: dict[str, str] = {}
        for key, value in source.items():
            form[key] = str(self._format_template_value(value, context))
        return form

    def _build_json_body(self, context: dict[str, object]) -> dict:
        source = self.json_data
        if not source:
            payload: dict[str, object] = {
                self.keyword_field: context["keyword"],
                self.page_size_field: context["page_size"],
            }
            if self.pagination_mode == "offset":
                payload[self.offset_field] = context["offset"]
            else:
                payload[self.page_field] = context["page"]
            return payload
        return {key: self._format_template_value(value, context) for key, value in source.items()}

    @staticmethod
    def _format_template_value(value: object, context: dict[str, object]) -> object:
        if isinstance(value, str):
            out = value
            for key, v in context.items():
                out = out.replace(f"{{{key}}}", str(v))
            if out.isdigit():
                return int(out)
            return out
        return value

    async def _request_json_with_retry(
        self,
        *,
        url: str,
        params: dict[str, str | int] | None,
        data: dict[str, str] | None,
        json_payload: dict | None,
        method_override: str | None = None,
        headers_override: dict[str, str] | None = None,
    ) -> dict:
        last_error: Exception | None = None
        method = (method_override or self.request_method).upper()
        request_headers: dict[str, str] | None = None
        if headers_override:
            request_headers = {
                str(k): str(v)
                for k, v in headers_override.items()
                if k and v is not None and str(v).strip()
            }
            for key in list(request_headers.keys()):
                if key.lower() in {"accept-encoding", "content-length", "host", "connection"}:
                    request_headers.pop(key, None)

        for attempt in range(1, self.retry_count + 1):
            try:
                if method == "GET":
                    response = await self.client.get(url, params=params, headers=request_headers)
                elif method == "POST":
                    response = await self.client.post(
                        url,
                        params=params,
                        data=data,
                        json=json_payload,
                        headers=request_headers,
                    )
                else:
                    raise RuntimeError(f"unsupported request_method: {method}")
                raw_bytes = response.content
                text = raw_bytes.decode("utf-8", errors="ignore")
                lowered = text.lower()
                if any(token in lowered for token in CHALLENGE_HINTS):
                    raise RuntimeError("51job anti-bot challenge detected, login cookie required")

                content_type = str(response.headers.get("content-type") or "").lower()
                if "application/json" not in content_type:
                    if response.status_code >= 400:
                        snippet = raw_bytes[:120]
                        raise RuntimeError(
                            f"51job http_{response.status_code} non_json_body_prefix={snippet!r}"
                        )
                    raise RuntimeError("51job non-json response, likely anti-bot challenge")

                payload: dict
                try:
                    payload = response.json()
                except Exception:
                    payload = {}
                    for encoding in ("utf-8", "gbk"):
                        try:
                            parsed = json.loads(raw_bytes.decode(encoding, errors="ignore"))
                        except Exception:  # noqa: BLE001
                            continue
                        if isinstance(parsed, dict):
                            payload = parsed
                            break
                if not isinstance(payload, dict):
                    return {}
                status = str(payload.get("status") or payload.get("code") or "").strip()
                message = self._clean_text(payload.get("message")) or self._clean_text(payload.get("msg")) or ""
                if status in {"110011"} or "鉴权失败" in message or "签名错误" in message:
                    raise RuntimeError("51job cupid signature invalid, refresh latest signed request")
                if status == "10002" or "签名不正确" in message:
                    raise RuntimeError("51job vapi signature invalid, refresh latest type__1260 token")
                if response.status_code >= 400:
                    raise RuntimeError(f"51job http_{response.status_code}: {message or status or 'unknown'}")
                return payload
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry_count:
                    break
                await asyncio.sleep(min(1.5 * attempt, 5.0))
        raise RuntimeError(f"51job request failed: {url}, reason={last_error}") from last_error

    @staticmethod
    def _load_signed_url_entries(value: object) -> list[dict[str, object]]:
        entries: list[dict[str, object]] = []
        if not isinstance(value, list):
            return entries
        for item in value:
            if isinstance(item, str):
                url = item.strip()
                if url:
                    entries.append({"url": url, "headers": None})
                continue
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "").strip()
            if not url:
                continue
            headers_raw = item.get("headers")
            headers = (
                {str(k): str(v) for k, v in headers_raw.items() if k and v is not None}
                if isinstance(headers_raw, dict)
                else None
            )
            entries.append({"url": url, "headers": headers})
        return entries

    @staticmethod
    def _extract_items(payload: dict) -> list[dict]:
        candidates: list[object] = []
        for key in ("items", "list", "results", "rows"):
            candidates.append(payload.get(key))

        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("items", "list", "results", "rows"):
                candidates.append(data.get(key))

        resultbody = payload.get("resultbody")
        if isinstance(resultbody, dict):
            for key in ("items", "list", "results", "rows"):
                candidates.append(resultbody.get(key))
            job = resultbody.get("job")
            if isinstance(job, dict):
                for key in ("items", "list", "results", "rows"):
                    candidates.append(job.get(key))

        for candidate in candidates:
            if isinstance(candidate, list):
                rows = [row for row in candidate if isinstance(row, dict)]
                if rows:
                    return rows
        return []

    @staticmethod
    def _extract_total(payload: dict) -> int:
        for key in ("total", "totalCount", "count"):
            total = Job51PublicAdapter._to_int(payload.get(key))
            if total > 0:
                return total
        data = payload.get("data")
        if isinstance(data, dict):
            for key in ("total", "totalCount", "count"):
                total = Job51PublicAdapter._to_int(data.get(key))
                if total > 0:
                    return total
        resultbody = payload.get("resultbody")
        if isinstance(resultbody, dict):
            for key in ("total", "totalCount", "count"):
                total = Job51PublicAdapter._to_int(resultbody.get(key))
                if total > 0:
                    return total
            job = resultbody.get("job")
            if isinstance(job, dict):
                for key in ("total", "totalCount", "count"):
                    total = Job51PublicAdapter._to_int(job.get(key))
                    if total > 0:
                        return total
        return 0

    @staticmethod
    def _extract_external_id(item: dict) -> str:
        for key in ("jobId", "jobid", "id", "positionId", "number"):
            value = item.get(key)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text

        for key in ("jobHref", "job_url", "jobUrl", "href", "job_href"):
            url = item.get(key)
            if not url:
                continue
            text = str(url).strip()
            if not text:
                continue
            return f"url_{sha1_hex(text)[:24]}"
        return ""

    @staticmethod
    def _extract_company_name(item: dict) -> str:
        for key in ("fullCompanyName", "companyName", "companyname", "company"):
            value = item.get(key)
            if isinstance(value, dict):
                text = Job51PublicAdapter._clean_text(value.get("name") or value.get("companyName"))
                if text:
                    return text
            text = Job51PublicAdapter._clean_text(value)
            if text:
                return text
        return ""

    @staticmethod
    def _extract_tags(item: dict) -> list[str]:
        tags: list[str] = []
        for key in ("jobTags", "welfare", "benefits", "welfareTagList"):
            value = item.get(key)
            if isinstance(value, list):
                for tag in value:
                    if isinstance(tag, dict):
                        text = Job51PublicAdapter._clean_text(tag.get("name") or tag.get("label"))
                        if text:
                            tags.append(text)
                    elif isinstance(tag, str):
                        text = tag.strip()
                        if text:
                            tags.append(text)
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
            "%m-%d",
        ):
            try:
                dt = datetime.strptime(text, fmt)
                if fmt == "%m-%d":
                    dt = dt.replace(year=datetime.now().year)
                return dt.replace(tzinfo=ZoneInfo("Asia/Shanghai")).astimezone(ZoneInfo("UTC"))
            except ValueError:
                continue
        return None

    @staticmethod
    def _load_keywords(value: object) -> list[str]:
        if isinstance(value, list):
            items = [str(x).strip() for x in value if str(x).strip()]
            if items:
                return items
        return ["后端", "Java", "实习"]
