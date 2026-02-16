from app.core.database import SessionLocal
from app.service.crawl_service import CrawlService


class TaskExecutor:
    def __init__(self) -> None:
        self.crawl_service = CrawlService()

    async def run_crawl(self, source_code: str, trigger_type: str = "schedule") -> dict:
        async with SessionLocal() as session:
            return await self.crawl_service.run_source(session, source_code=source_code, trigger_type=trigger_type)
