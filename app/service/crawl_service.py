import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler.registry import get_adapter
from app.dao.crawl_run_dao import CrawlRunDAO
from app.dao.job_dao import JobDAO
from app.dao.source_dao import SourceDAO
from app.exceptions.base import BusinessError
from app.exceptions.codes import SOURCE_DISABLED, SOURCE_NOT_FOUND
from app.service.compliance_service import ComplianceService

logger = logging.getLogger(__name__)


class CrawlService:
    def __init__(self) -> None:
        self.source_dao = SourceDAO()
        self.job_dao = JobDAO()
        self.run_dao = CrawlRunDAO()
        self.compliance = ComplianceService()

    async def run_source(self, session: AsyncSession, source_code: str, trigger_type: str = "manual") -> dict:
        source = await self.source_dao.get_by_code(session, source_code)
        if source is None:
            raise BusinessError(SOURCE_NOT_FOUND, f"Source not found: {source_code}", 404)
        if not source.enabled:
            raise BusinessError(SOURCE_DISABLED, f"Source is disabled: {source_code}", 400)

        run = await self.run_dao.create_running(session, source_id=source.id, trigger_type=trigger_type)

        try:
            self.compliance.validate_source_allowed(source)
            adapter = get_adapter(source_code)
            normalized_jobs = await adapter.crawl()
            inserted_count, updated_count = await self.job_dao.upsert_jobs(
                session,
                source_id=source.id,
                jobs=normalized_jobs,
            )
            await self.run_dao.finish_success(
                session,
                run,
                crawled_count=len(normalized_jobs),
                inserted_count=inserted_count,
                updated_count=updated_count,
            )
            await session.commit()

            return {
                "run_id": run.id,
                "status": getattr(run.status, "value", str(run.status)),
                "crawled_count": len(normalized_jobs),
                "inserted_count": inserted_count,
                "updated_count": updated_count,
            }
        except Exception as exc:
            await self.run_dao.finish_failed(session, run, str(exc))
            if self.compliance.should_pause_for_risk(str(exc)):
                source.enabled = False
                source.paused_reason = f"auto-paused due to risk: {str(exc)[:200]}"
            await session.commit()
            logger.exception("crawl failed", extra={"source_code": source_code, "run_id": run.id})
            raise

    async def get_run(self, session: AsyncSession, run_id: int) -> dict | None:
        run = await self.run_dao.get_by_id(session, run_id)
        if run is None:
            return None
        return {
            "id": run.id,
            "source_id": run.source_id,
            "status": getattr(run.status, "value", str(run.status)),
            "started_at": run.started_at,
            "finished_at": run.finished_at,
            "crawled_count": run.crawled_count,
            "inserted_count": run.inserted_count,
            "updated_count": run.updated_count,
            "failed_count": run.failed_count,
            "error_summary": run.error_summary,
        }
