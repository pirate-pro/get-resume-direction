from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JobVersion(Base):
    __tablename__ = "job_versions"
    __table_args__ = (Index("ix_job_versions_job_id_version", "job_id", "version_no"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    version_no: Mapped[int] = mapped_column(Integer)
    changed_fields_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
