from dataclasses import asdict
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler.types import NormalizedJob
from app.dao.company_dao import CompanyDAO
from app.dao.location_dao import LocationDAO
from app.models.company import Company
from app.models.job import Job
from app.models.location import Location
from app.models.source import Source


class JobDAO:
    def __init__(self) -> None:
        self.company_dao = CompanyDAO()
        self.location_dao = LocationDAO()

    async def upsert_jobs(self, session: AsyncSession, source_id: int, jobs: list[NormalizedJob]) -> tuple[int, int]:
        inserted_count = 0
        updated_count = 0

        for normalized in jobs:
            company = await self.company_dao.get_or_create(session, normalized.company_name)
            location = await self.location_dao.get_or_create(
                session=session,
                normalized_key=normalized.location_key,
                province=normalized.province,
                city=normalized.city,
                district=normalized.district,
            )

            payload = asdict(normalized)
            payload.pop("skills", None)

            search_text = " ".join(
                [
                    normalized.title,
                    normalized.responsibilities or "",
                    normalized.qualifications or "",
                    " ".join(normalized.skills),
                ]
            )

            stmt = insert(Job).values(
                source_id=source_id,
                external_job_id=normalized.external_job_id,
                source_url=normalized.source_url,
                dedup_fingerprint=normalized.dedup_fingerprint,
                global_fingerprint=normalized.global_fingerprint,
                company_id=company.id,
                location_id=location.id,
                title=normalized.title,
                job_category=normalized.job_category,
                seniority=normalized.seniority,
                department=normalized.department,
                job_type=normalized.job_type,
                remote_type=normalized.remote_type,
                salary_min=normalized.salary_min,
                salary_max=normalized.salary_max,
                salary_currency=normalized.salary_currency,
                salary_period=normalized.salary_period,
                education_requirement=normalized.education_requirement,
                experience_min_months=normalized.experience_min_months,
                experience_max_months=normalized.experience_max_months,
                responsibilities=normalized.responsibilities,
                qualifications=normalized.qualifications,
                benefits_json=normalized.benefits,
                tags_json=normalized.tags,
                published_at=normalized.published_at,
                updated_at_source=normalized.updated_at_source,
                first_crawled_at=normalized.first_crawled_at,
                last_crawled_at=normalized.last_crawled_at,
                search_vector=func.to_tsvector("simple", search_text),
                status="active",
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[Job.source_id, Job.external_job_id],
                set_={
                    "source_url": normalized.source_url,
                    "company_id": company.id,
                    "location_id": location.id,
                    "title": normalized.title,
                    "job_category": normalized.job_category,
                    "seniority": normalized.seniority,
                    "department": normalized.department,
                    "job_type": normalized.job_type,
                    "remote_type": normalized.remote_type,
                    "salary_min": normalized.salary_min,
                    "salary_max": normalized.salary_max,
                    "salary_currency": normalized.salary_currency,
                    "salary_period": normalized.salary_period,
                    "education_requirement": normalized.education_requirement,
                    "experience_min_months": normalized.experience_min_months,
                    "experience_max_months": normalized.experience_max_months,
                    "responsibilities": normalized.responsibilities,
                    "qualifications": normalized.qualifications,
                    "benefits_json": normalized.benefits,
                    "tags_json": normalized.tags,
                    "updated_at_source": normalized.updated_at_source,
                    "last_crawled_at": normalized.last_crawled_at,
                    "search_vector": func.to_tsvector("simple", search_text),
                    "status": "active",
                },
            ).returning(Job.id)

            result = await session.execute(stmt)
            job_id = result.scalar_one()
            exists_stmt = select(Job.id).where(
                Job.id == job_id,
                Job.first_crawled_at == normalized.first_crawled_at,
            )
            exists_result = await session.execute(exists_stmt)
            if exists_result.scalar_one_or_none() is None:
                updated_count += 1
            else:
                inserted_count += 1

        await session.flush()
        return inserted_count, updated_count

    async def search_jobs(
        self,
        session: AsyncSession,
        *,
        page: int,
        page_size: int,
        keyword: str | None,
        province: str | None,
        city: str | None,
        district: str | None,
        category: str | None,
        education: str | None,
        experience_min: int | None,
        salary_min: Decimal | None,
        salary_max: Decimal | None,
        industry: str | None,
        source_code: str | None,
        sort_by: str,
    ) -> dict:
        stmt = (
            select(Job, Company.display_name.label("company_name"), Source.code.label("source_code"), Location.city)
            .join(Company, Company.id == Job.company_id)
            .join(Source, Source.id == Job.source_id)
            .join(Location, Location.id == Job.location_id, isouter=True)
        )

        if keyword:
            ts_query = func.plainto_tsquery("simple", keyword)
            stmt = stmt.where(
                or_(
                    Job.search_vector.op("@@")(ts_query),
                    Job.title.ilike(f"%{keyword}%"),
                    Job.responsibilities.ilike(f"%{keyword}%"),
                )
            )

        if province:
            stmt = stmt.where(Location.province == province)
        if city:
            stmt = stmt.where(Location.city == city)
        if district:
            stmt = stmt.where(Location.district == district)
        if category:
            stmt = stmt.where(Job.job_category == category)
        if education:
            stmt = stmt.where(Job.education_requirement == education)
        if experience_min is not None:
            stmt = stmt.where(or_(Job.experience_min_months.is_(None), Job.experience_min_months >= experience_min))
        if salary_min is not None:
            stmt = stmt.where(or_(Job.salary_min.is_(None), Job.salary_min >= salary_min))
        if salary_max is not None:
            stmt = stmt.where(or_(Job.salary_max.is_(None), Job.salary_max <= salary_max))
        if industry:
            stmt = stmt.where(Company.industry == industry)
        if source_code:
            stmt = stmt.where(Source.code == source_code)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        if sort_by == "salary":
            stmt = stmt.order_by(Job.salary_max.desc().nullslast(), Job.published_at.desc().nullslast())
        elif sort_by == "relevance" and keyword:
            stmt = stmt.order_by(func.ts_rank_cd(Job.search_vector, func.plainto_tsquery("simple", keyword)).desc())
        else:
            stmt = stmt.order_by(Job.published_at.desc().nullslast(), Job.id.desc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await session.execute(stmt)).all()

        items = []
        for job, company_name, src_code, city_value in rows:
            items.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "company_name": company_name,
                    "city": city_value,
                    "salary_min": float(job.salary_min) if job.salary_min is not None else None,
                    "salary_max": float(job.salary_max) if job.salary_max is not None else None,
                    "salary_currency": job.salary_currency,
                    "salary_period": job.salary_period,
                    "education_requirement": getattr(job.education_requirement, "value", str(job.education_requirement)),
                    "published_at": job.published_at,
                    "source_code": src_code,
                }
            )

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    async def get_job_detail(self, session: AsyncSession, job_id: int) -> dict | None:
        stmt = (
            select(
                Job,
                Company.display_name.label("company_name"),
                Source.code.label("source_code"),
                Location.city.label("city"),
            )
            .join(Company, Company.id == Job.company_id)
            .join(Source, Source.id == Job.source_id)
            .join(Location, Location.id == Job.location_id, isouter=True)
            .where(Job.id == job_id)
        )
        row = (await session.execute(stmt)).first()
        if row is None:
            return None

        job, company_name, source_code, city = row
        return {
            "id": job.id,
            "title": job.title,
            "company_name": company_name,
            "city": city,
            "salary_min": float(job.salary_min) if job.salary_min is not None else None,
            "salary_max": float(job.salary_max) if job.salary_max is not None else None,
            "salary_currency": job.salary_currency,
            "salary_period": job.salary_period,
            "education_requirement": getattr(job.education_requirement, "value", str(job.education_requirement)),
            "published_at": job.published_at,
            "source_code": source_code,
            "source_url": job.source_url,
            "job_category": job.job_category,
            "seniority": job.seniority,
            "responsibilities": job.responsibilities,
            "qualifications": job.qualifications,
            "tags": job.tags_json or [],
            "benefits": job.benefits_json or [],
        }

    async def basic_stats(self, session: AsyncSession) -> dict:
        by_source_stmt = (
            select(Source.code, func.count(Job.id))
            .join(Job, Job.source_id == Source.id)
            .group_by(Source.code)
            .order_by(Source.code.asc())
        )
        by_city_stmt = (
            select(Location.city, func.count(Job.id))
            .join(Job, Job.location_id == Location.id)
            .group_by(Location.city)
            .order_by(func.count(Job.id).desc())
            .limit(20)
        )
        by_category_stmt = (
            select(Job.job_category, func.count(Job.id))
            .group_by(Job.job_category)
            .order_by(func.count(Job.id).desc())
            .limit(20)
        )

        by_source = [{"source": code, "count": count} for code, count in (await session.execute(by_source_stmt)).all()]
        by_city = [{"city": city, "count": count} for city, count in (await session.execute(by_city_stmt)).all()]
        by_category = [
            {"category": category or "unknown", "count": count}
            for category, count in (await session.execute(by_category_stmt)).all()
        ]

        return {
            "by_source": by_source,
            "by_city": by_city,
            "by_category": by_category,
        }
