"""四个 Worker 子图与 Supervisor 关键路由的确定性单元测试。

测试用内存 Fake 替代 DashScope、Redis、Repository 和 Store，验证短确认词上下文、
工具单调用/最大步数、推荐输出、口播降级、handoff，以及订单 interrupt/resume。
这样无需网络也能证明 LangGraph 的状态更新和路由协议没有被重构破坏。
"""

import asyncio
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from app.agents.contracts import (
    EmotionResponseInput,
    IntentUnderstandingInput,
    IntentUnderstandingOutput,
    ProductRecommendationInput,
    ProductRecommendationOutput,
    RequirementClarificationOutput,
)
from app.agents.emotion import EmotionResponseAgent
from app.agents.intent import IntentUnderstandingAgent
from app.agents.recommendation import ProductRecommendationAgent, RecommendationRuntime
from app.graph.supervisor import SupervisorDeps, build_voice_shopping_supervisor
from app.models.dto import IntentResultDto
from app.models.enums import Intent
from app.services.compliance import ComplianceChecker
from app.services.memory import recent_turns


class FakePrompts:
    """不读取磁盘，向所有 Agent 返回固定系统 Prompt。"""

    def load(self, relative_path: str) -> str:
        return f"prompt:{relative_path}"


class FakeRedis:
    """只实现 Intent 缓存需要的异步 get/set。"""

    def __init__(self):
        self.data = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def set(self, key: str, value: str, *, ex: int):
        assert ex > 0
        self.data[key] = value


class FailingChat:
    """所有模型调用都失败，用于验证确定性降级是否仍返回可用结果。"""

    settings = SimpleNamespace(llm_light_model="light", llm_main_model="main")

    async def complete_json(self, **_kwargs):
        raise AssertionError("LLM should not be called")

    async def complete_text(self, **_kwargs):
        raise AssertionError("LLM should not be called")


@pytest.mark.asyncio
async def test_intent_agent_common_confirmer_short_circuits_llm():
    agent = IntentUnderstandingAgent(FailingChat(), FakePrompts(), FakeRedis(), SimpleNamespace(llm_light_model="light"))

    output = await agent.run(
        IntentUnderstandingInput(
            session_id="s1",
            user_id=1,
            utterance="好",
            phase="ORDER_CONFIRM",
            pending_order={"product_id": 1},
        )
    )

    assert output.current_intent == Intent.ORDER_CONFIRM.value
    assert output.slots == {"confirmer": True}
    assert output.intent_confidence == 0.99


@pytest.mark.asyncio
async def test_short_confirmer_without_order_context_uses_model():
    class Chat:
        def __init__(self):
            self.called = False

        async def complete_json(self, **_kwargs):
            self.called = True
            return IntentResultDto(intent=Intent.CHITCHAT, confidence=0.8)

    chat = Chat()
    agent = IntentUnderstandingAgent(chat, FakePrompts(), FakeRedis(), SimpleNamespace(llm_light_model="light"))

    output = await agent.run(IntentUnderstandingInput(session_id="s1", user_id=1, utterance="好"))

    assert chat.called is True
    assert output.current_intent == Intent.CHITCHAT.value


@pytest.mark.asyncio
async def test_replace_shortcut_uses_recommendation_history():
    agent = IntentUnderstandingAgent(FailingChat(), FakePrompts(), FakeRedis(), SimpleNamespace(llm_light_model="light"))

    output = await agent.run(
        IntentUnderstandingInput(
            session_id="s1",
            user_id=1,
            utterance="换一个",
            phase="RECOMMEND",
            last_recommendations=[1, 2],
        )
    )

    assert output.current_intent == Intent.PRODUCT_COMPARE.value


@pytest.mark.asyncio
async def test_product_recommendation_agent_returns_structured_results():
    activity = []

    class ProfileRepo:
        async def load_snapshot(self, user_id: int):
            assert activity == ["candidates_done"]
            activity.append("profile")
            return {"user_id": user_id, "brand_affinity": {}}

    class Candidates:
        async def fetch_candidates(self, query, slots, scope, top_n):
            assert activity == []
            await asyncio.sleep(0)
            assert query == "running shoes"
            assert slots == {"category": "shoes", "budget": 900}
            assert scope == {"allowedMerchantIds": [1]}
            assert top_n == 20
            activity.append("candidates_done")
            return [
                {"product_id": 1, "name": "A", "price": 800, "match_score": 0.8, "attributes": {}},
                {"product_id": 2, "name": "B", "price": 700, "match_score": 0.7, "attributes": {}},
            ]

    class Reranker:
        def rerank(self, candidates, _profile, _slots):
            return list(reversed(candidates))

    class ReasonService:
        async def attach_reasons(self, _session_id, user_needs, products):
            assert "budget=900" in user_needs
            return [dict(p, reason="fit") for p in products]

    agent = ProductRecommendationAgent(FakePrompts())

    output = await agent.run(
        ProductRecommendationInput(
            session_id="s1",
            user_id=7,
            utterance="running shoes",
            slots={"category": "shoes", "budget": 900},
            session_scope={"allowedMerchantIds": [1]},
        ),
        RecommendationRuntime(Candidates(), ProfileRepo(), Reranker(), ReasonService()),
    )

    assert output.last_recommendations == [2, 1]
    assert output.display_blocks[0]["reason"] == "fit"
    assert output.phase == "RECOMMEND"


@pytest.mark.asyncio
async def test_recommendation_tool_planner_limits_catalog_to_one_call():
    class Planner:
        def __init__(self):
            self.calls = 0

        def bind_tools(self, tools):
            assert [tool.name for tool in tools] == ["search_product_catalog"]
            return self

        async def ainvoke(self, messages):
            self.calls += 1
            if any(isinstance(message, ToolMessage) for message in messages):
                return AIMessage(content="catalog observation is sufficient")
            return AIMessage(
                content="",
                tool_calls=[
                    {"name": "search_product_catalog", "args": {"query": "shoe"}, "id": "one"},
                    {"name": "search_product_catalog", "args": {"query": "shoe"}, "id": "two"},
                ],
            )

    class Candidates:
        def __init__(self):
            self.calls = 0

        async def fetch_candidates(self, *_args):
            self.calls += 1
            return [{"product_id": 1, "name": "A", "price": 100, "match_score": 1.0, "attributes": {}}]

    class ProfileRepo:
        async def load_snapshot(self, user_id):
            return {"user_id": user_id}

    class Reranker:
        def rerank(self, candidates, _profile, _slots):
            return candidates

    class Reasons:
        async def attach_reasons(self, _session_id, _needs, products):
            return products

    candidates = Candidates()
    planner = Planner()
    agent = ProductRecommendationAgent(FakePrompts(), planner)

    output = await agent.run(
        ProductRecommendationInput(session_id="s1", user_id=1, utterance="shoe"),
        RecommendationRuntime(candidates, ProfileRepo(), Reranker(), Reasons()),
    )

    assert candidates.calls == 1
    assert planner.calls == 2
    assert output.last_recommendations == [1]


@pytest.mark.asyncio
async def test_recommendation_react_loop_stops_at_max_steps():
    class RepeatingPlanner:
        def bind_tools(self, _tools):
            return self

        async def ainvoke(self, _messages):
            return AIMessage(
                content="",
                tool_calls=[
                    {"name": "search_product_catalog", "args": {"query": "shoe"}, "id": "one"},
                    {"name": "search_product_catalog", "args": {"query": "shoe"}, "id": "two"},
                ],
            )

    class Candidates:
        def __init__(self):
            self.calls = 0

        async def fetch_candidates(self, *_args):
            self.calls += 1
            return [{"product_id": self.calls, "name": "A", "price": 100, "attributes": {}}]

    class ProfileRepo:
        async def load_snapshot(self, user_id):
            return {"user_id": user_id}

    class Reranker:
        def rerank(self, candidates, _profile, _slots):
            return candidates

    class Reasons:
        async def attach_reasons(self, _session_id, _needs, products):
            return products

    candidates = Candidates()
    agent = ProductRecommendationAgent(FakePrompts(), RepeatingPlanner())

    output = await agent.run(
        ProductRecommendationInput(session_id="s1", user_id=1, utterance="shoe"),
        RecommendationRuntime(candidates, ProfileRepo(), Reranker(), Reasons()),
    )

    assert candidates.calls == agent.max_react_steps
    assert "product_tool_max_steps_reached" in (output.error or "")


@pytest.mark.asyncio
async def test_emotion_agent_preserves_selected_products():
    class Chat:
        async def complete_text(self, **kwargs):
            assert '"productId": 1' in kwargs["user"]
            return "speech"

    class Mood:
        async def detect(self, _utterance, _recent_turns):
            return "positive"

    settings = SimpleNamespace(llm_main_model="main", llm_light_model="light", perspective_enabled=False)
    agent = EmotionResponseAgent(Chat(), FakePrompts(), settings, Mood())
    products = [{"product_id": 1, "name": "A", "price": 100, "match_score": 0.9, "attributes": {}}]

    output = await agent.run(
        EmotionResponseInput(
            session_id="s1",
            user_id=1,
            utterance="u",
            user_needs="category=shoes",
            recommendations=products,
        )
    )

    assert output.speech_text == "speech"
    assert output.display_blocks == products
    assert output.session_mood == "positive"


@pytest.mark.asyncio
async def test_supervisor_routes_through_worker_agents():
    calls = []

    class SessionRepo:
        async def open_if_absent(self, *_args, **_kwargs):
            calls.append("load_context")

    class StateService:
        async def load(self, _session_id, _user_id):
            return {}

        async def save(self, data, _user_id):
            calls.append(("save", data["phase"], data["last_recommendations"]))

    class IntentAgent:
        async def run(self, request):
            calls.append(("intent", request.utterance))
            return IntentUnderstandingOutput(
                current_intent=Intent.PRODUCT_RECOMMENDATION.value,
                slots={"category": "shoes", "budget": 900},
                intent_confidence=0.99,
            )

    class ClarificationAgent:
        async def inspect(self, request):
            calls.append(("clarify_inspect", request.slots))
            return RequirementClarificationOutput(missing_slots=[], slots=request.slots)

    class RecommendationAgent:
        async def run(self, request, *_args):
            calls.append(("recommend", request.slots))
            product = {"product_id": 3, "name": "C", "price": 600, "match_score": 1.0, "attributes": {}}
            return ProductRecommendationOutput(
                candidates=[product],
                recommendations=[product],
                display_blocks=[product],
                last_recommendations=[3],
                user_needs="category=shoes; budget=900",
            )

    class EmotionAgent:
        async def run(self, request):
            calls.append(("emotion", request.response_mode, [p["product_id"] for p in request.recommendations]))
            return SimpleNamespace(
                to_state_patch=lambda: {
                    "speech_text": "done",
                    "display_blocks": request.recommendations,
                    "session_mood": "neutral",
                    "perspective_digest": "",
                }
            )

    deps = SupervisorDeps(
        session_repo=SessionRepo(),
        state_service=StateService(),
        product_repo=SimpleNamespace(),
        compliance=ComplianceChecker(),
        order_service=SimpleNamespace(
            pending_store=SimpleNamespace(get=lambda *_args: None),
        ),
        redis=FakeRedis(),
        intent_agent=IntentAgent(),
        clarification_agent=ClarificationAgent(),
        recommendation_agent=RecommendationAgent(),
        emotion_agent=EmotionAgent(),
    )

    async def no_pending(*_args):
        return None

    deps.order_service.pending_store.get = no_pending
    graph = build_voice_shopping_supervisor()
    result = await graph.ainvoke(
        {"session_id": "s1", "user_id": 1, "utterance": "u", "channel": "HOME_ENTRY"},
        context=deps,
    )

    assert result["speech_text"] == "done"
    assert result["last_recommendations"] == [3]
    assert ("emotion", "recommendation", [3]) in calls
    assert ("save", "RECOMMEND", [3]) in calls


@pytest.mark.asyncio
async def test_supervisor_interrupts_and_resumes_order_confirmation():
    calls = []

    class SessionRepo:
        async def open_if_absent(self, *_args, **_kwargs):
            return None

    class StateService:
        async def load(self, *_args):
            return {}

        async def save(self, data, _user_id):
            calls.append(("save", data["phase"]))

    class IntentAgent:
        async def run(self, _request):
            return IntentUnderstandingOutput(
                current_intent=Intent.ORDER_CONFIRM.value,
                slots={},
                intent_confidence=1.0,
            )

    class PendingStore:
        async def get(self, *_args):
            return None

    class OrderService:
        pending_store = PendingStore()

        async def handle_order(self, state):
            if state["utterance"] == "确认":
                calls.append("confirmed")
                return {
                    "phase": "ENDED",
                    "speech_text": "下单成功",
                    "display_blocks": [],
                    "pending_order": None,
                }
            return {
                "phase": "ORDER_CONFIRM",
                "speech_text": "确认下单吗？",
                "display_blocks": [],
                "pending_order": {"product_id": 1},
            }

    deps = SupervisorDeps(
        session_repo=SessionRepo(),
        state_service=StateService(),
        product_repo=SimpleNamespace(),
        compliance=ComplianceChecker(),
        order_service=OrderService(),
        redis=FakeRedis(),
        intent_agent=IntentAgent(),
        clarification_agent=SimpleNamespace(),
        recommendation_agent=SimpleNamespace(),
        emotion_agent=SimpleNamespace(),
    )
    graph = build_voice_shopping_supervisor(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "s-order"}}

    first = await graph.ainvoke(
        {"session_id": "s-order", "user_id": 1, "utterance": "第二款", "channel": "HOME_ENTRY"},
        config=config,
        context=deps,
    )

    assert first["phase"] == "ORDER_CONFIRM"
    assert (await graph.aget_state(config)).interrupts

    resumed = await graph.ainvoke(
        Command(resume={"utterance": "确认", "user_id": 1, "session_id": "s-order"}),
        config=config,
        context=deps,
    )

    assert resumed["phase"] == "ENDED"
    assert resumed["speech_text"] == "下单成功"
    assert "confirmed" in calls
    snapshot = await graph.aget_state(config)
    assert recent_turns(snapshot.values["messages"], 1)[0]["text"] == "用户：确认 / 助手：下单成功"
