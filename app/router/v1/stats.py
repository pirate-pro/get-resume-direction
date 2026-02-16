from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.response import success_response
from app.service.job_service import JobService

router = APIRouter()
job_service = JobService()


@router.get("/stats/basic")
async def basic_stats(session: AsyncSession = Depends(get_session)):
    data = await job_service.basic_stats(session)
    return success_response(data)
