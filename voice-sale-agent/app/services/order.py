"""订单预览、人工确认、取消、库存扣减和幂等保护。

待确认订单短暂存 Redis；真正确认时同时使用 Redis NX 锁、防重复幂等键和
PostgreSQL ``SELECT FOR UPDATE`` 行锁。大模型不直接调用这些写操作，
Supervisor 只在用户明确选择与确认后进入本服务。
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import OrderRecord
from app.repositories.product import ProductRepository
from app.repositories.session import SessionRepository
from app.services.common import contains_no, contains_yes
from app.services.order_reference import resolve_order_reference

log = logging.getLogger(__name__)


@dataclass
class PendingOrder:
    """确认前冻结的订单快照；价格和商品引用来自服务器端商品表。"""

    session_id: str
    user_id: int
    merchant_id: int
    product_id: int
    product_name: str
    sku_code: str
    quantity: int
    unit_price: str
    total_amount: str
    idempotency_key: str


class PendingOrderStore:
    """按用户+会话在 Redis 保存十分钟待确认订单。"""

    def __init__(self, redis: Redis):
        """绑定共享 Redis 客户端。"""
        self.redis = redis

    def key(self, session_id: str, user_id: int) -> str:
        """生成用户隔离的待确认订单 key。"""
        return f"vs:pending_order:{user_id}:{session_id}"

    async def put(self, order: PendingOrder) -> None:
        """序列化订单快照并设置 600 秒过期时间。"""
        await self.redis.set(
            self.key(order.session_id, order.user_id),
            json.dumps(asdict(order), ensure_ascii=False),
            ex=600,
        )

    async def get(self, session_id: str, user_id: int) -> PendingOrder | None:
        """读取并再次核对 JSON 内部所有者，防止错误 key/脏数据越权。"""
        raw = await self.redis.get(self.key(session_id, user_id))
        if not raw:
            return None
        order = PendingOrder(**json.loads(raw))
        if order.session_id != session_id or int(order.user_id) != int(user_id):
            raise ValueError("待确认订单不属于当前用户或会话")
        return order

    async def remove(self, session_id: str, user_id: int) -> None:
        """确认、取消或幂等恢复完成后删除待确认订单。"""
        await self.redis.delete(self.key(session_id, user_id))


class OrderService:
    """封装确定性订单状态机和数据库事务。"""

    def __init__(
        self,
        db: AsyncSession,
        redis: Redis,
        product_repo: ProductRepository,
        pending_store: PendingOrderStore,
        session_repo: SessionRepository,
    ):
        """注入当前请求的数据库/仓库和共享 Redis 待确认存储。"""
        self.db = db
        self.redis = redis
        self.product_repo = product_repo
        self.pending_store = pending_store
        self.session_repo = session_repo

    async def preview(self, session_id: str, user_id: int, product_id: int, qty: int = 1) -> PendingOrder:
        """校验会话/商品/库存，按当前价格创建待确认快照。

        此时不扣库存，也不写 order_record；真正交易必须再调用 ``confirm``。
        """
        await self.session_repo.require_owner(session_id, user_id)
        product = await self.product_repo.get(product_id)
        if product is None:
            raise ValueError("商品不存在")
        if product.stock < qty:
            raise ValueError("库存不足")
        total = Decimal(product.price) * Decimal(qty)
        order = PendingOrder(
            session_id=session_id,
            user_id=user_id,
            merchant_id=product.merchant_id,
            product_id=product.id,
            product_name=product.name,
            sku_code=product.sku_code,
            quantity=qty,
            unit_price=str(product.price),
            total_amount=str(total),
            idempotency_key=uuid.uuid4().hex,
        )
        await self.pending_store.put(order)
        return order

    async def confirm(self, session_id: str, user_id: int) -> OrderRecord:
        """在锁与事务保护下扣库存并创建一笔幂等订单。

        先用 Redis 锁挡住同会话快速重复请求，再查幂等键；数据库行锁解决不同
        会话竞争同一商品库存，唯一约束解决 Redis 锁失效后的最终重复写入。
        """
        await self.session_repo.require_owner(session_id, user_id)
        lock_key = f"vs:lock:order:{user_id}:{session_id}"
        if not await self.redis.set(lock_key, "1", ex=10, nx=True):
            raise ValueError("订单正在处理中，请稍等")
        try:
            pending = await self.pending_store.get(session_id, user_id)
            if pending is None:
                raise ValueError("没有待确认订单，或已过期")
            # 重试/网络重复确认如果已经成功，直接返回原订单，不再扣库存。
            existing = await self._find_by_idempotency_key(pending.idempotency_key)
            if existing is not None:
                await self.pending_store.remove(session_id, user_id)
                return existing
            # 行锁一直持有到 commit/rollback，确保检查和扣减库存不可被穿插。
            product = await self.product_repo.get_for_update(pending.product_id)
            if product is None:
                raise ValueError("商品不存在")
            if product.stock < pending.quantity:
                raise ValueError("库存不足")
            product.stock -= pending.quantity
            order = OrderRecord(
                order_no=uuid.uuid4().hex,
                idempotency_key=pending.idempotency_key,
                user_id=pending.user_id,
                merchant_id=pending.merchant_id,
                session_id=session_id,
                product_id=pending.product_id,
                sku_code=pending.sku_code,
                quantity=pending.quantity,
                unit_price=Decimal(pending.unit_price),
                total_amount=Decimal(pending.total_amount),
                status="PAID",
                agent_attribution=True,
            )
            self.db.add(order)
            await self.db.commit()
            await self.pending_store.remove(session_id, user_id)
            return order
        except IntegrityError:
            # 极端并发下唯一约束可能先拒绝后到事务；回滚后读取赢家订单。
            await self.db.rollback()
            pending = await self.pending_store.get(session_id, user_id)
            existing = await self._find_by_idempotency_key(pending.idempotency_key) if pending else None
            if existing is None:
                raise
            await self.pending_store.remove(session_id, user_id)
            return existing
        except Exception:
            # AsyncSession 出错后必须 rollback，才能继续被当前请求安全使用。
            await self.db.rollback()
            raise
        finally:
            try:
                await self.redis.delete(lock_key)
            except Exception:
                log.warning("failed to release order lock: %s", lock_key, exc_info=True)

    async def cancel(self, session_id: str, user_id: int) -> None:
        """校验会话所有者后删除待确认订单，不修改库存。"""
        await self.session_repo.require_owner(session_id, user_id)
        await self.pending_store.remove(session_id, user_id)

    async def _find_by_idempotency_key(self, idempotency_key: str) -> OrderRecord | None:
        """查询同一预览是否已经生成订单。"""
        stmt = select(OrderRecord).where(OrderRecord.idempotency_key == idempotency_key)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def handle_order(self, state: dict) -> dict:
        """根据待确认订单和用户话术执行预览、确认、取消或继续追问。

        返回的是 Supervisor 状态补丁，不抛给用户 ORM 对象。若没有 pending，
        只能从 ``last_recommendations`` 的相对序号创建新预览。
        """
        session_id = state["session_id"]
        user_id = int(state["user_id"])
        utterance = state.get("utterance") or ""
        await self.session_repo.require_owner(session_id, user_id)
        pending = await self.pending_store.get(session_id, user_id)
        if pending is not None:
            # 先判断否定/肯定只发生在已有 pending 的确认阶段。
            if contains_yes(utterance):
                order = await self.confirm(session_id, user_id)
                return {
                    "phase": "ENDED",
                    "speech_text": f"下单成功，订单尾号 {order.order_no[:6]}，1-2 天送达。还想继续看看别的吗？",
                    "display_blocks": [],
                    "order_result": {"orderNo": order.order_no, "id": order.id},
                }
            if contains_no(utterance):
                await self.cancel(session_id, user_id)
                return {"phase": "RECOMMEND", "speech_text": "好的，已取消这次下单。想再看看别的款，还是换个条件？", "display_blocks": []}
            return {"phase": "ORDER_CONFIRM", "speech_text": "那你是确认要这款，还是先不要？", "display_blocks": []}

        product_id = resolve_order_reference(state, utterance)
        if product_id is None:
            return {
                "phase": state.get("phase") or "RECOMMEND",
                "speech_text": "你想要的是刚才推荐的哪一款？可以说第一款、第二款，或者商品名。",
                "display_blocks": [],
            }
        order = await self.preview(session_id, user_id, product_id, 1)
        return {
            "phase": "ORDER_CONFIRM",
            "speech_text": f"好的，帮你准备下单：{order.product_name}，单价 {order.unit_price} 元，一共 {order.total_amount} 元。确认下单吗？",
            "display_blocks": [],
            "pending_order": asdict(order),
        }
