"""Emotion Worker：把结构化推荐包装成自然、可播报的中文回复。

它按 response_mode 分为推荐、购物闲聊和越界三条分支。推荐分支还会判断
用户情绪，并可并发获取价格/专业/入门三个视角；所有模型环节都有确定性兜底，
确保口播失败时商品卡片不会丢失。
"""

import asyncio
import json
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.contracts import (
    EmotionResponseInput,
    EmotionResponseOutput,
    EmotionWorkerState,
    normalize_items,
)
from app.agents.llm import ChatClient
from app.agents.prompts import PromptLoader
from app.core.config import Settings
from app.services.mood import SessionMoodDetector

log = logging.getLogger(__name__)


class EmotionResponseAgent:
    """最终用户话术的三分支 StateGraph。"""

    prompt_path = "prompts/emotion-merged.txt"
    perspective_prompt_paths = (
        ("\u4ef7\u683c\u987e\u95ee", "prompts/perspective_price.txt"),
        ("\u4e13\u4e1a\u8dd1\u8005", "prompts/perspective_pro.txt"),
        ("\u5165\u95e8\u4e70\u5bb6", "prompts/perspective_beginner.txt"),
    )
    empty_recommendation_text = (
        "\u6211\u5e2e\u4f60\u627e\u4e86\u4e00\u4e0b\uff0c\u8fd9\u4e2a\u6761\u4ef6\u4e0b\u5408\u9002\u7684\u4e0d\u591a\uff0c"
        "\u8981\u4e0d\u8981\u653e\u5bbd\u4e00\u70b9\u9884\u7b97\u6216\u6362\u4e2a\u6761\u4ef6\u770b\u770b\uff1f"
    )
    chitchat_fallback = (
        "\u53ef\u4ee5\u804a\uff0c\u4e0d\u8fc7\u6211\u4e3b\u8981\u662f\u5e2e\u4f60\u6311\u5546\u54c1\u3002"
        "\u4f60\u73b0\u5728\u60f3\u770b\u54ea\u7c7b\u5546\u54c1\uff1f"
    )
    out_of_scope_text = (
        "\u6211\u73b0\u5728\u4e3b\u8981\u8d1f\u8d23\u5e2e\u4f60\u6311\u5546\u54c1\u548c\u5b8c\u6210\u5bfc\u8d2d\uff0c"
        "\u8fd9\u4e2a\u95ee\u9898\u53ef\u4ee5\u627e\u5ba2\u670d\u5904\u7406\u3002\u6211\u4eec\u7ee7\u7eed\u804a\u60f3\u4e70\u4ec0\u4e48\uff1f"
    )

    def __init__(self, chat: ChatClient, prompts: PromptLoader, settings: Settings, mood_detector: SessionMoodDetector):
        """注入模型与情绪规则，并在启动期编译响应子图。"""
        self.chat = chat
        self.prompts = prompts
        self.settings = settings
        self.mood_detector = mood_detector
        self.graph = self._build_graph()

    async def run(self, request: EmotionResponseInput) -> EmotionResponseOutput:
        """执行响应子图并校验最终输出。"""
        state = await self.graph.ainvoke({"request": request.model_dump()})
        return EmotionResponseOutput.model_validate(state["output"])

    def _build_graph(self):
        """根据响应模式从 START 直接路由到对应处理节点。"""
        graph = StateGraph(EmotionWorkerState)
        graph.add_node("respond_out_of_scope", self._respond_out_of_scope_node)
        graph.add_node("respond_chitchat", self._respond_chitchat_node)
        graph.add_node("respond_recommendation", self._respond_recommendation_node)
        graph.add_conditional_edges(
            START,
            self._route_response_mode,
            {
                "out_of_scope": "respond_out_of_scope",
                "chitchat": "respond_chitchat",
                "recommendation": "respond_recommendation",
            },
        )
        graph.add_edge("respond_out_of_scope", END)
        graph.add_edge("respond_chitchat", END)
        graph.add_edge("respond_recommendation", END)
        return graph.compile(name="emotion_response_agent")

    def _route_response_mode(self, state: EmotionWorkerState) -> str:
        """读取已由 Pydantic 限定的 response_mode。"""
        request = EmotionResponseInput.model_validate(state["request"])
        return request.response_mode

    async def _respond_out_of_scope_node(self, _state: EmotionWorkerState) -> dict[str, Any]:
        """越界问题不调用模型，返回固定边界话术。"""
        output = EmotionResponseOutput(speech_text=self.out_of_scope_text, display_blocks=[])
        return {"output": output.model_dump()}

    async def _respond_chitchat_node(self, state: EmotionWorkerState) -> dict[str, Any]:
        """StateGraph 适配节点：生成受购物边界限制的闲聊回复。"""
        request = EmotionResponseInput.model_validate(state["request"])
        output = await self._respond_chitchat(request)
        return {"output": output.model_dump()}

    async def _respond_recommendation_node(self, state: EmotionWorkerState) -> dict[str, Any]:
        """StateGraph 适配节点：处理推荐口播。"""
        request = EmotionResponseInput.model_validate(state["request"])
        output = await self._respond_recommendation(request)
        return {"output": output.model_dump()}

    async def _respond_chitchat(self, request: EmotionResponseInput) -> EmotionResponseOutput:
        """调用主模型处理购物相关闲聊，失败时把话题拉回选品。"""
        payload = {
            "userUtterance": request.utterance,
            "sessionMood": "neutral",
            "userNeeds": "",
            "products": [],
        }
        try:
            speech = await self.chat.complete_text(
                model=self.settings.llm_main_model,
                system=self.prompts.load(self.prompt_path),
                user=json.dumps(payload, ensure_ascii=False),
            )
            return EmotionResponseOutput(speech_text=speech, display_blocks=[])
        except Exception as exc:  # noqa: BLE001 - keep chitchat bounded to shopping
            log.warning("chitchat response failed: %s", exc)
            return EmotionResponseOutput(
                speech_text=self.chitchat_fallback,
                display_blocks=[],
                error="chitchat_response_failed",
            )

    async def _respond_recommendation(self, request: EmotionResponseInput) -> EmotionResponseOutput:
        """检测情绪、汇总专家视角并生成最终推荐口播。"""
        recs = request.recommendations or []
        if not recs:
            # 不允许模型在零候选时“幻觉”出商品，直接建议放宽条件。
            return EmotionResponseOutput(speech_text=self.empty_recommendation_text, display_blocks=[])

        try:
            mood = await self.mood_detector.detect(request.utterance or "", request.recent_memory)
        except Exception as exc:  # noqa: BLE001 - mood is useful but not required for a reply
            log.warning("mood detection failed: %s", exc)
            mood = "neutral"

        # 多视角是可选增强，失败不应阻止核心推荐回复。
        perspective_digest = await self._perspective_digest(request, recs)
        context = request.utterance or ""
        if perspective_digest:
            context += "\n\n[Perspective digest]\n" + perspective_digest
        payload = {
            "userUtterance": context,
            "sessionMood": mood,
            "userNeeds": request.user_needs or "",
            "products": normalize_items(recs),
        }
        try:
            speech = await self.chat.complete_text(
                model=self.settings.llm_main_model,
                system=self.prompts.load(self.prompt_path),
                user=json.dumps(payload, ensure_ascii=False, default=str),
            )
            return EmotionResponseOutput(
                session_mood=mood,
                perspective_digest=perspective_digest,
                speech_text=speech.strip(),
                display_blocks=recs,
            )
        except Exception as exc:  # noqa: BLE001 - fallback must preserve selected products
            log.warning("emotion response failed: %s", exc)
            return EmotionResponseOutput(
                session_mood=mood,
                perspective_digest=perspective_digest,
                speech_text=fallback_recommend_text(recs),
                display_blocks=recs,
                error="emotion_response_failed",
            )

    async def _perspective_digest(self, request: EmotionResponseInput, items: list[dict[str, Any]]) -> str:
        """并发请求三个轻量专家视角，任一异常时整体忽略该增强。

        并发调用只共享不可变文本，不访问请求级 AsyncSession，因此不会产生
        SQLAlchemy 并发使用问题。
        """
        if not self.settings.perspective_enabled:
            return ""
        product_lines = "\n".join(
            f"- {p.get('name')} / {p.get('price')} / {p.get('reason') or ''}" for p in items
        )

        async def ask(label: str, path: str) -> str:
            """加载单个角色 Prompt，并把短观点加上角色标签。"""
            reply = await self.chat.complete_text(
                model=self.settings.llm_light_model,
                system=self.prompts.load(path),
                user=(
                    f"User utterance:\n{request.utterance}\n"
                    f"Products to review:\n{product_lines}\n"
                    "Keep each perspective within 30 Chinese characters."
                ),
            )
            return f"{label}:{reply.strip()}"

        try:
            replies = await asyncio.gather(*(ask(label, path) for label, path in self.perspective_prompt_paths))
            return "\n".join(replies)
        except Exception as exc:  # noqa: BLE001 - perspectives are optional
            log.warning("perspective digest failed: %s", exc)
            return ""


def fallback_recommend_text(items: list[dict[str, Any]]) -> str:
    """主模型失败时用模板逐款拼出口播，同时保留原推荐理由。"""
    if not items:
        return EmotionResponseAgent.empty_recommendation_text
    parts = ["\u597d\u7684\uff0c\u6211\u7ed9\u4f60\u6311\u4e86\u51e0\u6b3e\u3002"]
    for idx, item in enumerate(items, 1):
        reason = item.get("reason") or "\u6574\u4f53\u6bd4\u8f83\u8d34\u5408\u4f60\u7684\u9700\u6c42"
        parts.append(f"\u7b2c{idx}\u6b3e\uff1a{item.get('name')}\uff0c{reason}\u3002")
    parts.append("\u4f60\u770b\u66f4\u60f3\u8bd5\u54ea\u4e00\u6b3e\uff1f")
    return "".join(parts)
