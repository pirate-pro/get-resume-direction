from __future__ import annotations

import asyncio
import html
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.crawler.adapters.http_common import resolve_cookies
from app.crawler.base import SiteAdapter
from app.crawler.types import NormalizedJob, RawJob
from app.utils.hash import sha1_hex
from app.utils.normalizers import normalize_job

logger = logging.getLogger(__name__)

TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
STYLE_RE = re.compile(r"<style[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL)
TITLE_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
HTML_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
CITY_RE = re.compile(r">([^<>]{1,12})58同城<")
SALARY_RE = re.compile(
    r"(\d{3,6}(?:\.\d+)?\s*-\s*\d{3,6}(?:\.\d+)?\s*元(?:/|每)?(?:月|天|年)|\d{3,6}(?:\.\d+)?\s*元(?:/|每)?(?:月|天|年))"
)
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2}|\d{2}-\d{2})")
URL_RE = re.compile(
    r"""<a[^>]+href=["'](?P<href>(?:https?:)?//[^"']+?\.58\.com/[^"']+?\.shtml(?:\?[^"']*)?)["'][^>]*>(?P<title>.*?)</a>""",
    re.IGNORECASE | re.DOTALL,
)

CAPTCHA_HINTS = (
    "请输入验证码",
    "访问过于频繁",
    "点击按钮进行验证",
    "isdcaptcha",
    "firewall",
)


class Job58PublicAdapter(SiteAdapter):
    source_code = "job58_public"
    default_homepage_url = "https://www.58.com/job/"
    default_city = "bj"
    default_categories = ["cantfwy", "yewu", "caiwu", "xzbgs", "jiajiao"]

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config=config)
        self.homepage_url = str(self.config.get("homepage_url") or self.default_homepage_url).strip()
        self.city = str(self.config.get("city") or self.default_city).strip()
        self.categories = self._load_categories(self.config.get("categories"))
        self.max_pages = max(1, int(self.config.get("max_pages") or 8))
        self.max_items = max(1, int(self.config.get("max_items") or 300))
        self.fetch_detail_enabled = bool(self.config.get("fetch_detail", True))
        self.retry_count = max(1, int(self.config.get("retry_count") or 3))
        self.timeout_seconds = float(self.config.get("timeout_seconds") or 20.0)
        self.request_interval_seconds = max(0.0, float(self.config.get("request_interval_seconds") or 0.35))
        self.detail_request_interval_seconds = max(
            0.0, float(self.config.get("detail_request_interval_seconds") or 0.1)
        )
        self.fail_on_empty = bool(self.config.get("fail_on_empty", True))
        self.trust_env = bool(self.config.get("trust_env", False))
        self.proxy_url = str(self.config.get("proxy_url") or self.config.get("proxy") or "").strip() or None
        self.list_urls = self._load_list_urls(self.config.get("list_urls"))
        self.cookies = resolve_cookies(self.config, env_keys=("JOB58_COOKIE", "APP_JOB58_COOKIE"))
        self.last_crawl_meta: dict[str, object] = {}

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": self.homepage_url,
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
        seen_urls: set[str] = set()
        per_category_meta: list[dict[str, object]] = []

        try:
            targets = self._build_target_list_urls()
            for category, page, url in targets:
                page_html = await self._get_text_with_retry(url)
                if self._is_captcha_page(page_html):
                    raise RuntimeError(
                        "58 blocked/captcha page returned, provide JOB58 cookie or proxy"
                    )

                page_items = self._parse_list_items(page_html, category=category)
                if not page_items:
                    if page > 1:
                        continue
                    logger.info("job58_public list_empty category=%s page=%s url=%s", category, page, url)
                    continue

                added = 0
                for item in page_items:
                    source_url = item.get("source_url")
                    if not source_url or source_url in seen_urls:
                        continue
                    seen_urls.add(source_url)
                    items.append(item)
                    added += 1
                    if len(items) >= self.max_items:
                        break

                per_category_meta.append(
                    {
                        "category": category,
                        "page": page,
                        "page_items": len(page_items),
                        "added_items": added,
                    }
                )
                logger.info(
                    "job58_public page_fetched category=%s page=%s items=%s added=%s",
                    category,
                    page,
                    len(page_items),
                    added,
                )

                if len(items) >= self.max_items:
                    break
                if self.request_interval_seconds > 0:
                    await asyncio.sleep(self.request_interval_seconds)

            self.last_crawl_meta = {
                "source_code": self.source_code,
                "city": self.city,
                "categories": self.categories,
                "max_pages": self.max_pages,
                "max_items": self.max_items,
                "fetched_items": len(items),
                "by_category_page": per_category_meta,
            }
            if not items and self.fail_on_empty:
                raise RuntimeError("58 list empty, likely blocked or selectors changed")
            return items
        finally:
            pass

    async def fetch_detail(self, list_item: dict) -> dict:
        if not self.fetch_detail_enabled:
            return list_item
        source_url = str(list_item.get("source_url") or "").strip()
        if not source_url:
            return list_item
        html_text = await self._get_text_with_retry(source_url)
        if self._is_captcha_page(html_text):
            raise RuntimeError("58 detail blocked/captcha page returned")
        if self.detail_request_interval_seconds > 0:
            await asyncio.sleep(self.detail_request_interval_seconds)
        return {
            "source_url": source_url,
            "html": html_text,
            "list_item": list_item,
        }

    def parse_raw_job(self, list_item: dict, detail: dict | str) -> RawJob:
        detail_html: str | None = None
        source_url = self._clean_text(list_item.get("source_url"))
        title_hint = self._clean_text(list_item.get("title_hint"))
        if isinstance(detail, dict):
            source_url = self._clean_text(detail.get("source_url")) or source_url
            detail_html = self._clean_text(detail.get("html"))
        elif isinstance(detail, str):
            detail_html = detail
        if not source_url:
            raise ValueError("58 item missing source_url")

        text = self._plain_text(detail_html or "")
        title = self._extract_title(detail_html or "") or title_hint
        company_name = self._extract_company_name(detail_html or "", title, text)
        if not title or not company_name:
            raise ValueError("58 detail parse missing title/company")

        external_id = self._extract_external_id_from_url(source_url)
        if not external_id:
            external_id = f"url_{sha1_hex(source_url)[:24]}"

        salary_text = self._extract_salary(detail_html or "", text)
        city = self._extract_city(detail_html or "", source_url)
        education = self._extract_education(text)
        seniority = self._extract_experience(text)
        description = self._extract_description(detail_html or "", text)
        published_at = self._extract_published_at(detail_html or "", text)
        tags = self._extract_tags(detail_html or "", text)

        return RawJob(
            source_code=self.source_code,
            external_job_id=external_id,
            source_url=source_url,
            title=title[:255],
            company_name=company_name[:255],
            city=city,
            salary_text=salary_text,
            job_category=self._clean_text(list_item.get("category")) or self._extract_job_category(text),
            seniority=seniority,
            department=None,
            education_requirement=education,
            experience_min_months=None,
            experience_max_months=None,
            responsibilities=description,
            qualifications=None,
            description=description,
            tags=tags,
            benefits=[],
            job_type="全职",
            remote_type=None,
            skills_text=",".join([x for x in [title, description, ",".join(tags)] if x]),
            published_at=published_at,
            updated_at_source=published_at,
        )

    def normalize(self, raw: RawJob) -> NormalizedJob:
        return normalize_job(raw)

    async def crawl(self) -> list[NormalizedJob]:
        try:
            return await super().crawl()
        finally:
            await self.client.aclose()

    def _build_target_list_urls(self) -> list[tuple[str, int, str]]:
        targets: list[tuple[str, int, str]] = []
        if self.list_urls:
            for index, url in enumerate(self.list_urls, start=1):
                targets.append(("manual", index, url))
            return targets
        for category in self.categories:
            for page in range(1, self.max_pages + 1):
                if page == 1:
                    url = f"https://{self.city}.58.com/{category}/"
                else:
                    url = f"https://{self.city}.58.com/{category}/pn{page}/"
                targets.append((category, page, url))
        return targets

    async def _get_text_with_retry(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.retry_count + 1):
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                return response.text
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.retry_count:
                    break
                await asyncio.sleep(min(1.5 * attempt, 5.0))
        raise RuntimeError(f"58 request failed: {url}, reason={last_error}") from last_error

    @staticmethod
    def _is_captcha_page(text: str) -> bool:
        lowered = text.lower()
        return any(hint.lower() in lowered for hint in CAPTCHA_HINTS)

    @staticmethod
    def _parse_list_items(text: str, *, category: str) -> list[dict]:
        items: list[dict] = []
        for match in URL_RE.finditer(text):
            href = (match.group("href") or "").strip()
            if not href:
                continue
            if href.startswith("//"):
                href = f"https:{href}"
            if f"/{category}/" not in href and category != "manual":
                continue
            if any(token in href for token in ("/job.shtml", "/changecity/", "/job/")):
                continue
            title_hint = Job58PublicAdapter._plain_text(match.group("title") or "")
            if len(title_hint) < 2:
                continue
            items.append(
                {
                    "source_url": href,
                    "title_hint": title_hint[:255],
                    "external_job_id": Job58PublicAdapter._extract_external_id_from_url(href),
                    "category": category,
                }
            )
        return items

    @staticmethod
    def _extract_external_id_from_url(url: str) -> str | None:
        match = re.search(r"/(\d+)(?:x)?\.shtml", url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _extract_title(html_text: str) -> str | None:
        match = TITLE_RE.search(html_text)
        if match:
            return Job58PublicAdapter._plain_text(match.group(1))
        html_title = HTML_TITLE_RE.search(html_text)
        if html_title:
            title = Job58PublicAdapter._plain_text(html_title.group(1))
            for sep in ("-58同城", "_58同城", "【", "|58同城"):
                if sep in title:
                    title = title.split(sep, 1)[0].strip()
            return title
        return None

    @staticmethod
    def _extract_salary(html_text: str, plain_text: str) -> str | None:
        for source in (html_text, plain_text):
            match = SALARY_RE.search(source)
            if match:
                return Job58PublicAdapter._plain_text(match.group(1))
        return None

    @staticmethod
    def _extract_city(html_text: str, source_url: str) -> str | None:
        match = CITY_RE.search(html_text)
        if match:
            return Job58PublicAdapter._plain_text(match.group(1))
        url_match = re.search(r"https?://([a-z0-9-]+)\.58\.com/", source_url)
        if url_match:
            return url_match.group(1)
        return None

    @staticmethod
    def _extract_company_name(html_text: str, title: str, plain_text: str) -> str | None:
        patterns = (
            r"招聘企业[^<]{0,20}</[^>]+>\s*<[^>]*>(.*?)</",
            r"企业名称[^<]{0,20}</[^>]+>\s*<[^>]*>(.*?)</",
            r"公司名称[^<]{0,20}</[^>]+>\s*<[^>]*>(.*?)</",
            r"<a[^>]+class=[\"'][^\"']*(?:company|comp|qy)[^\"']*[\"'][^>]*>(.*?)</a>",
        )
        for pattern in patterns:
            match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
            if not match:
                continue
            value = Job58PublicAdapter._plain_text(match.group(1))
            if value and len(value) >= 2:
                return value

        html_title = HTML_TITLE_RE.search(html_text)
        if html_title:
            value = Job58PublicAdapter._plain_text(html_title.group(1))
            chunks = [x.strip() for x in re.split(r"[-_|]", value) if x.strip()]
            for chunk in chunks:
                if chunk != title and ("公司" in chunk or "企业" in chunk):
                    return chunk[:255]

        for keyword in ("有限公司", "有限责任公司", "集团"):
            pos = plain_text.find(keyword)
            if pos > 4:
                start = max(0, pos - 32)
                candidate = plain_text[start : pos + len(keyword)]
                candidate = candidate.split("\n")[-1].strip()
                if 2 <= len(candidate) <= 128:
                    return candidate
        return "58同城招聘企业"

    @staticmethod
    def _extract_education(text: str) -> str | None:
        for keyword in ("博士", "硕士", "本科", "大专", "中专", "学历不限"):
            if keyword in text:
                return keyword
        return None

    @staticmethod
    def _extract_experience(text: str) -> str | None:
        patterns = (
            r"经验不限",
            r"\d+\s*-\s*\d+\s*年",
            r"\d+\s*年(?:以上)?",
            r"应届生",
            r"在校生",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return Job58PublicAdapter._plain_text(match.group(0))
        return None

    @staticmethod
    def _extract_description(html_text: str, plain_text: str) -> str | None:
        patterns = (
            r"职位描述.*?<div[^>]*>(.*?)</div>",
            r"岗位职责.*?<div[^>]*>(.*?)</div>",
            r"职位详情.*?<div[^>]*>(.*?)</div>",
        )
        for pattern in patterns:
            match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
            if not match:
                continue
            value = Job58PublicAdapter._plain_text(match.group(1))
            if value and len(value) >= 10:
                return value[:4000]

        if "职位描述" in plain_text:
            snippet = plain_text.split("职位描述", 1)[1][:4000]
            snippet = snippet.strip()
            if snippet:
                return snippet
        return None

    @staticmethod
    def _extract_published_at(html_text: str, plain_text: str) -> datetime | None:
        update_match = re.search(r"(?:更新|发布时间)[:：]?\s*([^\s<]{2,16})", html_text)
        value = Job58PublicAdapter._plain_text(update_match.group(1)) if update_match else None
        if not value:
            date_match = DATE_RE.search(plain_text)
            if date_match:
                value = date_match.group(1)
        if not value:
            return None
        value = value.replace(".", "-").strip()
        if value == "今天":
            return datetime.now(tz=ZoneInfo("Asia/Shanghai")).astimezone(ZoneInfo("UTC"))
        if value == "昨天":
            return (
                datetime.now(tz=ZoneInfo("Asia/Shanghai")).replace(hour=0, minute=0, second=0, microsecond=0)
            ).astimezone(ZoneInfo("UTC"))
        for fmt in ("%Y-%m-%d", "%m-%d"):
            try:
                dt = datetime.strptime(value, fmt)
                if fmt == "%m-%d":
                    dt = dt.replace(year=datetime.now().year)
                return dt.replace(tzinfo=ZoneInfo("Asia/Shanghai")).astimezone(ZoneInfo("UTC"))
            except ValueError:
                continue
        return None

    @staticmethod
    def _extract_tags(html_text: str, plain_text: str) -> list[str]:
        tags: list[str] = []
        for match in re.finditer(r"<[^>]*class=[\"'][^\"']*tag[^\"']*[\"'][^>]*>(.*?)</", html_text, re.IGNORECASE):
            tag = Job58PublicAdapter._plain_text(match.group(1))
            if tag and len(tag) <= 30:
                tags.append(tag)
        for candidate in ("五险一金", "包住", "包吃", "周末双休", "加班补助", "话补", "房补"):
            if candidate in plain_text:
                tags.append(candidate)
        return list(dict.fromkeys(tags))

    @staticmethod
    def _extract_job_category(text: str) -> str | None:
        mapping = ("餐饮", "销售", "财务", "人事", "行政", "家教", "客服", "司机", "普工")
        for key in mapping:
            if key in text:
                return key
        return None

    @staticmethod
    def _plain_text(raw: str) -> str:
        if not raw:
            return ""
        value = SCRIPT_RE.sub(" ", raw)
        value = STYLE_RE.sub(" ", value)
        value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
        value = re.sub(r"</p\s*>", "\n", value, flags=re.IGNORECASE)
        value = TAG_RE.sub(" ", value)
        value = html.unescape(value)
        value = re.sub(r"[ \t\r\f\v]+", " ", value)
        value = re.sub(r"\n\s+", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()

    @staticmethod
    def _clean_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _load_categories(value: object) -> list[str]:
        if isinstance(value, list):
            items = [str(x).strip().strip("/") for x in value if str(x).strip()]
            if items:
                return items
        return list(Job58PublicAdapter.default_categories)

    @staticmethod
    def _load_list_urls(value: object) -> list[str]:
        if isinstance(value, list):
            items = [str(x).strip() for x in value if str(x).strip()]
            return list(dict.fromkeys(items))
        return []
