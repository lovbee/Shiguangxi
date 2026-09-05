"""订单查询接口的数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import OrderRecord


class OrderRepository:
    """只允许按当前用户查询订单，避免仅凭订单 ID 越权读取。"""

    def __init__(self, db: AsyncSession):
        """绑定当前请求的数据库 Session。"""
        self.db = db

    async def list_for_user(self, user_id: int) -> list[OrderRecord]:
        """按创建时间倒序返回用户全部订单。"""
        stmt = select(OrderRecord).where(OrderRecord.user_id == user_id).order_by(OrderRecord.created_at.desc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_for_user(self, order_id: int, user_id: int) -> OrderRecord | None:
        """同时匹配订单 ID 和用户 ID；无权访问时与不存在一样返回 ``None``。"""
        stmt = select(OrderRecord).where(OrderRecord.id == order_id, OrderRecord.user_id == user_id)
        return (await self.db.execute(stmt)).scalar_one_or_none()
