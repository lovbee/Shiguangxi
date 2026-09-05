"""Clarification Worker：检查缺失槽位并生成自然追问。

“缺哪些字段”由 YAML 规则确定，LLM 只负责把缺失项改写成一句自然中文。
这种分工避免模型自行放宽业务必填条件，并且模型失败时仍可使用固定问句。
"""

import json
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.contracts import (
    ClarificationWorkerState,
    RequirementClarificationInput,
    RequirementClarificationOutput,
)
from app.agents.llm import ChatClient
from app.agents.prompts import PromptLoader
from app.services.clarify_rules import ClarifyRuleService

log = logging.getLogger(__name__)


class RequirementClarificationAgent:
    """同一张子图支持只检查 ``inspect`` 和生成追问 ``run`` 两种模式。"""

    prompt_path = "prompts/clarify.txt"
    fallback_question = "\u4f60\u5927\u6982\u9884\u7b97\u591a\u5c11\uff0c\u4e3b\u8981\u60f3\u7528\u5728\u4ec0\u4e48\u573a\u666f\uff1f"

    def __init__(self, chat: ChatClient, prompts: PromptLoader, clarify_rules: ClarifyRuleService):
        """注入模型、Prompt 和规则服务，并在启动期编译子图。"""
        self.chat = chat
        self.prompts = prompts
        self.clarify_rules = clarify_rules
        self.graph = self._build_graph()

    async def inspect(self, request: RequirementClarificationInput) -> RequirementClarificationOutput:
        """只计算缺失字段，供 Supervisor 决定推荐还是追问。"""
        state = await self.graph.ainvoke({"mode": "inspect", "request": request.model_dump()})
        return RequirementClarificationOutput.model_validate(state["output"])

    async def run(self, request: RequirementClarificationInput) -> RequirementClarificationOutput:
        """计算缺失字段后调用模型生成用户可听的追问。"""
        state = await self.graph.ainvoke({"mode": "ask", "request": request.model_dump()})
        return RequirementClarificationOutput.model_validate(state["output"])

    def _build_graph(self):
        """构建“检查 -> 可选追问”的条件子图。"""
        graph = StateGraph(ClarificationWorkerState)
        graph.add_node("inspect_missing_slots", self._inspect_missing_slots_node)
        graph.add_node("ask_clarifying_question", self._ask_clarifying_question_node)
        graph.add_edge(START, "inspect_missing_slots")
        graph.add_conditional_edges(
            "inspect_missing_slots",
            self._route_after_inspection,
            {"done": END, "ask": "ask_clarifying_question"},
        )
        graph.add_edge("ask_clarifying_question", END)
        return graph.compile(name="requirement_clarification_agent")

    async def _inspect_missing_slots_node(self, state: ClarificationWorkerState) -> dict[str, Any]:
        """按品类规则找缺失槽位，一轮最多保留前两个。"""
        request = RequirementClarificationInput.model_validate(state["request"])
        slots = dict(request.slots or {})
        missing = self.clarify_rules.missing_slots(slots.get("category"), slots)
        output = RequirementClarificationOutput(missing_slots=missing[:2], slots=slots)
        return {"missing_slots": output.missing_slots, "slots": slots, "output": output.model_dump()}

    def _route_after_inspection(self, state: ClarificationWorkerState) -> str:
        """inspect 到此结束；ask 模式继续进入模型改写节点。"""
        return "done" if state.get("mode") == "inspect" else "ask"

    async def _ask_clarifying_question_node(self, state: ClarificationWorkerState) -> dict[str, Any]:
        """生成一句追问，并在模型失败时返回可用的固定问题。"""
        request = RequirementClarificationInput.model_validate(state["request"])
        slots = dict(state.get("slots") or request.slots or {})
        missing = list(state.get("missing_slots") or request.missing_slots or [])
        user = (
            f"User utterance:\n{request.utterance}\n"
            f"Known slots:\n{json.dumps(slots, ensure_ascii=False)}\n"
            f"Missing required slots:\n{missing}"
        )
        # 测试 Fake Chat 不一定带 settings，因此为模型名提供无副作用默认值。
        chat_settings = getattr(self.chat, "settings", None)
        try:
            question = await self.chat.complete_text(
                model=getattr(chat_settings, "llm_light_model", "qwen-turbo"),
                system=self.prompts.load(self.prompt_path),
                user=user,
            )
            question = question.strip()
        except Exception as exc:  # noqa: BLE001 - clarification must still ask a usable question
            log.warning("requirement clarification failed: %s", exc)
            question = self.fallback_question
            output = RequirementClarificationOutput(
                missing_slots=missing,
                slots=slots,
                phase="CLARIFY",
                pending_ask=missing[0] if missing else None,
                speech_text=question,
                display_blocks=[],
                error="requirement_clarification_failed",
            )
            return {"output": output.model_dump()}
        output = RequirementClarificationOutput(
            missing_slots=missing,
            slots=slots,
            phase="CLARIFY",
            pending_ask=missing[0] if missing else None,
            speech_text=question,
            display_blocks=[],
        )
        return {"output": output.model_dump()}
