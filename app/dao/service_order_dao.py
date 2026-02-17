from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_order import ServiceOrder


class ServiceOrderDAO:
    async def create(self, session: AsyncSession, payload: dict) -> ServiceOrder:
        order = ServiceOrder(**payload)
        session.add(order)
        await session.flush()
        return order

    async def get_by_id(self, session: AsyncSession, order_id: int) -> ServiceOrder | None:
        stmt = select(ServiceOrder).where(ServiceOrder.id == order_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    async def list_orders(self, session: AsyncSession, *, page: int, page_size: int, phone: str | None) -> dict:
        stmt = select(ServiceOrder)
        if phone:
            stmt = stmt.where(ServiceOrder.phone == phone)

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await session.execute(total_stmt)).scalar_one()
        stmt = stmt.order_by(ServiceOrder.id.desc()).offset((page - 1) * page_size).limit(page_size)
        orders = (await session.execute(stmt)).scalars().all()

        items = [
            {
                "id": order.id,
                "order_no": order.order_no,
                "user_name": order.user_name,
                "phone": order.phone,
                "status": order.status,
                "delivery_type": order.delivery_type,
                "target_job_id": order.target_job_id,
                "target_event_id": order.target_event_id,
                "target_company_name": order.target_company_name,
                "amount_cents": order.amount_cents,
                "currency": order.currency,
                "created_at": order.created_at,
            }
            for order in orders
        ]
        return {"items": items, "page": page, "page_size": page_size, "total": total}
