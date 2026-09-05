"""FastAPI 请求/响应和意图结构化输出的数据传输对象。

DTO 只描述“接口上看到的数据长什么样”，不负责数据库查询或业务决策。
字段别名把 Python 的 snake_case 与前端常用 camelCase 隔离开。
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Channel, Intent


class StartSessionRequest(BaseModel):
    """创建导购会话时由前端提交的入口上下文。"""

    session_id: str = Field(alias="sessionId")
    channel: Channel = Channel.HOME_ENTRY
    merchant_id: int | None = Field(default=None, alias="merchantId")
    bound_product_id: int | None = Field(default=None, alias="boundProductId")


class SessionScopeDto(BaseModel):
    """会话可访问的用户、商家和绑定商品范围。"""

    user_id: int = Field(alias="userId")
    allowed_merchant_ids: list[int] | None = Field(default=None, alias="allowedMerchantIds")
    bound_product_id: int | None = Field(default=None, alias="boundProductId")


class IntentSlots(BaseModel):
    """大模型可从用户话术中抽取的购物条件。

    这里保留 camelCase 字段是为了与既有 Prompt/状态协议兼容。``None`` 表示
    本轮没有抽到；它不会自动清除历史轮次已经保存的槽位。
    """

    category: str | None = None
    budget: int | None = None
    scenario: str | None = None
    brand: str | None = None
    gender: str | None = None
    priceDirection: str | None = None
    priceMin: int | None = None
    excludeProductIds: list[int] | None = None


class IntentResultDto(BaseModel):
    """对 Intent Agent 的 JSON 输出进行最终类型和枚举校验。"""

    intent: Intent
    slots: IntentSlots = Field(default_factory=IntentSlots)
    confidence: float = 0.5


class RecommendedItemDto(BaseModel):
    """前端商品推荐卡片所需的最小字段集合。"""

    model_config = ConfigDict(populate_by_name=True)

    product_id: int = Field(alias="productId")
    name: str
    price: Decimal | None = None
    reason: str | None = None
    match_score: float = Field(default=0.0, alias="matchScore")
    attributes: dict[str, Any] = Field(default_factory=dict)


class ChatTextRequest(BaseModel):
    """文本调试接口的一轮用户输入。"""

    session_id: str = Field(alias="sessionId")
    utterance: str


class ChatTextResponse(BaseModel):
    """文本调试接口返回的口播、商品及当前流程状态。"""

    speech_text: str = Field(alias="speechText")
    display_blocks: list[RecommendedItemDto] = Field(default_factory=list, alias="displayBlocks")
    intent: str | None = None
    phase: str | None = None


class ProductOut(BaseModel):
    """独立搜索接口返回的完整商品视图。

    ``from_attributes=True`` 允许直接从 SQLAlchemy ``Product`` 对象读取字段。
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    merchant_id: int = Field(alias="merchantId")
    sku_code: str = Field(alias="skuCode")
    name: str
    category_l1: str = Field(alias="categoryL1")
    category_l2: str = Field(alias="categoryL2")
    brand: str | None = None
    price: Decimal
    original_price: Decimal | None = Field(default=None, alias="originalPrice")
    stock: int
    attributes: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None
    selling_points: str | None = Field(default=None, alias="sellingPoints")
    status: str
