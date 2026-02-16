from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.models.enums import EducationLevel, JobType, RemoteType


@dataclass
class RawJob:
    source_code: str
    external_job_id: str | None
    source_url: str
    title: str
    company_name: str
    city: str | None = None
    salary_text: str | None = None

    job_category: str | None = None
    seniority: str | None = None
    department: str | None = None
    education_requirement: str | None = None
    experience_min_months: int | None = None
    experience_max_months: int | None = None
    responsibilities: str | None = None
    qualifications: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    benefits: list[str] | None = None
    job_type: str | None = None
    remote_type: str | None = None
    skills_text: str | None = None

    published_at: datetime | None = None
    updated_at_source: datetime | None = None


@dataclass
class NormalizedJob:
    source_code: str
    external_job_id: str
    source_url: str
    title: str
    company_name: str

    province: str | None
    city: str | None
    district: str | None
    location_key: str

    salary_min: Decimal | None
    salary_max: Decimal | None
    salary_currency: str | None
    salary_period: str | None

    job_category: str | None
    seniority: str | None
    department: str | None

    education_requirement: EducationLevel
    experience_min_months: int | None
    experience_max_months: int | None

    responsibilities: str | None
    qualifications: str | None
    tags: list[str]
    benefits: list[str]

    job_type: JobType
    remote_type: RemoteType

    dedup_fingerprint: str
    global_fingerprint: str

    published_at: datetime | None
    updated_at_source: datetime | None
    first_crawled_at: datetime
    last_crawled_at: datetime

    skills: list[str]
