from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location


class LocationDAO:
    async def get_or_create(
        self,
        session: AsyncSession,
        normalized_key: str,
        province: str | None,
        city: str | None,
        district: str | None,
    ) -> Location:
        stmt = insert(Location).values(
            normalized_key=normalized_key,
            province=province,
            city=city,
            district=district,
            country_code="CN",
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Location.normalized_key],
            set_={"province": province, "city": city, "district": district},
        ).returning(Location)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None:
            return row

        fallback = await session.execute(select(Location).where(Location.normalized_key == normalized_key))
        location = fallback.scalar_one_or_none()
        if location is None:
            raise RuntimeError("Failed to upsert location")
        return location
