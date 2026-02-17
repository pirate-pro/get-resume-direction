import argparse
import asyncio

from app.core.database import SessionLocal
from app.crawler.adapters.http_common import parse_cookie_string
from app.dao.source_dao import SourceDAO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="为指定数据源写入 Cookie 并可选启用该源")
    parser.add_argument("--source", required=True, help="source code, e.g. zhipin_public")
    parser.add_argument("--cookie", default="", help="浏览器复制的完整 Cookie 字符串")
    parser.add_argument("--cookie-file", default="", help="从文件读取完整 Cookie 字符串")
    parser.add_argument("--enable", action="store_true", help="写入 Cookie 后立即启用源")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    cookie_raw = args.cookie
    if args.cookie_file:
        cookie_raw = open(args.cookie_file, encoding="utf-8").read().strip()
    cookies = parse_cookie_string(cookie_raw)
    if not cookies:
        raise SystemExit("cookie string is empty after parsing")

    dao = SourceDAO()
    async with SessionLocal() as session:
        source = await dao.get_by_code(session, args.source)
        if source is None:
            raise SystemExit(f"source not found: {args.source}")

        config = dict(source.config_json or {})
        config["cookies"] = cookies
        source.config_json = config
        if args.enable:
            source.enabled = True
            source.paused_reason = None
        await session.commit()

    print(
        {
            "source": args.source,
            "cookies_keys": sorted(cookies.keys()),
            "enabled": bool(args.enable),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
