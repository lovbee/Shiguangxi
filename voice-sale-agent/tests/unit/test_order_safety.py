"""验证订单事务回滚、重复确认幂等和 ORM 唯一约束。

所有 Redis/Repository/DB 都是可控 Fake：可以让 commit 故意失败并检查 rollback，
也能模拟同一 idempotency_key 已有订单，确保不会再次扣库存或创建新订单。
"""

from types import SimpleNamespace

import pytest

from app.models.db import OrderRecord
from app.services.order import OrderService, PendingOrderStore


class FakeRedis:
    """支持 NX 锁、待确认 JSON 和 delete 的内存 Redis。"""

    def __init__(self):
        self.data = {}

    async def set(self, key, value, *, ex=None, nx=False):
        if nx and key in self.data:
            return False
        assert ex is not None
        self.data[key] = value
        return True

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key):
        self.data.pop(key, None)


class SessionRepo:
    """测试专用所有权校验替身；参数正确即视为通过。"""

    async def require_owner(self, session_id, user_id):
        if session_id != "s1" or user_id != 1:
            raise ValueError("wrong owner")
        return SimpleNamespace(id=session_id, user_id=user_id)


class ProductRepo:
    """返回一件有库存的固定商品，并记录行锁读取语义。"""

    def __init__(self):
        self.product = SimpleNamespace(
            id=10,
            merchant_id=2,
            name="Product",
            sku_code="SKU-10",
            price=100,
            stock=5,
        )
        self.lock_calls = 0

    async def get(self, _product_id):
        return self.product

    async def get_for_update(self, _product_id):
        self.lock_calls += 1
        return self.product


class Result:
    """模拟 SQLAlchemy Result.scalar_one_or_none。"""

    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeDb:
    """可配置 commit 失败或幂等查询结果的最小 AsyncSession。"""

    def __init__(self, *, existing=None, fail_commit=False):
        self.existing = existing
        self.fail_commit = fail_commit
        self.rollback_calls = 0
        self.added = []

    async def execute(self, _stmt):
        return Result(self.existing)

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        if self.fail_commit:
            raise RuntimeError("commit failed")

    async def rollback(self):
        self.rollback_calls += 1


def build_service(db):
    """用同一组 Fake 组装 OrderService，减少测试重复样板。"""
    redis = FakeRedis()
    products = ProductRepo()
    return (
        OrderService(db, redis, products, PendingOrderStore(redis), SessionRepo()),
        redis,
        products,
    )


@pytest.mark.asyncio
async def test_order_confirmation_rolls_back_failed_transaction():
    db = FakeDb(fail_commit=True)
    service, _redis, products = build_service(db)
    await service.preview("s1", 1, 10)

    with pytest.raises(RuntimeError, match="commit failed"):
        await service.confirm("s1", 1)

    assert db.rollback_calls == 1
    assert products.product.stock == 4
    assert products.lock_calls == 1


@pytest.mark.asyncio
async def test_order_confirmation_returns_existing_idempotent_order():
    existing = SimpleNamespace(id=99, order_no="existing")
    db = FakeDb(existing=existing)
    service, _redis, products = build_service(db)
    pending = await service.preview("s1", 1, 10)

    result = await service.confirm("s1", 1)

    assert result is existing
    assert products.lock_calls == 0
    assert await service.pending_store.get("s1", 1) is None
    assert pending.idempotency_key


def test_order_idempotency_key_has_database_unique_constraint():
    column = OrderRecord.__table__.c.idempotency_key
    assert column.unique is True
    assert column.nullable is False
