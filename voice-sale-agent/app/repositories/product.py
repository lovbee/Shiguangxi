"""商品表的数据访问封装。"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Product


class ProductRepository:
    """提供商品读取和库存行锁能力，不包含推荐排序规则。"""

    def __init__(self, db: AsyncSession):
        """绑定当前请求的数据库 Session。"""
        self.db = db

    async def get(self, product_id: int) -> Product | None:
        """按主键查单个商品；不存在时返回 ``None``。"""
        return await self.db.get(Product, product_id)

    async def get_for_update(self, product_id: int) -> Product | None:
        """用 ``SELECT FOR UPDATE`` 锁定商品行，供扣库存事务使用。"""
        stmt = select(Product).where(Product.id == product_id).with_for_update()
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def find_by_ids(self, ids: Sequence[int]) -> list[Product]:
        """批量取商品，并恢复输入 ID 的顺序。

        SQL 的 ``IN`` 不保证顺序，所以先建 ``by_id`` 字典再按召回顺序重组。
        """
        if not ids:
            return []
        stmt = select(Product).where(Product.id.in_(list(ids)))
        rows = list((await self.db.execute(stmt)).scalars().all())
        by_id = {p.id: p for p in rows}
        return [by_id[i] for i in ids if i in by_id]

    async def find_by_ids_with_scope(self, ids: Sequence[int], allowed_merchant_ids: Sequence[int] | None) -> list[Product]:
        """批量取商品并再次强制商家范围，作为检索层之外的纵深校验。"""
        if not ids:
            return []
        stmt = select(Product).where(Product.id.in_(list(ids)))
        if allowed_merchant_ids:
            stmt = stmt.where(Product.merchant_id.in_(list(allowed_merchant_ids)))
        rows = list((await self.db.execute(stmt)).scalars().all())
        by_id = {p.id: p for p in rows}
        return [by_id[i] for i in ids if i in by_id]
