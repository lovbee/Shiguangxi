"""当前用户的订单只读查询接口。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.repositories.order import OrderRepository

router = APIRouter(prefix="/internal/v1/orders", tags=["internal-orders"])


def order_to_dict(order) -> dict:
    """把 ORM 订单转成前端友好的字典，并安全序列化 Decimal。"""
    return {
        "id": order.id,
        "orderNo": order.order_no,
        "userId": order.user_id,
        "merchantId": order.merchant_id,
        "sessionId": order.session_id,
        "productId": order.product_id,
        "skuCode": order.sku_code,
        "quantity": order.quantity,
        "unitPrice": str(order.unit_price),
        "totalAmount": str(order.total_amount),
        "status": order.status,
        "createdAt": order.created_at,
    }


@router.get("/mine")
async def list_mine(user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)) -> list[dict]:
    """列出当前登录用户的订单，不能传入其他用户 ID。"""
    return [order_to_dict(o) for o in await OrderRepository(db).list_for_user(user_id)]


@router.get("/{order_id}")
async def get_order(order_id: int, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)) -> dict:
    """读取当前用户的一笔订单；不存在或不属于用户时统一返回 404。"""
    order = await OrderRepository(db).get_for_user(order_id, user_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order_to_dict(order)
