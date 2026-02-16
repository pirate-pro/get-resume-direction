"""init core schema

Revision ID: 20260216_0001
Revises: 
Create Date: 2026-02-16 12:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260216_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    source_type_enum = sa.Enum("platform", "university", name="sourcetype")
    job_type_enum = sa.Enum(
        "full_time",
        "intern",
        "campus",
        "part_time",
        "experienced",
        "unknown",
        name="jobtype",
    )
    remote_type_enum = sa.Enum("onsite", "hybrid", "remote", "unknown", name="remotetype")
    edu_enum = sa.Enum("unknown", "college", "bachelor", "master", "phd", name="educationlevel")
    run_status_enum = sa.Enum("running", "success", "failed", "paused", name="crawlrunstatus")

    bind = op.get_bind()
    source_type_enum.create(bind, checkfirst=True)
    job_type_enum.create(bind, checkfirst=True)
    remote_type_enum.create(bind, checkfirst=True)
    edu_enum.create(bind, checkfirst=True)
    run_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("robots_allowed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("paused_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", name="uq_sources_code"),
    )
    op.create_index("ix_sources_enabled", "sources", ["enabled"])
    op.create_index("ix_sources_code", "sources", ["code"])

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("size_range", sa.String(length=64), nullable=True),
        sa.Column("funding_stage", sa.String(length=64), nullable=True),
        sa.Column("company_type", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("normalized_name", name="uq_companies_normalized_name"),
    )
    op.create_index("ix_companies_industry", "companies", ["industry"])

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country_code", sa.String(length=8), nullable=False, server_default=sa.text("'CN'")),
        sa.Column("province", sa.String(length=64), nullable=True),
        sa.Column("city", sa.String(length=64), nullable=True),
        sa.Column("district", sa.String(length=64), nullable=True),
        sa.Column("normalized_key", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("normalized_key", name="uq_locations_normalized_key"),
    )
    op.create_index("ix_locations_city", "locations", ["city"])

    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("normalized_name", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.UniqueConstraint("normalized_name", name="uq_skills_normalized_name"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("external_job_id", sa.String(length=128), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("dedup_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("global_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("job_category", sa.String(length=128), nullable=True),
        sa.Column("seniority", sa.String(length=64), nullable=True),
        sa.Column("department", sa.String(length=128), nullable=True),
        sa.Column("job_type", job_type_enum, nullable=False),
        sa.Column("remote_type", remote_type_enum, nullable=False),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(length=8), nullable=True),
        sa.Column("salary_period", sa.String(length=16), nullable=True),
        sa.Column("education_requirement", edu_enum, nullable=False),
        sa.Column("experience_min_months", sa.Integer(), nullable=True),
        sa.Column("experience_max_months", sa.Integer(), nullable=True),
        sa.Column("headcount", sa.Integer(), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("qualifications", sa.Text(), nullable=True),
        sa.Column("benefits_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tags_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at_source", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_crawled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("source_id", "external_job_id", name="uq_jobs_source_external_job_id"),
        sa.UniqueConstraint("source_id", "dedup_fingerprint", name="uq_jobs_source_dedup_fingerprint"),
    )
    op.create_index("ix_jobs_source_id", "jobs", ["source_id"])
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_location_id", "jobs", ["location_id"])
    op.create_index("ix_jobs_published_at", "jobs", ["published_at"])
    op.create_index("ix_jobs_job_category", "jobs", ["job_category"])
    op.create_index("ix_jobs_salary_range", "jobs", ["salary_min", "salary_max"])
    op.create_index("ix_jobs_search_vector", "jobs", ["search_vector"], postgresql_using="gin")

    op.create_table(
        "job_skills",
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("weight", sa.Numeric(5, 2), nullable=True),
    )

    op.create_table(
        "job_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("changed_fields_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("crawled_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_versions_job_id", "job_versions", ["job_id"])
    op.create_index("ix_job_versions_job_id_version", "job_versions", ["job_id", "version_no"])

    op.create_table(
        "crawl_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("status", run_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("crawled_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("inserted_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_crawl_runs_source_id", "crawl_runs", ["source_id"])
    op.create_index("ix_crawl_runs_source_started", "crawl_runs", ["source_id", "started_at"])

    op.create_table(
        "crawl_run_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("crawl_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_crawl_run_events_run_id", "crawl_run_events", ["run_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("file_type", sa.String(length=32), nullable=False),
        sa.Column("parse_status", sa.String(length=32), nullable=False),
        sa.Column("parsed_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_resumes_user_id", table_name="resumes")
    op.drop_table("resumes")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_crawl_run_events_run_id", table_name="crawl_run_events")
    op.drop_table("crawl_run_events")

    op.drop_index("ix_crawl_runs_source_started", table_name="crawl_runs")
    op.drop_index("ix_crawl_runs_source_id", table_name="crawl_runs")
    op.drop_table("crawl_runs")

    op.drop_index("ix_job_versions_job_id_version", table_name="job_versions")
    op.drop_index("ix_job_versions_job_id", table_name="job_versions")
    op.drop_table("job_versions")

    op.drop_table("job_skills")

    op.drop_index("ix_jobs_search_vector", table_name="jobs")
    op.drop_index("ix_jobs_salary_range", table_name="jobs")
    op.drop_index("ix_jobs_job_category", table_name="jobs")
    op.drop_index("ix_jobs_published_at", table_name="jobs")
    op.drop_index("ix_jobs_location_id", table_name="jobs")
    op.drop_index("ix_jobs_company_id", table_name="jobs")
    op.drop_index("ix_jobs_source_id", table_name="jobs")
    op.drop_table("jobs")

    op.drop_table("skills")

    op.drop_index("ix_locations_city", table_name="locations")
    op.drop_table("locations")

    op.drop_index("ix_companies_industry", table_name="companies")
    op.drop_table("companies")

    op.drop_index("ix_sources_code", table_name="sources")
    op.drop_index("ix_sources_enabled", table_name="sources")
    op.drop_table("sources")

    bind = op.get_bind()
    sa.Enum(name="crawlrunstatus").drop(bind, checkfirst=True)
    sa.Enum(name="educationlevel").drop(bind, checkfirst=True)
    sa.Enum(name="remotetype").drop(bind, checkfirst=True)
    sa.Enum(name="jobtype").drop(bind, checkfirst=True)
    sa.Enum(name="sourcetype").drop(bind, checkfirst=True)
