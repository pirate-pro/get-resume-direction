import random
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.campus_event_dao import CampusEventDAO
from app.dao.job_dao import JobDAO
from app.dao.service_order_dao import ServiceOrderDAO
from app.exceptions.base import BusinessError
from app.exceptions.codes import ORDER_NOT_FOUND, ORDER_VALIDATION_ERROR


class OrderService:
    def __init__(self) -> None:
        self.order_dao = ServiceOrderDAO()
        self.job_dao = JobDAO()
        self.event_dao = CampusEventDAO()

    async def create(self, session: AsyncSession, payload: dict) -> dict:
        target_job_id = payload.get("target_job_id")
        target_event_id = payload.get("target_event_id")
        target_company_name = payload.get("target_company_name")

        if not target_job_id and not target_event_id and not target_company_name:
            raise BusinessError(ORDER_VALIDATION_ERROR, "请至少选择职位、活动或公司", 400)

        if target_job_id and not await self.job_dao.exists_by_id(session, int(target_job_id)):
            raise BusinessError(ORDER_VALIDATION_ERROR, f"职位不存在: {target_job_id}", 400)

        if target_event_id and await self.event_dao.get_by_id(session, int(target_event_id)) is None:
            raise BusinessError(ORDER_VALIDATION_ERROR, f"活动不存在: {target_event_id}", 400)

        create_payload = {
            "order_no": self._gen_order_no(),
            "user_name": payload["user_name"],
            "phone": payload["phone"],
            "wechat_id": payload.get("wechat_id"),
            "school_name": payload.get("school_name"),
            "major": payload.get("major"),
            "graduation_year": payload.get("graduation_year"),
            "resume_url": payload.get("resume_url"),
            "target_job_id": target_job_id,
            "target_event_id": target_event_id,
            "target_company_name": target_company_name,
            "target_source_url": payload.get("target_source_url"),
            "delivery_type": payload.get("delivery_type") or "onsite_resume_delivery",
            "quantity": payload.get("quantity") or 1,
            "note": payload.get("note"),
            "status": "created",
            "amount_cents": payload.get("amount_cents"),
            "currency": payload.get("currency") or "CNY",
        }

        order = await self.order_dao.create(session, create_payload)
        await session.commit()
        return {
            "id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "created_at": order.created_at,
        }

    async def list_orders(self, session: AsyncSession, page: int, page_size: int, phone: str | None) -> dict:
        return await self.order_dao.list_orders(session, page=page, page_size=page_size, phone=phone)

    async def detail(self, session: AsyncSession, order_id: int) -> dict:
        order = await self.order_dao.get_by_id(session, order_id)
        if order is None:
            raise BusinessError(ORDER_NOT_FOUND, f"订单不存在: {order_id}", 404)
        return {
            "id": order.id,
            "order_no": order.order_no,
            "user_name": order.user_name,
            "phone": order.phone,
            "wechat_id": order.wechat_id,
            "school_name": order.school_name,
            "major": order.major,
            "graduation_year": order.graduation_year,
            "resume_url": order.resume_url,
            "target_job_id": order.target_job_id,
            "target_event_id": order.target_event_id,
            "target_company_name": order.target_company_name,
            "target_source_url": order.target_source_url,
            "delivery_type": order.delivery_type,
            "quantity": order.quantity,
            "note": order.note,
            "status": order.status,
            "amount_cents": order.amount_cents,
            "currency": order.currency,
            "created_at": order.created_at,
        }

    @staticmethod
    def _gen_order_no() -> str:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        suffix = random.randint(1000, 9999)
        return f"ODR{ts}{suffix}"
