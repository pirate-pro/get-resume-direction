from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.crawler.types_event import NormalizedCampusEvent
from app.models.campus_event import CampusEvent
from app.models.source import Source


class CampusEventDAO:
    async def upsert_events(
        self, session: AsyncSession, source_id: int, events: list[NormalizedCampusEvent]
    ) -> tuple[int, int]:
        inserted_count = 0
        updated_count = 0

        for event in events:
            exists_stmt = select(CampusEvent).where(
                CampusEvent.source_id == source_id,
                CampusEvent.external_event_id == event.external_event_id,
            )
            existed = (await session.execute(exists_stmt)).scalar_one_or_none()
            if existed is None:
                inserted_count += 1
            else:
                # Count as "updated" only when core business fields changed (exclude crawl timestamps).
                has_changes = any(
                    [
                        existed.source_url != event.source_url,
                        existed.registration_url != event.registration_url,
                        existed.dedup_fingerprint != event.dedup_fingerprint,
                        existed.title != event.title,
                        existed.event_type != event.event_type,
                        existed.company_name != event.company_name,
                        existed.school_name != event.school_name,
                        existed.province != event.province,
                        existed.city != event.city,
                        existed.venue != event.venue,
                        existed.starts_at != event.starts_at,
                        existed.ends_at != event.ends_at,
                        existed.event_status != event.event_status,
                        existed.description != event.description,
                        (existed.tags_json or []) != (event.tags or []),
                        (existed.raw_payload_json or {}) != (event.raw_payload or {}),
                    ]
                )
                if has_changes:
                    updated_count += 1

            stmt = insert(CampusEvent).values(
                source_id=source_id,
                external_event_id=event.external_event_id,
                source_url=event.source_url,
                registration_url=event.registration_url,
                dedup_fingerprint=event.dedup_fingerprint,
                title=event.title,
                event_type=event.event_type,
                company_name=event.company_name,
                school_name=event.school_name,
                province=event.province,
                city=event.city,
                venue=event.venue,
                starts_at=event.starts_at,
                ends_at=event.ends_at,
                event_status=event.event_status,
                description=event.description,
                tags_json=event.tags,
                raw_payload_json=event.raw_payload,
                first_crawled_at=event.first_crawled_at,
                last_crawled_at=event.last_crawled_at,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[CampusEvent.source_id, CampusEvent.external_event_id],
                set_={
                    "source_url": event.source_url,
                    "registration_url": event.registration_url,
                    "dedup_fingerprint": event.dedup_fingerprint,
                    "title": event.title,
                    "event_type": event.event_type,
                    "company_name": event.company_name,
                    "school_name": event.school_name,
                    "province": event.province,
                    "city": event.city,
                    "venue": event.venue,
                    "starts_at": event.starts_at,
                    "ends_at": event.ends_at,
                    "event_status": event.event_status,
                    "description": event.description,
                    "tags_json": event.tags,
                    "raw_payload_json": event.raw_payload,
                    "last_crawled_at": event.last_crawled_at,
                },
            )
            await session.execute(stmt)

        await session.flush()
        return inserted_count, updated_count

    async def count_by_source(self, session: AsyncSession, source_id: int) -> int:
        stmt = select(func.count()).select_from(CampusEvent).where(CampusEvent.source_id == source_id)
        return (await session.execute(stmt)).scalar_one()

    async def search_events(
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
        source_code: str | None,
        sort_by: str,
    ) -> dict:
        stmt = (
            select(CampusEvent, Source.code.label("source_code"))
            .join(Source, Source.id == CampusEvent.source_id)
            .where(CampusEvent.event_status != "deleted")
        )

        if keyword:
            stmt = stmt.where(
                or_(
                    CampusEvent.title.ilike(f"%{keyword}%"),
                    CampusEvent.company_name.ilike(f"%{keyword}%"),
                    CampusEvent.school_name.ilike(f"%{keyword}%"),
                    CampusEvent.venue.ilike(f"%{keyword}%"),
                )
            )
        if city:
            stmt = stmt.where(CampusEvent.city == city)
        if school:
            stmt = stmt.where(CampusEvent.school_name.ilike(f"%{school}%"))
        if company:
            stmt = stmt.where(CampusEvent.company_name.ilike(f"%{company}%"))
        if event_type:
            stmt = stmt.where(CampusEvent.event_type == event_type)
        if source_code:
            stmt = stmt.where(Source.code == source_code)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(count_stmt)).scalar_one()

        if sort_by == "recent":
            stmt = stmt.order_by(CampusEvent.created_at.desc())
        else:
            stmt = stmt.order_by(CampusEvent.starts_at.asc().nullslast(), CampusEvent.id.desc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await session.execute(stmt)).all()

        items = []
        for event, source in rows:
            items.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "company_name": event.company_name,
                    "school_name": event.school_name,
                    "city": event.city,
                    "venue": event.venue,
                    "starts_at": event.starts_at,
                    "event_type": event.event_type,
                    "event_status": event.event_status,
                    "source_code": source,
                    "source_url": event.source_url,
                }
            )

        return {"items": items, "page": page, "page_size": page_size, "total": total}

    async def get_event_detail(self, session: AsyncSession, event_id: int) -> dict | None:
        stmt = (
            select(CampusEvent, Source.code.label("source_code"))
            .join(Source, Source.id == CampusEvent.source_id)
            .where(CampusEvent.id == event_id)
        )
        row = (await session.execute(stmt)).first()
        if row is None:
            return None
        event, source_code = row
        return {
            "id": event.id,
            "title": event.title,
            "company_name": event.company_name,
            "school_name": event.school_name,
            "province": event.province,
            "city": event.city,
            "venue": event.venue,
            "starts_at": event.starts_at,
            "ends_at": event.ends_at,
            "event_type": event.event_type,
            "event_status": event.event_status,
            "description": event.description,
            "tags": event.tags_json or [],
            "source_code": source_code,
            "source_url": event.source_url,
            "registration_url": event.registration_url,
        }

    async def get_by_id(self, session: AsyncSession, event_id: int) -> CampusEvent | None:
        stmt = select(CampusEvent).where(CampusEvent.id == event_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    async def basic_stats(self, session: AsyncSession) -> dict:
        by_source_stmt = (
            select(Source.code, func.count(CampusEvent.id))
            .join(CampusEvent, CampusEvent.source_id == Source.id)
            .group_by(Source.code)
            .order_by(Source.code.asc())
        )
        by_city_stmt = (
            select(CampusEvent.city, func.count(CampusEvent.id))
            .group_by(CampusEvent.city)
            .order_by(func.count(CampusEvent.id).desc())
            .limit(20)
        )
        by_school_stmt = (
            select(CampusEvent.school_name, func.count(CampusEvent.id))
            .group_by(CampusEvent.school_name)
            .order_by(func.count(CampusEvent.id).desc())
            .limit(20)
        )

        by_source = [{"source": code, "count": count} for code, count in (await session.execute(by_source_stmt)).all()]
        by_city = [{"city": city or "unknown", "count": count} for city, count in (await session.execute(by_city_stmt)).all()]
        by_school = [
            {"school": school or "unknown", "count": count}
            for school, count in (await session.execute(by_school_stmt)).all()
        ]
        return {"by_source": by_source, "by_city": by_city, "by_school": by_school}
