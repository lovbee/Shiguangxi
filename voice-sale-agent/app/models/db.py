"""SQLAlchemy ORM 数据库模型。

每个类对应一张 PostgreSQL 表，只描述字段映射，不包含复杂业务逻辑。
当前完整 SQL Schema 还包含 Merchant、FAQ、SessionMessage 和向量列，
它们尚未全部映射成 ORM，因此不能只靠这些类从空库生成完整结构。
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 类的声明基类，Alembic 通过其 metadata 发现表。"""


class AppUser(Base):
    """Java 用户在 Agent 数据库中的最小投影，不承担登录职责。"""

    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    nickname: Mapped[str | None] = mapped_column(String(64))
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class Product(Base):
    """可推荐商品及库存信息。

    ``attributes`` 保存不同品类不统一的扩展属性；商品 embedding 列目前只在
    SQL Schema 和原生 SQL 中使用，没有在此 ORM 类声明。
    """

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(BigInteger)
    sku_code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    category_l1: Mapped[str] = mapped_column(String(32))
    category_l2: Mapped[str] = mapped_column(String(64))
    brand: Mapped[str | None] = mapped_column(String(64))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    description: Mapped[str | None] = mapped_column(Text)
    selling_points: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="ON_SALE")
    is_new_arrival: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class UserProfileStatic(Base):
    """变化较少的用户基础画像，例如年龄、体型和预算档位。"""

    __tablename__ = "user_profile_static"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    gender: Mapped[str | None] = mapped_column(String(8))
    age: Mapped[int | None] = mapped_column(Integer)
    city: Mapped[str | None] = mapped_column(String(32))
    height_cm: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[int | None] = mapped_column(Integer)
    skin_type: Mapped[str | None] = mapped_column(String(16))
    tech_savvy: Mapped[str | None] = mapped_column(String(16))
    budget_band: Mapped[str | None] = mapped_column(String(16))
    locale: Mapped[str | None] = mapped_column(String(16))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class UserProfileDynamic(Base):
    """随浏览/购买行为变化的偏好画像，用于推荐重排。"""

    __tablename__ = "user_profile_dynamic"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category_affinity: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict)
    brand_affinity: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict)
    recent_viewed: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=list)
    recent_purchased: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=list)
    price_sensitivity: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    avg_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class ShoppingSession(Base):
    """一次导购会话的所有者、入口和结果元数据。"""

    __tablename__ = "session"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    merchant_id: Mapped[int | None] = mapped_column(BigInteger)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    channel: Mapped[str] = mapped_column(String(16))
    bound_product_id: Mapped[int | None] = mapped_column(BigInteger)
    locale: Mapped[str | None] = mapped_column(String(16))
    outcome: Mapped[str | None] = mapped_column(String(16))
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)


class SessionState(Base):
    """跨轮次需要恢复的精简业务状态。

    它不等于 LangGraph Checkpoint：这里只存阶段、槽位和上次推荐等业务事实，
    Checkpoint 另外保存节点执行位置、messages 和 interrupt。
    """

    __tablename__ = "session_state"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    phase: Mapped[str] = mapped_column(String(32), default="INTENT")
    current_intent: Mapped[str | None] = mapped_column(String(32))
    slots: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    pending_ask: Mapped[str | None] = mapped_column(Text)
    last_recommendations: Mapped[list[int] | None] = mapped_column(ARRAY(BigInteger))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class OrderRecord(Base):
    """Agent 创建的模拟订单。

    ``idempotency_key`` 的非空唯一约束是重复确认时只产生一笔订单的最后防线。
    当前演示流程创建后直接标记为 PAID，并未接入真实支付。
    """

    __tablename__ = "order_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    merchant_id: Mapped[int] = mapped_column(BigInteger)
    session_id: Mapped[str] = mapped_column(String(64))
    product_id: Mapped[int] = mapped_column(BigInteger)
    sku_code: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(16))
    agent_attribution: Mapped[bool] = mapped_column(Boolean, default=True)
    receiver_name: Mapped[str | None] = mapped_column(String(64))
    receiver_phone: Mapped[str | None] = mapped_column(String(32))
    receiver_addr: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
