from app.core.database import SessionLocal
from app.crawler.campus_registry import REGISTRY as CAMPUS_CRAWLER_REGISTRY
from app.crawler.registry import REGISTRY as JOB_CRAWLER_REGISTRY
from app.service.campus_crawl_service import CampusCrawlService
from app.service.crawl_service import CrawlService


class TaskExecutor:
    def __init__(self) -> None:
        self.crawl_service = CrawlService()
        self.campus_crawl_service = CampusCrawlService()

    async def run_crawl(self, source_code: str, trigger_type: str = "schedule") -> dict:
        async with SessionLocal() as session:
            if source_code in JOB_CRAWLER_REGISTRY:
                return await self.crawl_service.run_source(session, source_code=source_code, trigger_type=trigger_type)
            if source_code in CAMPUS_CRAWLER_REGISTRY:
                return await self.campus_crawl_service.run_source(
                    session,
                    source_code=source_code,
                    trigger_type=trigger_type,
                )
            raise KeyError(f"No crawler adapter registered for source={source_code}")
