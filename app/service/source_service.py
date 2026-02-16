from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.source_dao import SourceDAO
from app.exceptions.base import BusinessError
from app.exceptions.codes import SOURCE_NOT_FOUND


class SourceService:
    def __init__(self) -> None:
        self.source_dao = SourceDAO()

    async def list_sources(self, session: AsyncSession) -> list[dict]:
        sources = await self.source_dao.list_all(session)
        return [
            {
                "code": src.code,
                "name": src.name,
                "source_type": getattr(src.source_type, "value", str(src.source_type)),
                "enabled": src.enabled,
                "paused_reason": src.paused_reason,
            }
            for src in sources
        ]

    async def toggle_source(
        self,
        session: AsyncSession,
        *,
        source_code: str,
        enabled: bool,
        reason: str | None,
    ) -> dict:
        source = await self.source_dao.get_by_code(session, source_code)
        if source is None:
            raise BusinessError(SOURCE_NOT_FOUND, f"Source not found: {source_code}", 404)

        updated = await self.source_dao.toggle(session, source, enabled, reason)
        await session.commit()
        return {
            "code": updated.code,
            "enabled": updated.enabled,
            "paused_reason": updated.paused_reason,
        }
