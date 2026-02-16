from datetime import datetime

from pydantic import BaseModel, Field


class CrawlRunCreateRequest(BaseModel):
    source_code: str
    trigger_type: str = "manual"


class CrawlRunResponse(BaseModel):
    id: int
    source_id: int
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    crawled_count: int = Field(default=0)
    inserted_count: int = Field(default=0)
    updated_count: int = Field(default=0)
    failed_count: int = Field(default=0)
