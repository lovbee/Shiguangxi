"""Intent Worker：识别六类购物意图并累计槽位。

简单确认词先走确定性规则；其余请求优先读 Redis 指纹缓存，再调用轻量模型。
任何模型/解析失败都会降级成 OUT_OF_SCOPE 和结构化错误，让父图仍能安全回复。
"""

import hashlib
import json
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.contracts import (
    IntentUnderstandingInput,
    IntentUnderstandingOutput,
    IntentWorkerState,
)
from app.agents.llm import ChatClient
from app.agents.prompts import PromptLoader
from app.core.config import Settings
from app.models.dto import IntentResultDto
from app.models.enums import Intent
from app.services.common import is_common_confirmer

log = logging.getLogger(__name__)


class IntentUnderstandingAgent:
    """封装意图理解单节点 StateGraph。"""

    prompt_path = "prompts/intent.txt"

    def __init__(self, chat: ChatClient, prompts: PromptLoader, redis: object, settings: Settings):
        """注入模型、Prompt、缓存和配置，并在启动期编译子图。"""
        self.chat = chat
        self.prompts = prompts
        self.redis = redis
        self.settings = settings
        self.graph = self._build_graph()

    async def run(self, request: IntentUnderstandingInput) -> IntentUnderstandingOutput:
        """执行子图并把内部字典重新校验成公开 Output。"""
        state = await self.graph.ainvoke({"request": request.model_dump()})
        return IntentUnderstandingOutput.model_validate(state["output"])

    def _build_graph(self):
        """编译只有“理解意图”一个业务节点的 Worker 子图。"""
        graph = StateGraph(IntentWorkerState)
        graph.add_node("understand_intent", self._understand_node)
        graph.add_edge(START, "understand_intent")
        graph.add_edge("understand_intent", END)
        return graph.compile(name="intent_understanding_agent")

    async def _understand_node(self, state: IntentWorkerState) -> dict[str, Any]:
        """StateGraph 节点适配器：字典 -> Pydantic -> 字典。"""
        request = IntentUnderstandingInput.model_validate(state["request"])
        output = await self._understand(request)
        return {"output": output.model_dump()}

    async def _understand(self, request: IntentUnderstandingInput) -> IntentUnderstandingOutput:
        """执行规则短路、缓存、模型调用、槽位合并和失败降级。"""
        utterance = request.utterance or ""
        # “好/嗯/下一个”脱离上下文没有固定含义，必须结合订单阶段和推荐历史。
        if is_common_confirmer(utterance):
            normalized = utterance.strip("，。！？,.!? ")
            if request.pending_order or request.phase == "ORDER_CONFIRM":
                return IntentUnderstandingOutput(
                    current_intent=Intent.ORDER_CONFIRM.value,
                    slots=dict(request.slots or {}, confirmer=True),
                    intent_confidence=0.99,
                )
            if request.last_recommendations and normalized in {"下一个", "再来", "换一个"}:
                return IntentUnderstandingOutput(
                    current_intent=Intent.PRODUCT_COMPARE.value,
                    slots=dict(request.slots or {}),
                    intent_confidence=0.95,
                )

        # 指纹包含所有会影响结果的上下文，避免同一句话在不同阶段错误共用缓存。
        cache_context = json.dumps(
            {
                "user_id": request.user_id,
                "utterance": utterance,
                "phase": request.phase,
                "slots": request.slots,
                "recent_memory": request.recent_memory,
                "semantic_memories": request.semantic_memories,
                "last_recommendations": request.last_recommendations,
                "has_pending_order": request.pending_order is not None,
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        fingerprint = hashlib.sha256(cache_context.encode("utf-8")).hexdigest()
        cache_key = f"vs:intent:{request.user_id}:{request.session_id}:{fingerprint}"
        cached = await self.redis.get(cache_key)
        if cached:
            try:
                parsed = json.loads(cached)
                return IntentUnderstandingOutput(
                    current_intent=parsed["intent"],
                    slots=parsed.get("slots") or {},
                    intent_confidence=parsed.get("confidence", 0.5),
                )
            except Exception as exc:  # noqa: BLE001 - bad cache entries should not fail a turn
                log.warning("intent cache ignored: %s", exc)

        # 最近消息用于消解“这个/换一个”，长期记忆用于补充跨会话稳定偏好。
        history = "\n".join(f"{t.get('role')}: {t.get('text')}" for t in request.recent_memory) or "(none)"
        long_term = "\n".join(str(item.get("content")) for item in request.semantic_memories) or "(none)"
        user = (
            f"Recent conversation summary:\n{history}\n\n"
            f"Cross-session user memories:\n{long_term}\n\n"
            f"Current user utterance:\n{utterance}\n"
        )
        try:
            result = await self.chat.complete_json(
                model=self.settings.llm_light_model,
                system=self.prompts.load(self.prompt_path),
                user=user,
                schema=IntentResultDto,
            )
            current_slots = result.slots.model_dump(exclude_none=True)
            # 新值覆盖旧值，但模型本轮没抽到的 None 不会抹掉历史条件。
            slots = dict(request.slots or {})
            slots.update({k: v for k, v in current_slots.items() if v is not None})
            payload = {"intent": result.intent.value, "slots": slots, "confidence": result.confidence}
            # 越界输入变化大且缓存价值低，避免把偶发误判固定五分钟。
            if result.intent != Intent.OUT_OF_SCOPE:
                await self.redis.set(cache_key, json.dumps(payload, ensure_ascii=False), ex=300)
            return IntentUnderstandingOutput(
                current_intent=result.intent.value,
                slots=slots,
                intent_confidence=result.confidence,
            )
        except Exception as exc:  # noqa: BLE001 - supervisor needs a deterministic route on LLM failure
            log.warning("intent understanding failed: %s", exc)
            return IntentUnderstandingOutput(
                current_intent=Intent.OUT_OF_SCOPE.value,
                slots={},
                intent_confidence=0.3,
                error="intent_understanding_failed",
            )
