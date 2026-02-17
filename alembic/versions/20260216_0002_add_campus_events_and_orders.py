"""add campus events and service orders

Revision ID: 20260216_0002
Revises: 20260216_0001
Create Date: 2026-02-16 16:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260216_0002"
down_revision = "20260216_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campus_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("external_event_id", sa.String(length=128), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("registration_url", sa.String(length=1024), nullable=True),
        sa.Column("dedup_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False, server_default=sa.text("'talk'")),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("school_name", sa.String(length=255), nullable=True),
        sa.Column("province", sa.String(length=64), nullable=True),
        sa.Column("city", sa.String(length=64), nullable=True),
        sa.Column("venue", sa.String(length=255), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_status", sa.String(length=32), nullable=False, server_default=sa.text("'upcoming'")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("first_crawled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("source_id", "external_event_id", name="uq_campus_events_source_external_event_id"),
        sa.UniqueConstraint("source_id", "dedup_fingerprint", name="uq_campus_events_source_dedup_fingerprint"),
    )
    op.create_index("ix_campus_events_source_id", "campus_events", ["source_id"])
    op.create_index("ix_campus_events_starts_at", "campus_events", ["starts_at"])
    op.create_index("ix_campus_events_city", "campus_events", ["city"])
    op.create_index("ix_campus_events_school_name", "campus_events", ["school_name"])
    op.create_index("ix_campus_events_event_type", "campus_events", ["event_type"])
    op.create_index("ix_campus_events_event_status", "campus_events", ["event_status"])

    op.create_table(
        "service_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_no", sa.String(length=32), nullable=False),
        sa.Column("user_name", sa.String(length=64), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("wechat_id", sa.String(length=64), nullable=True),
        sa.Column("school_name", sa.String(length=255), nullable=True),
        sa.Column("major", sa.String(length=128), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("resume_url", sa.String(length=1024), nullable=True),
        sa.Column("target_job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "target_event_id", sa.Integer(), sa.ForeignKey("campus_events.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("target_company_name", sa.String(length=255), nullable=True),
        sa.Column("target_source_url", sa.String(length=1024), nullable=True),
        sa.Column(
            "delivery_type", sa.String(length=32), nullable=False, server_default=sa.text("'onsite_resume_delivery'")
        ),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'created'")),
        sa.Column("amount_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default=sa.text("'CNY'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("order_no", name="uq_service_orders_order_no"),
    )
    op.create_index("ix_service_orders_order_no", "service_orders", ["order_no"])
    op.create_index("ix_service_orders_status", "service_orders", ["status"])
    op.create_index("ix_service_orders_phone", "service_orders", ["phone"])


def downgrade() -> None:
    op.drop_index("ix_service_orders_phone", table_name="service_orders")
    op.drop_index("ix_service_orders_status", table_name="service_orders")
    op.drop_index("ix_service_orders_order_no", table_name="service_orders")
    op.drop_table("service_orders")

    op.drop_index("ix_campus_events_event_status", table_name="campus_events")
    op.drop_index("ix_campus_events_event_type", table_name="campus_events")
    op.drop_index("ix_campus_events_school_name", table_name="campus_events")
    op.drop_index("ix_campus_events_city", table_name="campus_events")
    op.drop_index("ix_campus_events_starts_at", table_name="campus_events")
    op.drop_index("ix_campus_events_source_id", table_name="campus_events")
    op.drop_table("campus_events")
