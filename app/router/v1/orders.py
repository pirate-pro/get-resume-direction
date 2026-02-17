from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.response import success_response
from app.schemas.order import CreateOrderRequest
from app.service.order_service import OrderService

router = APIRouter()
order_service = OrderService()


@router.post("/orders")
async def create_order(
    payload: CreateOrderRequest,
    session: AsyncSession = Depends(get_session),
):
    data = await order_service.create(session, payload.model_dump())
    return success_response(data, message="订单创建成功")


@router.get("/orders")
async def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    phone: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    data = await order_service.list_orders(session, page=page, page_size=page_size, phone=phone)
    return success_response(data)


@router.get("/orders/{order_id}")
async def order_detail(order_id: int, session: AsyncSession = Depends(get_session)):
    data = await order_service.detail(session, order_id)
    return success_response(data)
