from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.job_dao import JobDAO
from app.exceptions.base import BusinessError
from app.exceptions.codes import JOB_NOT_FOUND


class JobService:
    def __init__(self) -> None:
        self.job_dao = JobDAO()

    async def search(
        self,
        session: AsyncSession,
        *,
        page: int,
        page_size: int,
        sort_by: str,
        keyword: str | None,
        province: str | None,
        city: str | None,
        district: str | None,
        category: str | None,
        education: str | None,
        experience_min: int | None,
        salary_min: float | None,
        salary_max: float | None,
        industry: str | None,
        source: str | None,
    ) -> dict:
        return await self.job_dao.search_jobs(
            session,
            page=page,
            page_size=page_size,
            keyword=keyword,
            province=province,
            city=city,
            district=district,
            category=category,
            education=education,
            experience_min=experience_min,
            salary_min=Decimal(str(salary_min)) if salary_min is not None else None,
            salary_max=Decimal(str(salary_max)) if salary_max is not None else None,
            industry=industry,
            source_code=source,
            sort_by=sort_by,
        )

    async def detail(self, session: AsyncSession, job_id: int) -> dict:
        detail = await self.job_dao.get_job_detail(session, job_id)
        if detail is None:
            raise BusinessError(JOB_NOT_FOUND, f"Job not found: {job_id}", 404)
        return detail

    async def basic_stats(self, session: AsyncSession) -> dict:
        return await self.job_dao.basic_stats(session)
