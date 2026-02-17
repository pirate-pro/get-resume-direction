from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler.campus_registry import REGISTRY as CAMPUS_CRAWLER_REGISTRY
from app.core.database import get_session
from app.core.response import success_response
from app.schemas.crawler import CrawlRunCreateRequest
from app.service.campus_crawl_service import CampusCrawlService
from app.service.crawl_service import CrawlService

router = APIRouter()
crawl_service = CrawlService()
campus_crawl_service = CampusCrawlService()


@router.post("/crawler/runs")
async def trigger_crawl(
    payload: CrawlRunCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    if payload.source_code in CAMPUS_CRAWLER_REGISTRY:
        data = await campus_crawl_service.run_source(
            session,
            source_code=payload.source_code,
            trigger_type=payload.trigger_type,
        )
    else:
        data = await crawl_service.run_source(
            session,
            source_code=payload.source_code,
            trigger_type=payload.trigger_type,
        )
    return success_response(data)


@router.get("/crawler/runs/{run_id}")
async def get_crawl_run(run_id: int, session: AsyncSession = Depends(get_session)):
    data = await crawl_service.get_run(session, run_id)
    return success_response(data)
