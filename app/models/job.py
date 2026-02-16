from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import EducationLevel, JobType, RemoteType


job_skills = Table(
    "job_skills",
    Base.metadata,
    Column("job_id", ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
    Column("weight", Numeric(5, 2), nullable=True),
)


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source_id", "external_job_id", name="uq_jobs_source_external_job_id"),
        UniqueConstraint("source_id", "dedup_fingerprint", name="uq_jobs_source_dedup_fingerprint"),
        Index("ix_jobs_published_at", "published_at"),
        Index("ix_jobs_salary_range", "salary_min", "salary_max"),
        Index("ix_jobs_job_category", "job_category"),
        Index("ix_jobs_search_vector", "search_vector", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), index=True)
    external_job_id: Mapped[str] = mapped_column(String(128))
    source_url: Mapped[str] = mapped_column(String(1024))

    dedup_fingerprint: Mapped[str] = mapped_column(String(64))
    global_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="RESTRICT"), index=True)
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(255), index=True)
    job_category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(64), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    job_type: Mapped[JobType] = mapped_column(SAEnum(JobType, name="jobtype"), default=JobType.unknown)
    remote_type: Mapped[RemoteType] = mapped_column(
        SAEnum(RemoteType, name="remotetype"), default=RemoteType.unknown
    )

    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    salary_period: Mapped[str | None] = mapped_column(String(16), nullable=True)

    education_requirement: Mapped[EducationLevel] = mapped_column(
        SAEnum(EducationLevel, name="educationlevel"), default=EducationLevel.unknown
    )
    experience_min_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_max_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    headcount: Mapped[int | None] = mapped_column(Integer, nullable=True)

    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)
    qualifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefits_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    tags_json: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at_source: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(String(32), default="active")
    search_vector: Mapped[Any] = mapped_column(TSVECTOR, nullable=True)

    company = relationship("Company")
    location = relationship("Location")
