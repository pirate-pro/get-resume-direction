from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crawl_run import CrawlRun
from app.models.enums import CrawlRunStatus
from app.utils.time import now_utc


class CrawlRunDAO:
    async def create_running(self, session: AsyncSession, source_id: int, trigger_type: str) -> CrawlRun:
        run = CrawlRun(
            source_id=source_id,
            trigger_type=trigger_type,
            status=CrawlRunStatus.running,
            started_at=now_utc(),
            crawled_count=0,
            inserted_count=0,
            updated_count=0,
            failed_count=0,
        )
        session.add(run)
        await session.flush()
        return run

    async def finish_success(
        self,
        session: AsyncSession,
        run: CrawlRun,
        crawled_count: int,
        inserted_count: int,
        updated_count: int,
    ) -> None:
        run.status = CrawlRunStatus.success
        run.finished_at = now_utc()
        run.crawled_count = crawled_count
        run.inserted_count = inserted_count
        run.updated_count = updated_count
        await session.flush()

    async def finish_failed(self, session: AsyncSession, run: CrawlRun, reason: str) -> None:
        run.status = CrawlRunStatus.failed
        run.finished_at = now_utc()
        run.error_summary = reason[:2000]
        run.failed_count += 1
        await session.flush()

    async def get_by_id(self, session: AsyncSession, run_id: int) -> CrawlRun | None:
        result = await session.execute(select(CrawlRun).where(CrawlRun.id == run_id))
        return result.scalar_one_or_none()
