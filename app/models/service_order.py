from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ServiceOrder(Base, TimestampMixin):
    __tablename__ = "service_orders"
    __table_args__ = (
        Index("ix_service_orders_status", "status"),
        Index("ix_service_orders_phone", "phone"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    user_name: Mapped[str] = mapped_column(String(64))
    phone: Mapped[str] = mapped_column(String(32))
    wechat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    school_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    major: Mapped[str | None] = mapped_column(String(128), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resume_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    target_job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    target_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("campus_events.id", ondelete="SET NULL"), nullable=True
    )
    target_company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    delivery_type: Mapped[str] = mapped_column(String(32), default="onsite_resume_delivery")
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="created")
    amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
