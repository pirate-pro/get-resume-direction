from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.response import success_response
from app.schemas.crawler import CrawlRunCreateRequest
from app.service.campus_crawl_service import CampusCrawlService
from app.service.campus_event_service import CampusEventService

router = APIRouter()
event_service = CampusEventService()
campus_crawl_service = CampusCrawlService()


@router.get("/campus-events")
async def list_campus_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="time"),
    keyword: str | None = None,
    city: str | None = None,
    school: str | None = None,
    company: str | None = None,
    event_type: str | None = None,
    source: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    data = await event_service.search(
        session,
        page=page,
        page_size=page_size,
        keyword=keyword,
        city=city,
        school=school,
        company=company,
        event_type=event_type,
        source=source,
        sort_by=sort_by,
    )
    return success_response(data)


@router.get("/campus-events/stats/basic")
async def campus_event_stats(session: AsyncSession = Depends(get_session)):
    return success_response(await event_service.basic_stats(session))


@router.post("/campus-events/crawler/runs")
async def trigger_campus_crawl(
    payload: CrawlRunCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    data = await campus_crawl_service.run_source(session, payload.source_code, payload.trigger_type)
    return success_response(data)


@router.get("/campus-events/{event_id}")
async def get_campus_event_detail(event_id: int, session: AsyncSession = Depends(get_session)):
    data = await event_service.detail(session, event_id)
    return success_response(data)
