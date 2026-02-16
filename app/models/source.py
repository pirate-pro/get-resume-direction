from typing import Any

from sqlalchemy import Boolean, Enum as SAEnum, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import SourceType


class Source(Base, TimestampMixin):
    __tablename__ = "sources"
    __table_args__ = (
        Index("ix_sources_enabled", "enabled"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="sourcetype"), default=SourceType.platform
    )

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    robots_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    paused_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
