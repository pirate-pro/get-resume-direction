import argparse
import asyncio
from pathlib import Path

from app.core.database import SessionLocal
from app.crawler.adapters.http_common import parse_cookie_string
from app.dao.source_dao import SourceDAO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 job51_public 切换为 cupid signed-url 抓取模式")
    parser.add_argument("--source", default="job51_public", help="source code")
    parser.add_argument("--signed-url", action="append", default=[], help="完整 signed URL，可传多次")
    parser.add_argument("--signed-url-file", default="", help="从文件读取 signed URL（每行一条）")
    parser.add_argument("--append", action="store_true", help="追加到已存在 signed_urls（去重）")
    parser.add_argument("--account-id", required=True, help="header Account-Id")
    parser.add_argument("--from-domain", default="51job_web", help="header From-Domain")
    parser.add_argument("--sign", required=True, help="header Sign")
    parser.add_argument("--user-token", required=True, help="header User-Token")
    parser.add_argument("--uuid", required=True, help="header Uuid")
    parser.add_argument("--user-agent", required=True, help="header User-Agent")
    parser.add_argument("--origin", default="https://jobs.51job.com", help="header Origin")
    parser.add_argument("--referer", default="https://jobs.51job.com/", help="header Referer")
    parser.add_argument("--cookie", default="", help="可选，完整 Cookie")
    parser.add_argument("--cookie-file", default="", help="可选，从文件读取 Cookie")
    parser.add_argument("--enable", action="store_true", help="配置后启用")
    return parser.parse_args()


def load_signed_urls(args: argparse.Namespace) -> list[str]:
    urls = [str(x).strip() for x in args.signed_url if str(x).strip()]
    if args.signed_url_file:
        file_path = Path(args.signed_url_file)
        if not file_path.exists():
            raise SystemExit(f"signed-url-file not found: {args.signed_url_file}")
        file_urls = [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        urls.extend(file_urls)
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


async def main() -> None:
    args = parse_args()
    input_signed_urls = load_signed_urls(args)
    if not input_signed_urls:
        raise SystemExit("请至少提供一个 --signed-url 或 --signed-url-file")

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
        existing_urls = config.get("signed_urls")
        existing = [str(x).strip() for x in existing_urls if str(x).strip()] if isinstance(existing_urls, list) else []
        if args.append:
            combined: list[str] = []
            seen: set[str] = set()
            for url in [*existing, *input_signed_urls]:
                if url in seen:
                    continue
                seen.add(url)
                combined.append(url)
            next_signed_urls = combined
        else:
            next_signed_urls = input_signed_urls

        config.update(
            {
                "request_method": "GET",
                "body_type": "none",
                "signed_urls": next_signed_urls,
                "headers": {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Origin": args.origin,
                    "Referer": args.referer,
                    "From-Domain": args.from_domain,
                    "Account-Id": args.account_id,
                    "Sign": args.sign,
                    "User-Agent": args.user_agent,
                    "User-Token": args.user_token,
                    "Uuid": args.uuid,
                    "Sec-Ch-Ua": '"Chromium";v="9", "Not?A_Brand";v="8"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Windows"',
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site",
                },
                "allow_paths": ["/open/noauth/jobs/same"],
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
            "signed_url_count_before": len(existing),
            "signed_url_count_after": len(next_signed_urls),
            "signed_url_count_input": len(input_signed_urls),
            "cookies_keys": sorted(cookies.keys()),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
