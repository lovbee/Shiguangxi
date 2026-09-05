"""Supervisor 的输入、内部状态和对外输出协议。

输入只包含一轮请求，内部状态包含记忆/候选/错误等所有工作字段，输出只暴露
客户端需要的数据。``Annotated`` reducer 决定并行或连续节点更新同一字段时
如何合并，而不是简单地整字段覆盖。
"""

from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from app.models.agent import AgentError

IntentName = Literal[
    "PRODUCT_RECOMMENDATION",
    "CLARIFY_NEEDED",
    "PRODUCT_COMPARE",
    "CHITCHAT",
    "ORDER_CONFIRM",
    "OUT_OF_SCOPE",
]
"""父图允许保存的意图字符串；与 ``models.enums.Intent`` 保持同步。"""


def merge_agent_errors(current: list[AgentError], new: list[AgentError]) -> list[AgentError]:
    """追加 Worker 错误并最多保留最近 50 条，防止长期会话无限增长。"""
    return (current + new)[-50:]


class VoiceShoppingInput(TypedDict):
    """每次调用 Supervisor 必须提供的最小输入。"""

    session_id: str
    user_id: int
    utterance: str
    channel: str


class VoiceShoppingState(TypedDict, total=False):
    """主图节点共享的完整工作状态。

    ``total=False`` 表示不同阶段只需持有相关字段；节点读取可选字段时应使用
    ``get`` 和合理默认值。messages/errors 使用 reducer，其余字段默认覆盖。
    """

    session_id: str
    user_id: int
    utterance: str
    channel: str
    phase: str
    current_intent: IntentName | None
    revised_intent: IntentName | None
    intent_confidence: float
    slots: dict[str, Any]
    messages: Annotated[list[AnyMessage], add_messages]
    recent_memory: list[dict[str, Any]]
    semantic_memories: list[dict[str, Any]]
    session_scope: dict[str, Any] | None
    last_recommendations: list[int]
    pending_order: dict[str, Any] | None
    candidates: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    display_blocks: list[dict[str, Any]]
    user_profile: dict[str, Any] | None
    user_needs: str
    session_mood: str
    speech_text: str
    missing_slots: list[str]
    pending_ask: str | None
    perspective_digest: str | None
    order_result: dict[str, Any] | None
    errors: Annotated[list[AgentError], merge_agent_errors]


class VoiceShoppingOutput(TypedDict, total=False):
    """图执行完成后允许返回给 API 的字段白名单。"""

    phase: str
    current_intent: IntentName | None
    revised_intent: IntentName | None
    intent_confidence: float
    slots: dict[str, Any]
    candidates: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    display_blocks: list[dict[str, Any]]
    last_recommendations: list[int]
    speech_text: str
    pending_order: dict[str, Any] | None
    order_result: dict[str, Any] | None
    errors: list[AgentError]
