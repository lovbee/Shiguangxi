"""FastAPI 应用入口与资源生命周期管理。

启动顺序是日志 -> SQLAlchemy -> Redis -> LangGraph PostgreSQL 持久化 ->
Agent 注册表 -> Supervisor 编译；关闭时按相反方向释放外部连接。
运行命令通常是 ``uvicorn app.main:app``。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.agents.registry import build_agent_registry
from app.api.routes import chat, health, order, search, session, voice_ws
from app.core.config import get_settings
from app.core.exceptions import SessionAccessError, SessionTurnInProgressError
from app.core.logging import configure_logging
from app.graph.checkpoint import postgres_graph_persistence
from app.graph.supervisor import build_voice_shopping_supervisor
from app.repositories.db import close_db, init_db
from app.repositories.redis import close_redis, get_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """在应用启动时创建共享资源，并在应用退出时可靠关闭它们。

    ``yield`` 之前属于启动阶段，之后属于关闭阶段。图和 Worker 在启动时
    只编译一次；每个请求自己的数据库 Session 则由依赖注入单独创建。
    """
    settings = get_settings()
    configure_logging(settings.debug)
    init_db(settings)
    await init_redis(settings)
    async with postgres_graph_persistence(settings) as persistence:
        # AgentRegistry 中的 Worker 不持有请求级数据库连接，可以跨请求复用。
        app.state.agent_registry = build_agent_registry(settings, get_redis())
        # Checkpointer/Store 必须在 compile 时传入，图才能保存消息和 interrupt。
        app.state.voice_graph = build_voice_shopping_supervisor(
            checkpointer=persistence.checkpointer,
            store=persistence.store,
        )
        yield
    await close_redis()
    await close_db()


def create_app() -> FastAPI:
    """组装并返回 FastAPI 实例，不在这里主动连接外部服务。

    把工厂函数与全局 ``app`` 分开，便于测试或其他进程创建独立应用实例。
    真正的连接初始化由上面的 ``lifespan`` 完成。
    """
    settings = get_settings()
    docs_url = "/docs" if settings.env == "dev" else None
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url="/redoc" if docs_url else None,
        openapi_url="/openapi.json" if docs_url else None,
    )
    app.include_router(health.router)
    app.include_router(session.router)
    app.include_router(search.router)
    app.include_router(order.router)
    app.include_router(chat.router)
    app.include_router(voice_ws.router)

    @app.exception_handler(SessionAccessError)
    async def session_access_error_handler(_request: Request, exc: SessionAccessError) -> JSONResponse:
        """把会话越权统一转换为 403，避免向客户端泄露内部堆栈。"""
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})

    @app.exception_handler(SessionTurnInProgressError)
    async def session_turn_in_progress_handler(_request: Request, exc: SessionTurnInProgressError) -> JSONResponse:
        """文本接口中同会话的并行 Agent 请求返回可重试的冲突状态。"""
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    return app


# Uvicorn 通过 ``app.main:app`` 导入的就是这个对象。
app = create_app()
