"""语音导购 Supervisor 主图。

Supervisor 负责跨 Worker 编排和公共安全边界：恢复上下文、确定性修正意图、
路由、订单人工确认、合规和记忆持久化。四个 Worker 只接收各自的 Pydantic
输入，返回状态补丁；高风险订单操作始终由确定性 Service 执行。
"""

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langgraph.types import Command, interrupt

from app.agents.clarification import RequirementClarificationAgent
from app.agents.contracts import (
    EmotionResponseInput,
    IntentUnderstandingInput,
    ProductRecommendationInput,
    RequirementClarificationInput,
)
from app.agents.emotion import EmotionResponseAgent
from app.agents.intent import IntentUnderstandingAgent
from app.agents.recommendation import ProductRecommendationAgent
from app.graph.handoff import handoff_command
from app.graph.state import VoiceShoppingInput, VoiceShoppingOutput, VoiceShoppingState
from app.models.enums import Intent
from app.repositories.product import ProductRepository
from app.repositories.session import SessionRepository
from app.services.compliance import ComplianceChecker
from app.services.memory import bounded_message_update, recent_turns, turn_messages
from app.services.order import OrderService
from app.services.semantic_memory import (
    save_semantic_memories,
    search_semantic_memories,
)
from app.services.session_keys import session_scope_key
from app.services.session_state import SessionStateService


@dataclass
class SupervisorDeps:
    """每轮执行通过 Runtime.context 注入的请求级依赖。

    Repository/OrderService 共享当前请求 AsyncSession；Agent 对象在启动期编译，
    不持有该 Session，可以跨请求复用。
    """

    session_repo: SessionRepository
    state_service: SessionStateService
    product_repo: ProductRepository
    compliance: ComplianceChecker
    order_service: OrderService
    redis: object
    intent_agent: IntentUnderstandingAgent
    clarification_agent: RequirementClarificationAgent
    recommendation_agent: ProductRecommendationAgent
    emotion_agent: EmotionResponseAgent
    max_history_turns: int = 10
    recommendation_context: Any | None = None


def _deps(runtime: Runtime[SupervisorDeps]) -> SupervisorDeps:
    """读取并校验 Runtime context，避免每个节点重复空值判断。"""
    if runtime.context is None:
        raise RuntimeError("Supervisor runtime context is required")
    return runtime.context


def build_voice_shopping_supervisor(*, checkpointer=None, store=None):
    """构建并编译完整导购 StateGraph。

    ``checkpointer`` 保存线程状态和 interrupt，``store`` 保存跨线程用户偏好。
    两者由应用 lifespan 初始化，也可在单元测试中传 ``None`` 或 Fake。
    """
    graph = StateGraph(
        VoiceShoppingState,
        context_schema=SupervisorDeps,
        input_schema=VoiceShoppingInput,
        output_schema=VoiceShoppingOutput,
    )

    async def load_context(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """恢复一轮执行所需的业务状态、短期消息、长期偏好和会话范围。"""
        deps = _deps(runtime)
        session_id = state["session_id"]
        user_id = int(state["user_id"])
        await deps.session_repo.open_if_absent(
            session_id,
            user_id,
            state.get("channel") or "HOME_ENTRY",
        )
        # 业务状态优先读 Redis，未命中再从 session_state 表回填。
        persisted = await deps.state_service.load(session_id, user_id)
        # messages 已由 Checkpointer 恢复到 state；只重建最近三轮用户/最终助手消息。
        recent = recent_turns(state.get("messages") or [], 3)
        scope_raw = await deps.redis.get(session_scope_key(session_id, user_id))
        scope = json.loads(scope_raw) if scope_raw else None
        if scope and int(scope.get("userId", user_id)) != user_id:
            raise ValueError("Session scope does not belong to the current user")
        pending = await deps.order_service.pending_store.get(session_id, user_id)
        errors = []
        try:
            # 长期记忆是推荐增强能力，外部 embedding/Store 故障不能阻断整轮服务。
            semantic_memories = await search_semantic_memories(
                runtime.store,
                user_id,
                state.get("utterance") or "",
                persisted.get("slots") or {},
            )
        except Exception:  # noqa: BLE001 - long-term memory is optional for serving a turn
            semantic_memories = []
            errors.append({"agent": "memory", "code": "semantic_memory_search_failed", "recoverable": True})
        return Command(update={
            "phase": persisted.get("phase") or "INTENT",
            "slots": persisted.get("slots") or {},
            "current_intent": persisted.get("current_intent"),
            "revised_intent": None,
            "pending_ask": persisted.get("pending_ask"),
            "last_recommendations": persisted.get("last_recommendations") or [],
            "recent_memory": recent,
            "semantic_memories": semantic_memories,
            "session_scope": scope,
            "pending_order": pending.__dict__ if pending else None,
            "candidates": [],
            "recommendations": [],
            "display_blocks": [],
            "speech_text": "",
            "errors": errors,
        }, goto="order_phase_guard")

    async def order_phase_guard(state: VoiceShoppingState) -> Command:
        """待确认订单优先于普通意图识别，避免“确认”被解释成闲聊。"""
        if state.get("phase") == "ORDER_CONFIRM" and state.get("pending_order"):
            return handoff_command(
                source="supervisor",
                target="order_agent",
                goto="order",
                reason="resume pending order confirmation",
                payload={"phase": state.get("phase")},
            )
        return handoff_command(
            source="supervisor",
            target="intent_agent",
            goto="intent",
            reason="classify the current user turn",
        )

    async def intent_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """调用 Intent Worker，并把结果作为消息型 handoff 交回 Supervisor。"""
        deps = _deps(runtime)
        output = await deps.intent_agent.run(
            IntentUnderstandingInput(
                session_id=state["session_id"],
                user_id=int(state["user_id"]),
                utterance=state.get("utterance") or "",
                recent_memory=state.get("recent_memory", []),
                semantic_memories=state.get("semantic_memories", []),
                slots=state.get("slots") or {},
                phase=state.get("phase") or "INTENT",
                pending_order=state.get("pending_order"),
                last_recommendations=state.get("last_recommendations") or [],
            )
        )
        patch = output.to_state_patch()
        if output.current_intent == Intent.ORDER_CONFIRM.value:
            # 下单意图无需等待后面的规则修正，显式同步 revised_intent。
            patch["revised_intent"] = Intent.ORDER_CONFIRM.value
        return handoff_command(
            source="intent_agent",
            target="supervisor",
            goto="revise_intent",
            reason="intent classification completed",
            update=patch,
            payload={"intent": output.current_intent, "confidence": output.intent_confidence},
        )

    async def revise_intent(state: VoiceShoppingState) -> Command:
        """用上下文确定性修正模型意图，并选择下一业务节点。

        模型擅长理解自然语言，但“便宜点必须基于上次推荐比较”等关键路由由
        代码兜底，保证同一状态得到可预测结果。
        """
        current = state.get("current_intent")
        current_slots = state.get("slots") or {}
        has_last = state.get("phase") == "RECOMMEND" and bool(state.get("last_recommendations"))
        if has_last and current_slots.get("priceDirection") and current in {
            Intent.CLARIFY_NEEDED.value,
            Intent.PRODUCT_RECOMMENDATION.value,
        }:
            current = Intent.PRODUCT_COMPARE.value
        if current == Intent.CLARIFY_NEEDED.value:
            has_category = current_slots.get("category") is not None
            has_anchor = any(current_slots.get(key) is not None for key in ["budget", "scenario", "brand"])
            if has_category and has_anchor:
                current = Intent.PRODUCT_RECOMMENDATION.value
        patch = {"revised_intent": current, "slots": current_slots}
        # target 是交接消息中的业务角色名，goto 是实际 LangGraph 节点名。
        target, goto = {
            Intent.PRODUCT_RECOMMENDATION.value: ("clarification_agent", "clarify_before_recommend"),
            Intent.CLARIFY_NEEDED.value: ("clarification_agent", "clarify"),
            Intent.PRODUCT_COMPARE.value: ("comparison_worker", "compare"),
            Intent.ORDER_CONFIRM.value: ("order_agent", "order"),
            Intent.CHITCHAT.value: ("emotion_agent", "chitchat"),
            Intent.OUT_OF_SCOPE.value: ("emotion_agent", "out_of_scope"),
        }.get(current, ("emotion_agent", "out_of_scope"))
        return handoff_command(
            source="supervisor",
            target=target,
            goto=goto,
            reason=f"route intent {current or 'UNKNOWN'}",
            update=patch,
            payload={"intent": current, "slots": current_slots},
        )

    async def clarify_before_recommend(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """推荐前只检查规则必填槽位，决定直接召回还是先追问。"""
        output = await _deps(runtime).clarification_agent.inspect(
            RequirementClarificationInput(
                utterance=state.get("utterance") or "",
                slots=state.get("slots") or {},
            )
        )
        patch = output.to_missing_patch()
        needs_clarification = bool(output.missing_slots)
        return handoff_command(
            source="clarification_agent",
            target="clarification_agent" if needs_clarification else "recommendation_agent",
            goto="clarify" if needs_clarification else "recommend",
            reason="missing required slots" if needs_clarification else "requirements are complete",
            update=patch,
            payload={"missing_slots": output.missing_slots},
        )

    async def clarify_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """生成用户可听的澄清问题，再统一进入合规与记忆出口。"""
        output = await _deps(runtime).clarification_agent.run(
            RequirementClarificationInput(
                utterance=state.get("utterance") or "",
                slots=state.get("slots") or {},
                missing_slots=state.get("missing_slots") or [],
            )
        )
        return handoff_command(
            source="clarification_agent",
            target="compliance_guard",
            goto="compliance",
            reason="clarification response is ready",
            update=output.to_state_patch(),
        )

    async def compare_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """把“便宜点/贵点”转换成新价格边界，并排除刚推荐过的商品。"""
        slots = dict(state.get("slots") or {})
        last_ids = state.get("last_recommendations") or []
        direction = slots.get("priceDirection")
        if direction and last_ids:
            products = await _deps(runtime).product_repo.find_by_ids(last_ids)
            prices = [product.price for product in products if product.price is not None]
            if prices:
                # 80%/120% 是当前演示规则，不是模型生成值，也不是动态定价。
                if direction == "cheaper":
                    slots["budget"] = int(max(prices) * Decimal("0.8"))
                elif direction == "expensive":
                    slots["priceMin"] = int(min(prices) * Decimal("1.2"))
                slots["excludeProductIds"] = last_ids
        return handoff_command(
            source="comparison_worker",
            target="recommendation_agent",
            goto="recommend",
            reason="comparison constraints have been calculated",
            update={"slots": slots, "phase": "RECOMMEND"},
            payload={"slots": slots},
        )

    async def recommend_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """调用推荐子图，输出候选、前三推荐和后续下单引用顺序。"""
        deps = _deps(runtime)
        request = ProductRecommendationInput(
            session_id=state["session_id"],
            user_id=int(state["user_id"]),
            utterance=state.get("utterance") or "",
            slots=state.get("slots") or {},
            session_scope=state.get("session_scope"),
            semantic_memories=state.get("semantic_memories") or [],
            top_n=20,
        )
        if deps.recommendation_context is None:
            # 兼容测试/旧调用方；生产 build_deps 始终提供请求级推荐上下文。
            output = await deps.recommendation_agent.run(request)
        else:
            output = await deps.recommendation_agent.run(request, deps.recommendation_context)
        return handoff_command(
            source="recommendation_agent",
            target="emotion_agent",
            goto="emotion",
            reason="ranked recommendations are ready for response generation",
            update=output.to_state_patch(),
            payload={"product_ids": output.last_recommendations},
        )

    async def emotion_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """把推荐结果交给 Emotion Worker 生成最终口播。"""
        output = await _deps(runtime).emotion_agent.run(
            EmotionResponseInput(
                session_id=state["session_id"],
                user_id=int(state["user_id"]),
                utterance=state.get("utterance") or "",
                user_needs=state.get("user_needs") or "",
                recommendations=state.get("recommendations") or [],
                recent_memory=state.get("recent_memory") or [],
                response_mode="recommendation",
            )
        )
        return handoff_command(
            source="emotion_agent",
            target="compliance_guard",
            goto="compliance",
            reason="user-facing response is ready",
            update=output.to_state_patch(),
        )

    async def order_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """执行订单预览/确认/取消，并决定是否需要人工确认 interrupt。"""
        try:
            patch = await _deps(runtime).order_service.handle_order(state)
        except Exception as exc:  # noqa: BLE001 - order failures should produce a recoverable reply
            patch = {
                "speech_text": f"下单这边遇到问题：{exc}。要不要换一款看看？",
                "display_blocks": [],
                "errors": [{"agent": "order", "code": "order_operation_failed", "recoverable": True}],
            }
        # 只有首次预览且确实生成 pending_order 才进入 interrupt；模糊确认会在
        # order_confirmation 节点内部继续询问，不重新创建待确认订单。
        needs_confirmation = patch.get("phase") == "ORDER_CONFIRM" and patch.get("pending_order")
        return handoff_command(
            source="order_agent",
            target="human_confirmation" if needs_confirmation else "compliance_guard",
            goto="order_confirmation" if needs_confirmation else "compliance",
            reason="explicit order confirmation required" if needs_confirmation else "order operation completed",
            update=patch,
        )

    async def order_confirmation_node(
        state: VoiceShoppingState,
        runtime: Runtime[SupervisorDeps],
    ) -> Command:
        """暂停图等待用户明确确认/取消，模糊回答则在同一节点再次暂停。

        ``interrupt`` 会由 Checkpointer 保存当前位置；下一轮 execution.py 将用户
        话术放入 ``Command(resume=...)``，函数从 interrupt 调用处继续执行。
        """
        prompt = state.get("speech_text") or "确认下单吗？"
        while True:
            decision = interrupt(
                {
                    "type": "order_confirmation",
                    "session_id": state["session_id"],
                    "user_id": int(state["user_id"]),
                    "pending_order": state.get("pending_order"),
                    "prompt": prompt,
                }
            )
            utterance = decision.get("utterance", "") if isinstance(decision, dict) else str(decision)
            # 不直接修改 Checkpoint 中的旧 state，复制后只替换本轮 utterance。
            resumed_state = dict(state)
            resumed_state["utterance"] = utterance
            patch = await _deps(runtime).order_service.handle_order(resumed_state)
            patch["utterance"] = utterance
            if patch.get("phase") != "ORDER_CONFIRM":
                return handoff_command(
                    source="human_confirmation",
                    target="compliance_guard",
                    goto="compliance",
                    reason="human order decision received",
                    update=patch,
                )
            prompt = patch.get("speech_text") or "请明确说确认或取消。"

    async def chitchat_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """调用 Emotion Worker 的购物闲聊模式。"""
        output = await _deps(runtime).emotion_agent.run(
            EmotionResponseInput(
                session_id=state["session_id"],
                user_id=int(state["user_id"]),
                utterance=state.get("utterance") or "",
                response_mode="chitchat",
            )
        )
        return handoff_command(
            source="emotion_agent",
            target="compliance_guard",
            goto="compliance",
            reason="bounded chitchat response is ready",
            update=output.to_state_patch(),
        )

    async def out_of_scope_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """返回固定越界边界话术，并把用户引回导购任务。"""
        output = await _deps(runtime).emotion_agent.run(
            EmotionResponseInput(
                session_id=state["session_id"],
                user_id=int(state["user_id"]),
                utterance=state.get("utterance") or "",
                response_mode="out_of_scope",
            )
        )
        return handoff_command(
            source="emotion_agent",
            target="compliance_guard",
            goto="compliance",
            reason="out-of-scope response is ready",
            update=output.to_state_patch(),
        )

    async def compliance_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """对所有分支的最终口播执行同一套确定性合规清洗。"""
        return handoff_command(
            source="compliance_guard",
            target="memory_manager",
            goto="memory_update",
            reason="response passed deterministic compliance checks",
            update=_deps(runtime).compliance.ensure_compliant_state(state),
        )

    async def memory_update_node(state: VoiceShoppingState, runtime: Runtime[SupervisorDeps]) -> Command:
        """保存长期偏好、业务状态，并向 Checkpoint 追加本轮 Human/AI 消息。"""
        deps = _deps(runtime)
        user_id = int(state["user_id"])
        intent = state.get("revised_intent") or state.get("current_intent")
        speech = state.get("speech_text") or ""
        errors = []
        try:
            # 长期语义记忆失败只记录错误；短期 Checkpoint 消息仍可正常保存。
            await save_semantic_memories(
                runtime.store,
                user_id,
                state["session_id"],
                state.get("slots") or {},
            )
        except Exception:  # noqa: BLE001 - checkpointed conversation remains available
            errors.append({"agent": "memory", "code": "semantic_memory_save_failed", "recoverable": True})
        # 业务状态先写 PostgreSQL 再同步 Redis，供下轮 load_context 快速恢复。
        await deps.state_service.save(
            {
                "session_id": state["session_id"],
                "phase": state.get("phase") or "INTENT",
                "current_intent": intent,
                "slots": state.get("slots") or {},
                "pending_ask": state.get("pending_ask"),
                "last_recommendations": state.get("last_recommendations") or [],
            },
            user_id,
        )
        # handoff 消息用于 Trace；这里额外添加真正的用户/最终助手消息供短期记忆。
        new_messages = turn_messages(state.get("utterance") or "", speech)
        return Command(
            update={
                "messages": bounded_message_update(
                    state.get("messages") or [],
                    new_messages,
                    deps.max_history_turns,
                ),
                "errors": errors,
            },
            goto="finalize",
        )

    async def finalize_node(_state: VoiceShoppingState) -> dict:
        """统一结束扩展点；当前不再修改状态。"""
        return {}

    # destinations 只声明可能跳转目标，真正选择由节点返回的 Command.goto 决定。
    graph.add_node("load_context", load_context, destinations=("order_phase_guard",))
    graph.add_node("order_phase_guard", order_phase_guard, destinations=("order", "intent"))
    graph.add_node("intent", intent_node, destinations=("revise_intent",))
    graph.add_node(
        "revise_intent",
        revise_intent,
        destinations=("clarify_before_recommend", "clarify", "compare", "order", "chitchat", "out_of_scope"),
    )
    graph.add_node("clarify_before_recommend", clarify_before_recommend, destinations=("clarify", "recommend"))
    graph.add_node("clarify", clarify_node, destinations=("compliance",))
    graph.add_node("recommend", recommend_node, destinations=("emotion",))
    graph.add_node("compare", compare_node, destinations=("recommend",))
    graph.add_node("order", order_node, destinations=("order_confirmation", "compliance"))
    graph.add_node("order_confirmation", order_confirmation_node, destinations=("compliance",))
    graph.add_node("chitchat", chitchat_node, destinations=("compliance",))
    graph.add_node("out_of_scope", out_of_scope_node, destinations=("compliance",))
    graph.add_node("emotion", emotion_node, destinations=("compliance",))
    graph.add_node("compliance", compliance_node, destinations=("memory_update",))
    graph.add_node("memory_update", memory_update_node, destinations=("finalize",))
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "load_context")
    graph.add_edge("finalize", END)
    # 编译后的图可跨请求复用，请求级依赖通过 invoke 的 context 参数进入。
    return graph.compile(
        checkpointer=checkpointer,
        store=store,
        name="voice_shopping_supervisor",
    )
