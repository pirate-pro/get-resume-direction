import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.dao.source_dao import SourceDAO
from app.tasks.executor import TaskExecutor

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self) -> None:
        settings = get_settings()
        self.scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
        self.source_dao = SourceDAO()
        self.executor = TaskExecutor()

    async def start(self) -> None:
        if self.scheduler.running:
            return

        try:
            async with SessionLocal() as session:
                sources = await self.source_dao.list_enabled(session)
                for src in sources:
                    cron_expr = src.config_json.get("schedule_cron", "*/30 * * * *")
                    trigger = CronTrigger.from_crontab(cron_expr)
                    self.scheduler.add_job(
                        self._run_source,
                        trigger=trigger,
                        args=[src.code],
                        id=f"crawl:{src.code}",
                        max_instances=1,
                        replace_existing=True,
                    )
                    logger.info("scheduler job registered", extra={"source": src.code, "cron": cron_expr})
        except Exception:
            logger.exception("scheduler registration failed; startup will continue")

        self.scheduler.start()

    async def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    async def _run_source(self, source_code: str) -> None:
        try:
            await self.executor.run_crawl(source_code=source_code, trigger_type="schedule")
        except Exception:
            logger.exception("scheduled crawl failed", extra={"source": source_code})


scheduler_service = SchedulerService()
