"""Supervisor 与四个 Worker Agent 之间的类型契约。

Pydantic 模型负责运行时校验，TypedDict 描述各子图内部状态。Worker 返回的
Output 不直接修改父图，而是通过 ``to_state_patch`` 显式映射允许更新的字段，
从而减少 Agent 之间的隐式耦合。
"""

from decimal import Decimal
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from app.models.agent import AgentError


def agent_error(agent: str, code: str | None) -> list[AgentError]:
    """把分号分隔的内部错误码转换成父图统一错误结构。"""
    if not code:
        return []
    return [
        {"agent": agent, "code": value, "recoverable": True}
        for value in code.split(";")
        if value
    ]


class IntentUnderstandingInput(BaseModel):
    """意图 Worker 所需的最小上下文，不暴露完整父状态。"""

    session_id: str
    user_id: int
    utterance: str = ""
    recent_memory: list[dict[str, Any]] = Field(default_factory=list)
    semantic_memories: list[dict[str, Any]] = Field(default_factory=list)
    slots: dict[str, Any] = Field(default_factory=dict)
    phase: str = "INTENT"
    pending_order: dict[str, Any] | None = None
    last_recommendations: list[int] = Field(default_factory=list)


class IntentUnderstandingOutput(BaseModel):
    """意图、累计槽位、置信度及可选降级错误。"""

    current_intent: str
    slots: dict[str, Any] = Field(default_factory=dict)
    intent_confidence: float = 0.5
    error: str | None = None

    def to_state_patch(self) -> dict[str, Any]:
        """转换成 Supervisor 可以合并的字段补丁。"""
        patch: dict[str, Any] = {
            "current_intent": self.current_intent,
            "slots": self.slots,
            "intent_confidence": self.intent_confidence,
        }
        if self.error:
            patch["errors"] = agent_error("intent", self.error)
        return patch


class RequirementClarificationInput(BaseModel):
    """澄清 Worker 的当前话术、已知槽位和待追问字段。"""

    utterance: str = ""
    slots: dict[str, Any] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)


class RequirementClarificationOutput(BaseModel):
    """澄清检查或追问生成的结构化结果。"""

    missing_slots: list[str] = Field(default_factory=list)
    slots: dict[str, Any] = Field(default_factory=dict)
    phase: str | None = None
    pending_ask: str | None = None
    speech_text: str | None = None
    display_blocks: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None

    def to_missing_patch(self) -> dict[str, Any]:
        """inspect 模式只回传槽位及缺失项，不提前生成用户回复。"""
        return {"missing_slots": self.missing_slots, "slots": self.slots}

    def to_state_patch(self) -> dict[str, Any]:
        """ask 模式回传阶段、追问文本和错误。"""
        patch: dict[str, Any] = {
            "phase": self.phase or "CLARIFY",
            "pending_ask": self.pending_ask,
            "speech_text": self.speech_text or "",
            "display_blocks": self.display_blocks,
        }
        if self.error:
            patch["errors"] = agent_error("clarification", self.error)
        return patch


class ProductRecommendationInput(BaseModel):
    """推荐 Worker 的查询条件、会话范围和语义偏好。"""

    session_id: str
    user_id: int
    utterance: str = ""
    slots: dict[str, Any] = Field(default_factory=dict)
    session_scope: dict[str, Any] | None = None
    semantic_memories: list[dict[str, Any]] = Field(default_factory=list)
    top_n: int = 20


class ProductRecommendationOutput(BaseModel):
    """推荐流水线的候选、最终前三和用于后续下单的商品顺序。"""

    phase: str = "RECOMMEND"
    user_profile: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    display_blocks: list[dict[str, Any]] = Field(default_factory=list)
    last_recommendations: list[int] = Field(default_factory=list)
    user_needs: str = ""
    error: str | None = None

    def to_state_patch(self) -> dict[str, Any]:
        """把推荐结果映射回父图，并规范化错误来源。"""
        patch: dict[str, Any] = {
            "phase": self.phase,
            "user_profile": self.user_profile,
            "candidates": self.candidates,
            "recommendations": self.recommendations,
            "display_blocks": self.display_blocks,
            "last_recommendations": self.last_recommendations,
            "user_needs": self.user_needs,
        }
        if self.error:
            patch["errors"] = agent_error("recommendation", self.error)
        return patch


class EmotionResponseInput(BaseModel):
    """最终话术 Worker 的输入；response_mode 决定推荐、闲聊或越界分支。"""

    session_id: str
    user_id: int
    utterance: str = ""
    user_needs: str = ""
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    recent_memory: list[dict[str, Any]] = Field(default_factory=list)
    response_mode: Literal["recommendation", "chitchat", "out_of_scope"] = "recommendation"


class EmotionResponseOutput(BaseModel):
    """用户情绪、专家视角摘要、最终口播及展示商品。"""

    session_mood: str = "neutral"
    perspective_digest: str = ""
    speech_text: str = ""
    display_blocks: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None

    def to_state_patch(self) -> dict[str, Any]:
        """把用户可见回复和可恢复错误返回 Supervisor。"""
        patch: dict[str, Any] = {
            "session_mood": self.session_mood,
            "perspective_digest": self.perspective_digest,
            "speech_text": self.speech_text,
            "display_blocks": self.display_blocks,
        }
        if self.error:
            patch["errors"] = agent_error("emotion", self.error)
        return patch


class IntentWorkerState(TypedDict, total=False):
    """Intent 单节点子图的内部状态。"""

    request: dict[str, Any]
    output: dict[str, Any]


class ClarificationWorkerState(TypedDict, total=False):
    """Clarification 子图在检查与生成问题之间传递的状态。"""

    mode: Literal["inspect", "ask"]
    request: dict[str, Any]
    missing_slots: list[str]
    slots: dict[str, Any]
    output: dict[str, Any]


class RecommendationWorkerState(TypedDict, total=False):
    """Recommendation 多节点/ReAct 子图的内部中间结果。"""

    request: dict[str, Any]
    messages: Annotated[list[AnyMessage], add_messages]
    profile: dict[str, Any] | None
    candidates: list[dict[str, Any]]
    reranked: list[dict[str, Any]]
    user_needs: str
    errors: list[str]
    react_steps: int
    output: dict[str, Any]


class EmotionWorkerState(TypedDict, total=False):
    """Emotion 子图的路由输入和最终输出。"""

    request: dict[str, Any]
    session_mood: str
    perspective_digest: str
    output: dict[str, Any]


def format_user_needs(
    slots: dict[str, Any],
    semantic_memories: list[dict[str, Any]] | None = None,
) -> str:
    """把当前槽位和跨会话偏好整理成人类/Prompt 可读的一行需求。"""
    parts = [f"{key}={value}" for key, value in (slots or {}).items() if value is not None]
    parts.extend(
        f"历史偏好={memory.get('content')}"
        for memory in semantic_memories or []
        if memory.get("content")
    )
    return "; ".join(parts)


def normalize_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """统一商品字段命名并把 Decimal 价格转换成 JSON 兼容字符串。"""
    output = []
    for item in items:
        output.append(
            {
                "productId": item.get("product_id") or item.get("productId"),
                "name": item.get("name"),
                "price": str(item.get("price")) if isinstance(item.get("price"), Decimal) else item.get("price"),
                "reason": item.get("reason"),
                "matchScore": item.get("match_score") or item.get("matchScore"),
                "attributes": item.get("attributes") or {},
            }
        )
    return output
