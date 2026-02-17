from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.campus_event_dao import CampusEventDAO
from app.exceptions.base import BusinessError
from app.exceptions.codes import CAMPUS_EVENT_NOT_FOUND


class CampusEventService:
    def __init__(self) -> None:
        self.event_dao = CampusEventDAO()

    async def search(
        self,
        session: AsyncSession,
        *,
        page: int,
        page_size: int,
        keyword: str | None,
        city: str | None,
        school: str | None,
        company: str | None,
        event_type: str | None,
        source: str | None,
        sort_by: str,
    ) -> dict:
        return await self.event_dao.search_events(
            session,
            page=page,
            page_size=page_size,
            keyword=keyword,
            city=city,
            school=school,
            company=company,
            event_type=event_type,
            source_code=source,
            sort_by=sort_by,
        )

    async def detail(self, session: AsyncSession, event_id: int) -> dict:
        detail = await self.event_dao.get_event_detail(session, event_id)
        if detail is None:
            raise BusinessError(CAMPUS_EVENT_NOT_FOUND, f"Campus event not found: {event_id}", 404)
        return detail

    async def basic_stats(self, session: AsyncSession) -> dict:
        return await self.event_dao.basic_stats(session)
