from datetime import datetime

from pydantic import BaseModel, Field


class JobSearchQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "time"
    keyword: str | None = None
    province: str | None = None
    city: str | None = None
    district: str | None = None
    category: str | None = None
    education: str | None = None
    experience_min: int | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    industry: str | None = None
    source: str | None = None


class JobListItem(BaseModel):
    id: int
    title: str
    company_name: str
    city: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    education_requirement: str | None = None
    published_at: datetime | None = None
    source_code: str


class JobDetail(JobListItem):
    source_url: str
    job_category: str | None = None
    seniority: str | None = None
    responsibilities: str | None = None
    qualifications: str | None = None
    tags: list[str] = []
    benefits: list[str] = []
