import argparse
import asyncio
from dataclasses import dataclass
from typing import Any

from playwright.async_api import BrowserContext, Page, async_playwright

from app.core.database import SessionLocal
from app.dao.source_dao import SourceDAO
from app.models.source import Source


HEADER_WHITELIST = {
    "accept",
    "accept-encoding",
    "accept-language",
    "account-id",
    "from-domain",
    "origin",
    "referer",
    "sec-ch-ua",
    "sec-ch-ua-mobile",
    "sec-ch-ua-platform",
    "sec-fetch-dest",
    "sec-fetch-mode",
    "sec-fetch-site",
    "sign",
    "user-agent",
    "user-token",
    "uuid",
}

HEADER_CANONICAL = {
    "accept": "Accept",
    "accept-encoding": "Accept-Encoding",
    "accept-language": "Accept-Language",
    "account-id": "Account-Id",
    "from-domain": "From-Domain",
    "origin": "Origin",
    "referer": "Referer",
    "sec-ch-ua": "Sec-Ch-Ua",
    "sec-ch-ua-mobile": "Sec-Ch-Ua-Mobile",
    "sec-ch-ua-platform": "Sec-Ch-Ua-Platform",
    "sec-fetch-dest": "Sec-Fetch-Dest",
    "sec-fetch-mode": "Sec-Fetch-Mode",
    "sec-fetch-site": "Sec-Fetch-Site",
    "sign": "Sign",
    "user-agent": "User-Agent",
    "user-token": "User-Token",
    "uuid": "Uuid",
}


@dataclass
class SignedEntry:
    url: str
    headers: dict[str, str]

    @property
    def dedup_key(self) -> str:
        return f"{self.url}|{self.headers.get('Sign', '')}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="自动采集 51job 搜索 API signed URL，并写入 source 配置")
    parser.add_argument("--source", default="job51_public", help="source code")
    parser.add_argument("--keyword", action="append", default=[], help="关键词，可多次传参")
    parser.add_argument("--max-pages", type=int, default=6, help="每个关键词最多翻页数（含第一页）")
    parser.add_argument("--headed", action="store_true", help="使用有界面模式运行浏览器（默认 headless）")
    parser.add_argument("--replace", action="store_true", help="覆盖已存在 signed_urls，默认追加")
    parser.add_argument("--enable", action="store_true", help="采集后启用 source")
    parser.add_argument("--log", action="store_true", help="打印采集明细")
    return parser.parse_args()


def _normalize_headers(raw: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in raw.items():
        k = key.lower().strip()
        if k not in HEADER_WHITELIST:
            continue
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        out[HEADER_CANONICAL.get(k, key)] = text
    return out


def _parse_existing_signed_urls(value: Any) -> list[SignedEntry]:
    rows: list[SignedEntry] = []
    if not isinstance(value, list):
        return rows
    for item in value:
        if isinstance(item, str):
            url = item.strip()
            if url:
                rows.append(SignedEntry(url=url, headers={}))
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
            else {}
        )
        rows.append(SignedEntry(url=url, headers=headers))
    return rows


async def _collect_for_keyword(page: Page, keyword: str, max_pages: int, log: bool) -> None:
    await page.fill("#keywordInput", keyword)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(3500)
    if log:
        print({"keyword": keyword, "step": "searched"})

    for page_no in range(2, max_pages + 1):
        next_btn = page.locator(".btn-next").first
        if await next_btn.count() == 0:
            break
        disabled = await next_btn.get_attribute("disabled")
        class_name = (await next_btn.get_attribute("class")) or ""
        if disabled is not None or "is-disabled" in class_name:
            break
        await next_btn.click()
        await page.wait_for_timeout(3000)
        if log:
            print({"keyword": keyword, "step": "next_page", "page_no": page_no})


async def _collect_signed_entries(
    *,
    keywords: list[str],
    max_pages: int,
    headless: bool,
    user_agent: str | None,
    log: bool,
) -> tuple[list[SignedEntry], dict[str, str]]:
    seen: set[str] = set()
    entries: list[SignedEntry] = []
    collected_cookies: dict[str, str] = {}

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context_kwargs: dict[str, Any] = {}
        if user_agent:
            context_kwargs["user_agent"] = user_agent
        context: BrowserContext = await browser.new_context(**context_kwargs)
        page = await context.new_page()

        def on_request(request) -> None:
            url = request.url
            if "/api/job/search-pc?" not in url:
                return
            headers = _normalize_headers(request.headers)
            if "Sign" not in headers:
                return
            entry = SignedEntry(url=url, headers=headers)
            if entry.dedup_key in seen:
                return
            seen.add(entry.dedup_key)
            entries.append(entry)
            if log:
                print(
                    {
                        "captured": len(entries),
                        "url": url,
                        "sign_prefix": headers.get("Sign", "")[:16],
                    }
                )

        page.on("request", on_request)

        await page.goto("https://we.51job.com/pc/search", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3500)

        for keyword in keywords:
            await _collect_for_keyword(page, keyword=keyword, max_pages=max_pages, log=log)

        raw_cookies = await context.cookies()
        for cookie in raw_cookies:
            domain = str(cookie.get("domain") or "")
            if "51job.com" not in domain:
                continue
            name = str(cookie.get("name") or "").strip()
            value = str(cookie.get("value") or "").strip()
            if not name or not value:
                continue
            collected_cookies[name] = value

        await browser.close()

    return entries, collected_cookies


async def _save_to_source(
    *,
    source: Source,
    entries: list[SignedEntry],
    cookies: dict[str, str],
    replace: bool,
    enable: bool,
) -> dict[str, Any]:
    existing = _parse_existing_signed_urls((source.config_json or {}).get("signed_urls"))
    existing_map = {entry.dedup_key: entry for entry in existing}
    incoming_map = {entry.dedup_key: entry for entry in entries}

    if replace:
        merged_map = incoming_map
    else:
        merged_map = dict(existing_map)
        merged_map.update(incoming_map)

    merged_entries = list(merged_map.values())
    merged_signed_urls = [{"url": entry.url, "headers": entry.headers} for entry in merged_entries]

    config = dict(source.config_json or {})
    config["request_method"] = "GET"
    config["body_type"] = "none"
    config["allow_paths"] = ["/api/job/search-pc", "/open/noauth/jobs/same"]
    config["deny_paths"] = ["/captcha", "/verify", "/login"]
    config["fail_on_empty"] = True
    config["signed_urls"] = merged_signed_urls
    if cookies:
        existing_cookies = config.get("cookies")
        merged_cookies = dict(existing_cookies) if isinstance(existing_cookies, dict) else {}
        merged_cookies.update(cookies)
        config["cookies"] = merged_cookies

    source.config_json = config
    if enable:
        source.enabled = True
        source.paused_reason = None

    return {
        "source": source.code,
        "signed_url_count_before": len(existing),
        "signed_url_count_after": len(merged_entries),
        "signed_url_count_captured": len(entries),
        "cookies_collected": len(cookies),
        "enabled": bool(source.enabled),
    }


async def main() -> None:
    args = parse_args()
    keywords = [str(x).strip() for x in args.keyword if str(x).strip()]
    if not keywords:
        keywords = ["后端", "Java", "实习", "校招", "测试"]

    dao = SourceDAO()
    async with SessionLocal() as session:
        source = await dao.get_by_code(session, args.source)
        if source is None:
            raise SystemExit(f"source not found: {args.source}")
        base_headers = (source.config_json or {}).get("headers") if isinstance(source.config_json, dict) else None
        user_agent = None
        if isinstance(base_headers, dict):
            user_agent = base_headers.get("User-Agent") or base_headers.get("user-agent")

        entries, cookies = await _collect_signed_entries(
            keywords=keywords,
            max_pages=max(1, args.max_pages),
            headless=not bool(args.headed),
            user_agent=user_agent,
            log=bool(args.log),
        )
        if not entries:
            raise SystemExit("no signed search-pc requests captured")

        result = await _save_to_source(
            source=source,
            entries=entries,
            cookies=cookies,
            replace=bool(args.replace),
            enable=bool(args.enable),
        )
        await session.commit()

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
