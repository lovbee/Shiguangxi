"""Recommendation Worker：受控工具召回、画像加载、重排和理由生成。

轻量模型只能调用 ``search_product_catalog``，硬过滤、商家范围和 top_n 都由
Python Runtime 强制执行。Tool observation 最多循环三次，随后顺序加载画像、
规则重排并取前三生成理由；任何非关键步骤失败都尽量保留已有候选。
"""

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, ToolRuntime
from langgraph.runtime import Runtime

from app.agents.contracts import (
    ProductRecommendationInput,
    ProductRecommendationOutput,
    RecommendationWorkerState,
    format_user_needs,
)
from app.agents.prompts import PromptLoader
from app.repositories.profile import ProfileRepository
from app.services.profile_reranker import ProfileReranker
from app.services.recommend_candidates import RecommendCandidatesService
from app.services.recommend_reason import RecommendReasonService

log = logging.getLogger(__name__)


@dataclass
class RecommendationRuntime:
    """推荐子图运行时所需的请求级服务集合。

    这些对象依赖当前请求的 AsyncSession，不能保存到全局 AgentRegistry。
    """

    candidates: RecommendCandidatesService
    profile_repo: ProfileRepository
    reranker: ProfileReranker
    reason_service: RecommendReasonService


@tool(response_format="content_and_artifact")
async def search_product_catalog(
    query: str,
    runtime: ToolRuntime[RecommendationRuntime, RecommendationWorkerState],
) -> tuple[str, list[dict[str, Any]]]:
    """在硬过滤和会话商家范围内搜索商品目录。

    返回给模型的 ``content`` 只有命中数量，真实候选放在 ``artifact`` 中供后续
    Python 节点使用，避免让模型随意改写权威商品数据。
    """
    request = ProductRecommendationInput.model_validate(runtime.state["request"])
    candidates = await runtime.context.candidates.fetch_candidates(
        query or request.utterance,
        dict(request.slots or {}),
        request.session_scope,
        request.top_n,
    )
    return f"Found {len(candidates)} eligible products.", candidates


class ProductRecommendationAgent:
    """包含有界 ReAct 工具循环和确定性排序后处理的推荐子图。"""

    prompt_path = "prompts/recommend-reason.txt"
    tool_prompt_path = "prompts/recommend-tools.txt"
    max_react_steps = 3

    def __init__(self, prompts: PromptLoader, tool_model=None):
        """绑定允许的目录工具，并在启动期编译推荐子图。"""
        self.prompts = prompts
        self.tool_model = tool_model.bind_tools([search_product_catalog]) if tool_model is not None else None
        self.graph = self._build_graph()

    async def run(
        self,
        request: ProductRecommendationInput,
        context: RecommendationRuntime,
    ) -> ProductRecommendationOutput:
        """以空消息轨迹启动子图，并注入本请求 RecommendationRuntime。"""
        state = await self.graph.ainvoke(
            {"request": request.model_dump(), "messages": [], "errors": [], "react_steps": 0},
            context=context,
        )
        return ProductRecommendationOutput.model_validate(state["output"])

    def _build_graph(self):
        """构建工具规划 -> 结果收集 -> 画像 -> 重排 -> 理由的子图。"""
        graph = StateGraph(RecommendationWorkerState, context_schema=RecommendationRuntime)
        graph.add_node("reason_catalog", self._reason_catalog_node)
        graph.add_node(
            "catalog_tools",
            ToolNode(
                [search_product_catalog],
                messages_key="messages",
                handle_tool_errors="Product catalog search failed.",
            ),
        )
        graph.add_node("observe_catalog_tools", self._observe_catalog_tools_node)
        graph.add_node("collect_catalog_results", self._collect_catalog_results_node)
        graph.add_node("load_profile", self._load_profile_node)
        graph.add_node("rerank_products", self._rerank_products_node)
        graph.add_node("attach_recommendation_reasons", self._attach_recommendation_reasons_node)
        graph.add_edge(START, "reason_catalog")
        graph.add_conditional_edges(
            "reason_catalog",
            self._route_catalog_tools,
            {"tools": "catalog_tools", "finish": "collect_catalog_results"},
        )
        graph.add_edge("catalog_tools", "observe_catalog_tools")
        graph.add_edge("observe_catalog_tools", "reason_catalog")
        graph.add_edge("collect_catalog_results", "load_profile")
        graph.add_edge("load_profile", "rerank_products")
        graph.add_edge("rerank_products", "attach_recommendation_reasons")
        graph.add_edge("attach_recommendation_reasons", END)
        return graph.compile(name="product_recommendation_agent")

    async def _reason_catalog_node(self, state: RecommendationWorkerState) -> dict[str, Any]:
        """让轻量模型决定调用目录工具还是结束当前 ReAct 循环。"""
        request = ProductRecommendationInput.model_validate(state["request"])
        user_needs = format_user_needs(request.slots or {}, request.semantic_memories)
        react_steps = int(state.get("react_steps", 0))
        if react_steps >= self.max_react_steps:
            # 无论模型是否还想调用，达到上限都强制结束，避免无限循环和成本失控。
            errors = list(state.get("errors") or [])
            errors.append("product_tool_max_steps_reached")
            return {
                "messages": [AIMessage(content="Catalog tool loop reached its step limit.")],
                "user_needs": user_needs,
                "errors": errors,
            }
        if self.tool_model is None:
            # 单元测试/降级环境没有工具模型时，首次确定性发起一次目录查询。
            if react_steps:
                return {
                    "messages": [AIMessage(content="Catalog search observation accepted.")],
                    "user_needs": user_needs,
                }
            response = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": search_product_catalog.name,
                        "args": {"query": request.utterance},
                        "id": f"catalog-{uuid.uuid4().hex}",
                        "type": "tool_call",
                    }
                ],
            )
            return {"messages": [response], "user_needs": user_needs}

        # 模型能看到需求和范围，但不能直接构造 SQL，也不能修改库存/订单。
        planner_payload = {
            "utterance": request.utterance,
            "slots": request.slots,
            "merchantScope": request.session_scope,
            "semanticMemories": request.semantic_memories,
        }
        try:
            response = await self.tool_model.ainvoke(
                [
                    SystemMessage(content=self.prompts.load(self.tool_prompt_path)),
                    HumanMessage(content=json.dumps(planner_payload, ensure_ascii=False, default=str)),
                    *(state.get("messages") or []),
                ]
            )
            if response.tool_calls:
                # 每步最多执行一个工具调用，避免同一 AsyncSession 被并发使用。
                response = AIMessage(content=response.content, tool_calls=response.tool_calls[:1])
            return {"messages": [response], "user_needs": user_needs}
        except Exception as exc:  # noqa: BLE001 - deterministic catalog fallback remains available
            log.warning("recommendation tool planning failed: %s", exc)
            return {
                "messages": [AIMessage(content="Catalog planning unavailable.")],
                "user_needs": user_needs,
                "errors": ["product_tool_planning_failed"],
            }

    @staticmethod
    def _route_catalog_tools(state: RecommendationWorkerState) -> str:
        """最后一条 AIMessage 有 tool_calls 才进入 ToolNode，否则结束循环。"""
        messages = state.get("messages") or []
        last = messages[-1] if messages else None
        return "tools" if isinstance(last, AIMessage) and last.tool_calls else "finish"

    @staticmethod
    async def _observe_catalog_tools_node(state: RecommendationWorkerState) -> dict[str, Any]:
        """每完成一次工具 observation 就增加步数，再回到规划节点。"""
        return {"react_steps": int(state.get("react_steps", 0)) + 1}

    async def _collect_catalog_results_node(self, state: RecommendationWorkerState) -> dict[str, Any]:
        """从 ToolMessage.artifact 汇总去重候选，并记录零结果错误。"""
        candidates: list[dict[str, Any]] = []
        seen_product_ids: set[int] = set()
        for message in state.get("messages") or []:
            if isinstance(message, ToolMessage) and isinstance(message.artifact, list):
                for candidate in message.artifact:
                    product_id = candidate.get("product_id")
                    if product_id is not None and int(product_id) in seen_product_ids:
                        continue
                    if product_id is not None:
                        seen_product_ids.add(int(product_id))
                    candidates.append(candidate)
        errors = list(state.get("errors") or [])
        if not candidates:
            errors.append("product_tool_search_failed")
        return {"candidates": candidates, "errors": errors}

    async def _load_profile_node(
        self,
        state: RecommendationWorkerState,
        runtime: Runtime[RecommendationRuntime],
    ) -> dict[str, Any]:
        """确保有候选后加载用户画像；两者失败都允许后续空结果降级。"""
        request = ProductRecommendationInput.model_validate(state["request"])
        errors = list(state.get("errors") or [])
        candidates = list(state.get("candidates") or [])
        if not candidates:
            # 工具规划/执行失败时直接调用同一受控服务，不让模型故障拖垮召回。
            try:
                candidates = await runtime.context.candidates.fetch_candidates(
                    request.utterance or "",
                    dict(request.slots or {}),
                    request.session_scope,
                    request.top_n,
                )
            except Exception as exc:  # noqa: BLE001 - failed recall should not break the whole graph
                log.warning("product recommendation recall failed: %s", exc)
                errors.append("product_recall_failed")

        try:
            profile = await runtime.context.profile_repo.load_snapshot(int(request.user_id))
        except Exception as exc:  # noqa: BLE001 - anonymous reranking remains available
            log.warning("profile loading failed: %s", exc)
            profile = None
            errors.append("profile_load_failed")
        return {"profile": profile, "candidates": candidates, "errors": errors}

    async def _rerank_products_node(
        self,
        state: RecommendationWorkerState,
        runtime: Runtime[RecommendationRuntime],
    ) -> dict[str, Any]:
        """按预算和画像规则重排；失败时保持原召回顺序。"""
        request = ProductRecommendationInput.model_validate(state["request"])
        candidates = state.get("candidates") or []
        errors = list(state.get("errors") or [])
        try:
            reranked = runtime.context.reranker.rerank(candidates, state.get("profile"), request.slots or {})
        except Exception as exc:  # noqa: BLE001 - return unranked candidates if profile rerank fails
            log.warning("product rerank failed: %s", exc)
            reranked = candidates
            errors.append("product_rerank_failed")
        return {"reranked": reranked, "errors": errors}

    async def _attach_recommendation_reasons_node(
        self,
        state: RecommendationWorkerState,
        runtime: Runtime[RecommendationRuntime],
    ) -> dict[str, Any]:
        """截取前三商品生成短理由，并组装公开输出协议。"""
        request = ProductRecommendationInput.model_validate(state["request"])
        user_needs = state.get("user_needs") or format_user_needs(
            request.slots or {},
            request.semantic_memories,
        )
        errors = list(state.get("errors") or [])
        # 对外最多展示三款，完整 candidates 仍保存在输出里便于调试。
        top3 = (state.get("reranked") or [])[:3]
        try:
            with_reasons = await runtime.context.reason_service.attach_reasons(
                request.session_id,
                user_needs,
                top3,
            )
        except Exception as exc:  # noqa: BLE001 - reason generation is non-critical
            log.warning("recommendation reason generation failed: %s", exc)
            with_reasons = [dict(item) for item in top3]
            errors.append("recommend_reason_failed")

        output = ProductRecommendationOutput(
            phase="RECOMMEND",
            user_profile=state.get("profile"),
            candidates=state.get("candidates") or [],
            recommendations=with_reasons,
            display_blocks=with_reasons,
            last_recommendations=[
                int(product["product_id"])
                for product in with_reasons
                if product.get("product_id") is not None
            ],
            user_needs=user_needs,
            # dict.fromkeys 在保留首次出现顺序的同时去掉重复错误码。
            error=";".join(dict.fromkeys(errors)) or None,
        )
        return {"output": output.model_dump()}
