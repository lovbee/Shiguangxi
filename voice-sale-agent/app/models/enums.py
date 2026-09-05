"""业务中允许出现的受控枚举值。"""

from enum import StrEnum


class Intent(StrEnum):
    """Intent Agent 可返回的六种用户意图。

    使用字符串枚举既能让 Pydantic 校验非法模型输出，也能直接写入 JSON 和
    数据库。新增意图时还必须同步更新 Prompt、State 类型和 Supervisor 路由。
    """

    PRODUCT_RECOMMENDATION = "PRODUCT_RECOMMENDATION"
    CLARIFY_NEEDED = "CLARIFY_NEEDED"
    PRODUCT_COMPARE = "PRODUCT_COMPARE"
    CHITCHAT = "CHITCHAT"
    ORDER_CONFIRM = "ORDER_CONFIRM"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


class Channel(StrEnum):
    """用户从哪个页面进入导购，用于确定商品检索范围。"""

    HOME_ENTRY = "HOME_ENTRY"
    PRODUCT_PAGE = "PRODUCT_PAGE"
    SEARCH_FALLBACK = "SEARCH_FALLBACK"
    MERCHANT_HOME = "MERCHANT_HOME"
