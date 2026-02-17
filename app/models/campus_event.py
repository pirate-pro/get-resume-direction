from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CampusEvent(Base, TimestampMixin):
    __tablename__ = "campus_events"
    __table_args__ = (
        UniqueConstraint("source_id", "external_event_id", name="uq_campus_events_source_external_event_id"),
        UniqueConstraint("source_id", "dedup_fingerprint", name="uq_campus_events_source_dedup_fingerprint"),
        Index("ix_campus_events_starts_at", "starts_at"),
        Index("ix_campus_events_city", "city"),
        Index("ix_campus_events_school_name", "school_name"),
        Index("ix_campus_events_event_type", "event_type"),
        Index("ix_campus_events_status", "event_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), index=True)
    external_event_id: Mapped[str] = mapped_column(String(128))
    source_url: Mapped[str] = mapped_column(String(1024))
    registration_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    dedup_fingerprint: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str] = mapped_column(String(32), default="talk")

    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    province: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)

    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_status: Mapped[str] = mapped_column(String(32), default="upcoming")

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    raw_payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    first_crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
