from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class NormalizedCampusEvent:
    source_code: str
    external_event_id: str
    source_url: str

    title: str
    company_name: str | None
    school_name: str | None
    province: str | None
    city: str | None
    venue: str | None

    starts_at: datetime | None
    ends_at: datetime | None
    event_type: str
    event_status: str

    description: str | None
    tags: list[str]
    registration_url: str | None
    raw_payload: dict[str, Any] | None

    dedup_fingerprint: str
    first_crawled_at: datetime
    last_crawled_at: datetime
