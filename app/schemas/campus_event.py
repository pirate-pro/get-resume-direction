from datetime import datetime

from pydantic import BaseModel, Field


class CampusEventSearchQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "time"
    keyword: str | None = None
    city: str | None = None
    school: str | None = None
    company: str | None = None
    event_type: str | None = None
    source: str | None = None


class CampusEventListItem(BaseModel):
    id: int
    title: str
    company_name: str | None = None
    school_name: str | None = None
    city: str | None = None
    venue: str | None = None
    starts_at: datetime | None = None
    event_type: str
    event_status: str
    source_code: str
    source_url: str


class CampusEventDetail(CampusEventListItem):
    province: str | None = None
    ends_at: datetime | None = None
    description: str | None = None
    tags: list[str] = []
    registration_url: str | None = None
