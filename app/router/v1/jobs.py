from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.response import success_response
from app.service.job_service import JobService

router = APIRouter()
job_service = JobService()


@router.get("/jobs")
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="time"),
    keyword: str | None = None,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    category: str | None = None,
    education: str | None = None,
    experience_min: int | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    industry: str | None = None,
    source: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    data = await job_service.search(
        session,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        keyword=keyword,
        province=province,
        city=city,
        district=district,
        category=category,
        education=education,
        experience_min=experience_min,
        salary_min=salary_min,
        salary_max=salary_max,
        industry=industry,
        source=source,
    )
    return success_response(data)


@router.get("/jobs/{job_id}")
async def get_job_detail(job_id: int, session: AsyncSession = Depends(get_session)):
    detail = await job_service.detail(session, job_id)
    return success_response(detail)
