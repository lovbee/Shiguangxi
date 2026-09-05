"""SQLAlchemy 异步引擎和请求级 Session 工厂。

应用启动时调用 ``init_db``，路由通过 ``session_scope`` 获取独立 Session，
应用关闭时调用 ``close_db``。这里不自动提交事务，提交/回滚由业务代码决定。
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_db(settings: Settings) -> None:
    """按配置创建全局异步引擎和 Session 工厂；重复调用不会重复创建。"""
    global _engine, _sessionmaker
    if _engine is not None:
        return
    connect_args = {} if settings.database_ssl else {"ssl": False}
    _engine = create_async_engine(
        settings.database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def close_db() -> None:
    """释放连接池并清空全局引用，主要由 FastAPI lifespan 调用。"""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """返回已初始化工厂；启动流程有问题时尽早抛出清晰错误。"""
    if _sessionmaker is None:
        raise RuntimeError("Database is not initialized")
    return _sessionmaker


async def session_scope() -> AsyncIterator[AsyncSession]:
    """为一次请求提供独立 AsyncSession，并在请求结束后自动关闭。"""
    maker = get_sessionmaker()
    async with maker() as session:
        yield session
