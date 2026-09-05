"""FastAPI 与 LangGraph 的依赖装配中心。

路由只声明“我需要数据库、当前用户或已编译图”，本文件负责创建具体对象。
理解 ``build_deps`` 就能看清 Repository、Service、Worker 如何连接起来。
"""

from collections.abc import AsyncIterator

from fastapi import Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.recommendation import RecommendationRuntime
from app.agents.registry import AgentRegistry, build_agent_registry
from app.core.config import Settings, get_settings
from app.core.gateway_identity import GATEWAY_USER_ID_HEADER, parse_gateway_user_id
from app.graph.supervisor import SupervisorDeps
from app.repositories.db import session_scope
from app.repositories.product import ProductRepository
from app.repositories.profile import ProfileRepository
from app.repositories.redis import get_redis
from app.repositories.session import SessionRepository, SessionStateRepository
from app.services.compliance import ComplianceChecker
from app.services.embedding import EmbeddingService
from app.services.order import OrderService, PendingOrderStore
from app.services.recommend_candidates import RecommendCandidatesService
from app.services.session_state import SessionStateService
from app.services.vector_search import ProductVectorService


async def get_db() -> AsyncIterator[AsyncSession]:
    """向一次 HTTP 请求提供独立数据库 Session，请求结束后自动关闭。"""
    async for session in session_scope():
        yield session


def get_current_user_id(
    gateway_user_id: str | None = Header(default=None, alias=GATEWAY_USER_ID_HEADER),
) -> int:
    """读取 Gateway/Java 门面认证后注入的可信用户头。"""
    return parse_gateway_user_id(gateway_user_id)


def build_deps(
    db: AsyncSession,
    agents: AgentRegistry | None = None,
    settings: Settings | None = None,
) -> SupervisorDeps:
    """为一轮图执行组装请求级运行上下文。

    ``db`` 及依赖它的 Repository/Service 不能跨请求共享；AgentRegistry、Redis
    和无状态重排器可以复用。RecommendationRuntime 单独传给推荐子图。
    """
    settings = settings or get_settings()
    redis = get_redis()
    agents = agents or build_agent_registry(settings, redis)
    # 以下对象共享同一个请求级 AsyncSession，所以推荐子图会顺序执行数据库 I/O。
    product_repo = ProductRepository(db)
    embedding = EmbeddingService(redis, settings)
    vector = ProductVectorService(db, embedding)
    candidates_service = RecommendCandidatesService(vector, product_repo)
    state_repo = SessionStateRepository(db)
    state_service = SessionStateService(state_repo, redis, settings)
    pending = PendingOrderStore(redis)
    session_repo = SessionRepository(db)
    order_service = OrderService(db, redis, product_repo, pending, session_repo)
    profile_repo = ProfileRepository(db)
    return SupervisorDeps(
        session_repo=session_repo,
        state_service=state_service,
        product_repo=product_repo,
        compliance=ComplianceChecker(),
        order_service=order_service,
        redis=redis,
        intent_agent=agents.intent,
        clarification_agent=agents.clarification,
        recommendation_agent=agents.recommendation,
        emotion_agent=agents.emotion,
        max_history_turns=settings.max_history_turns,
        recommendation_context=RecommendationRuntime(
            candidates=candidates_service,
            profile_repo=profile_repo,
            reranker=agents.reranker,
            reason_service=agents.reason_service,
        ),
    )


def get_voice_graph(request: Request):
    """从 FastAPI app.state 取得启动时编译的 Supervisor。"""
    graph = getattr(request.app.state, "voice_graph", None)
    if graph is None:
        raise RuntimeError("Voice shopping graph is not initialized")
    return graph


def get_agent_registry(request: Request) -> AgentRegistry:
    """取得启动期构建的四个 Worker，避免每个请求重复编译子图。"""
    agents = getattr(request.app.state, "agent_registry", None)
    if agents is None:
        raise RuntimeError("Agent registry is not initialized")
    return agents
