from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source


class SourceDAO:
    async def get_by_code(self, session: AsyncSession, code: str) -> Source | None:
        stmt = select(Source).where(Source.code == code)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_enabled(self, session: AsyncSession) -> list[Source]:
        stmt = select(Source).where(Source.enabled.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, session: AsyncSession) -> list[Source]:
        result = await session.execute(select(Source).order_by(Source.code.asc()))
        return list(result.scalars().all())

    async def toggle(self, session: AsyncSession, source: Source, enabled: bool, reason: str | None) -> Source:
        source.enabled = enabled
        source.paused_reason = None if enabled else reason
        await session.flush()
        return source
