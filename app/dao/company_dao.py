from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


class CompanyDAO:
    async def get_or_create(self, session: AsyncSession, company_name: str) -> Company:
        normalized = company_name.strip().lower()
        stmt = insert(Company).values(normalized_name=normalized, display_name=company_name)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Company.normalized_name],
            set_={"display_name": company_name},
        ).returning(Company)
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None:
            return row

        fallback = await session.execute(select(Company).where(Company.normalized_name == normalized))
        company = fallback.scalar_one_or_none()
        if company is None:
            raise RuntimeError("Failed to upsert company")
        return company
