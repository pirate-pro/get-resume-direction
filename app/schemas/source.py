from pydantic import BaseModel


class SourceToggleRequest(BaseModel):
    enabled: bool
    reason: str | None = None


class SourceOut(BaseModel):
    code: str
    name: str
    source_type: str
    enabled: bool
    paused_reason: str | None = None
