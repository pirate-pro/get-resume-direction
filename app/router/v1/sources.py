from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.response import success_response
from app.schemas.source import SourceToggleRequest
from app.service.source_service import SourceService

router = APIRouter()
source_service = SourceService()


@router.get("/sources")
async def list_sources(session: AsyncSession = Depends(get_session)):
    data = await source_service.list_sources(session)
    return success_response(data)


@router.patch("/sources/{source_code}/toggle")
async def toggle_source(
    source_code: str,
    payload: SourceToggleRequest,
    session: AsyncSession = Depends(get_session),
):
    data = await source_service.toggle_source(
        session,
        source_code=source_code,
        enabled=payload.enabled,
        reason=payload.reason,
    )
    return success_response(data)
