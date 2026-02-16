from pydantic import BaseModel


class ResumeUploadResponse(BaseModel):
    resume_id: int
    parse_status: str
