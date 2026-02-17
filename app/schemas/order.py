from datetime import datetime

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=64)
    phone: str = Field(min_length=6, max_length=32)
    wechat_id: str | None = Field(default=None, max_length=64)
    school_name: str | None = Field(default=None, max_length=255)
    major: str | None = Field(default=None, max_length=128)
    graduation_year: int | None = None
    resume_url: str | None = Field(default=None, max_length=1024)

    target_job_id: int | None = None
    target_event_id: int | None = None
    target_company_name: str | None = Field(default=None, max_length=255)
    target_source_url: str | None = Field(default=None, max_length=1024)

    delivery_type: str = "onsite_resume_delivery"
    quantity: int = Field(default=1, ge=1, le=20)
    note: str | None = None
    amount_cents: int | None = Field(default=None, ge=0)
    currency: str = Field(default="CNY", max_length=8)


class OrderListItem(BaseModel):
    id: int
    order_no: str
    user_name: str
    phone: str
    status: str
    delivery_type: str
    target_job_id: int | None = None
    target_event_id: int | None = None
    target_company_name: str | None = None
    amount_cents: int | None = None
    currency: str
    created_at: datetime


class OrderDetail(OrderListItem):
    wechat_id: str | None = None
    school_name: str | None = None
    major: str | None = None
    graduation_year: int | None = None
    resume_url: str | None = None
    target_source_url: str | None = None
    quantity: int = 1
    note: str | None = None
