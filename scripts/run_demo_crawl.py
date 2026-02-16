import asyncio

from app.core.database import SessionLocal
from app.service.crawl_service import CrawlService


async def main() -> None:
    service = CrawlService()
    async with SessionLocal() as session:
        result = await service.run_source(session, source_code="demo_platform", trigger_type="manual")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
