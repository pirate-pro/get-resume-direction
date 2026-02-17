import argparse
import asyncio
from urllib.parse import parse_qsl

from app.core.database import SessionLocal
from app.crawler.adapters.http_common import parse_cookie_string
from app.dao.source_dao import SourceDAO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 job51_public 切换为 vapi.51job.com POST 配置")
    parser.add_argument("--source", default="job51_public", help="source code")
    parser.add_argument("--api-url", default="https://vapi.51job.com/job.php", help="vapi endpoint")
    parser.add_argument("--api-version", default="400", help="query apiversion")
    parser.add_argument("--module", default="hrinfo", help="query module")
    parser.add_argument("--client-id", default="000005", help="query clientid")
    parser.add_argument("--type-token", required=True, help="query type__1260")
    parser.add_argument("--account-id", required=True, help="header Account-Id")
    parser.add_argument(
        "--form",
        required=True,
        help="原始 form body，示例: a=1&b=2&keyword=后端&page=1&page_size=20",
    )
    parser.add_argument("--cookie", default="", help="完整 Cookie 字符串，可选")
    parser.add_argument("--cookie-file", default="", help="从文件读取完整 Cookie 字符串")
    parser.add_argument("--enable", action="store_true", help="配置后启用该源")

    parser.add_argument("--keywords", default="后端,Java,实习", help="逗号分隔")
    parser.add_argument("--keyword-field", default="keyword", help="body 中关键词字段名")
    parser.add_argument("--page-field", default="page", help="body 中页码字段名")
    parser.add_argument("--page-size-field", default="page_size", help="body 中每页字段名")
    parser.add_argument("--offset-field", default="start", help="offset 模式字段名")
    parser.add_argument("--pagination-mode", choices=["page", "offset"], default="page")

    parser.add_argument("--user-agent", default="Mozilla/5.0", help="请求头 UA")
    parser.add_argument("--origin", default="https://jobs.51job.com", help="请求头 Origin")
    parser.add_argument("--referer", default="https://jobs.51job.com/", help="请求头 Referer")
    return parser.parse_args()


def parse_form_template(raw_form: str) -> dict[str, str]:
    pairs = parse_qsl(raw_form, keep_blank_values=True)
    return {k: v for k, v in pairs if k}


async def main() -> None:
    args = parse_args()
    form_data = parse_form_template(args.form)
    if not form_data:
        raise SystemExit("form body 解析为空")

    if args.keyword_field in form_data:
        form_data[args.keyword_field] = "{keyword}"
    if args.page_size_field in form_data:
        form_data[args.page_size_field] = "{page_size}"
    if args.pagination_mode == "offset":
        if args.offset_field in form_data:
            form_data[args.offset_field] = "{offset}"
    else:
        if args.page_field in form_data:
            form_data[args.page_field] = "{page}"

    keywords = [x.strip() for x in args.keywords.split(",") if x.strip()]
    cookie_raw = args.cookie
    if args.cookie_file:
        cookie_raw = open(args.cookie_file, encoding="utf-8").read().strip()
    cookies = parse_cookie_string(cookie_raw) if cookie_raw else {}

    dao = SourceDAO()
    async with SessionLocal() as session:
        source = await dao.get_by_code(session, args.source)
        if source is None:
            raise SystemExit(f"source not found: {args.source}")

        config = dict(source.config_json or {})
        config.update(
            {
                "api_url": args.api_url,
                "request_method": "POST",
                "body_type": "form",
                "pagination_mode": args.pagination_mode,
                "keyword_field": args.keyword_field,
                "page_field": args.page_field,
                "page_size_field": args.page_size_field,
                "offset_field": args.offset_field,
                "query_params": {
                    "apiversion": args.api_version,
                    "module": args.module,
                    "clientid": args.client_id,
                    "type__1260": args.type_token,
                },
                "form_data": form_data,
                "keywords": keywords or config.get("keywords") or ["后端"],
                "headers": {
                    "User-Agent": args.user_agent,
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": args.origin,
                    "Referer": args.referer,
                    "Account-Id": args.account_id,
                },
                "allow_paths": ["/job.php"],
                "deny_paths": ["/captcha", "/verify", "/login"],
                "fail_on_empty": True,
            }
        )
        if cookies:
            config["cookies"] = cookies

        source.config_json = config
        if args.enable:
            source.enabled = True
            source.paused_reason = None
        await session.commit()

    print(
        {
            "source": args.source,
            "enabled": bool(args.enable),
            "query_params": {
                "apiversion": args.api_version,
                "module": args.module,
                "clientid": args.client_id,
                "type__1260_len": len(args.type_token),
            },
            "form_keys": sorted(form_data.keys()),
            "cookies_keys": sorted(cookies.keys()),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
