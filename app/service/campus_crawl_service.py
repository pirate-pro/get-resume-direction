import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler.campus_registry import get_campus_adapter
from app.dao.campus_event_dao import CampusEventDAO
from app.dao.crawl_run_dao import CrawlRunDAO
from app.dao.source_dao import SourceDAO
from app.exceptions.base import BusinessError
from app.exceptions.codes import INVALID_REQUEST, SOURCE_DISABLED, SOURCE_NOT_FOUND
from app.service.compliance_service import ComplianceService

logger = logging.getLogger(__name__)


class CampusCrawlService:
    def __init__(self) -> None:
        self.source_dao = SourceDAO()
        self.event_dao = CampusEventDAO()
        self.run_dao = CrawlRunDAO()
        self.compliance = ComplianceService()

    async def run_source(self, session: AsyncSession, source_code: str, trigger_type: str = "manual") -> dict:
        source = await self.source_dao.get_by_code(session, source_code)
        if source is None:
            raise BusinessError(SOURCE_NOT_FOUND, f"Source not found: {source_code}", 404)
        if not source.enabled:
            raise BusinessError(SOURCE_DISABLED, f"Source is disabled: {source_code}", 400)

        try:
            adapter = get_campus_adapter(source_code, config=source.config_json or {})
        except KeyError as exc:
            raise BusinessError(INVALID_REQUEST, str(exc), 400) from exc

        run = await self.run_dao.create_running(session, source_id=source.id, trigger_type=trigger_type)
        try:
            self.compliance.validate_source_allowed(source)
            events = await adapter.crawl()
            inserted_count, updated_count = await self.event_dao.upsert_events(session, source.id, events)
            source_total = await self.event_dao.count_by_source(session, source.id)
            await self.run_dao.finish_success(
                session,
                run,
                crawled_count=len(events),
                inserted_count=inserted_count,
                updated_count=updated_count,
            )
            await session.commit()
            result = {
                "run_id": run.id,
                "status": getattr(run.status, "value", str(run.status)),
                "crawled_count": len(events),
                "inserted_count": inserted_count,
                "updated_count": updated_count,
                "target_table": "campus_events",
                "source_total": source_total,
            }
            crawl_meta = getattr(adapter, "last_crawl_meta", None)
            if isinstance(crawl_meta, dict):
                result["crawl_meta"] = crawl_meta
            return result
        except Exception as exc:
            await session.rollback()
            failed_run = await self.run_dao.get_by_id(session, run.id)
            if failed_run is not None:
                await self.run_dao.finish_failed(session, failed_run, str(exc))
                if self.compliance.should_pause_for_risk(str(exc)):
                    source.enabled = False
                    source.paused_reason = f"auto-paused due to risk: {str(exc)[:200]}"
                await session.commit()
            logger.exception("campus crawl failed", extra={"source_code": source_code, "run_id": run.id})
            raise
