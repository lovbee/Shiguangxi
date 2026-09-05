"""LangGraph PostgreSQL Checkpointer 与长期 Store 的生命周期。

SQLAlchemy 业务库使用 asyncpg；LangGraph 的 PostgresSaver/Store 使用 psycopg3
连接池。二者可连接同一数据库，但驱动和连接池互相独立。
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.engine import make_url

from app.core.config import Settings
from app.services.embedding import EmbeddingService


@dataclass(frozen=True)
class GraphPersistence:
    """一起交给 Supervisor 的短期 Checkpointer 和长期语义 Store。"""

    checkpointer: AsyncPostgresSaver
    store: AsyncPostgresStore


def checkpoint_connection_string(settings: Settings) -> str:
    """把 SQLAlchemy URL 转成 psycopg URL，并按配置补充 sslmode。"""
    url = make_url(settings.database_url).set(drivername="postgresql")
    if not settings.database_ssl:
        url = url.update_query_dict({"sslmode": "disable"})
    return url.render_as_string(hide_password=False)


@asynccontextmanager
async def postgres_checkpointer(settings: Settings) -> AsyncIterator[AsyncPostgresSaver]:
    """只创建 Checkpointer 的轻量上下文，主要供独立测试使用。"""
    async with _postgres_pool(settings) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        yield checkpointer


@asynccontextmanager
async def postgres_graph_persistence(settings: Settings) -> AsyncIterator[GraphPersistence]:
    """初始化并返回 Checkpointer 与带语义索引的 Store。

    ``setup`` 会创建 LangGraph 自己需要的表。Store 的 embedding 不使用 Redis
    缓存，以免索引写入受过期缓存或模型配置变化影响。
    """
    embedding = EmbeddingService(None, settings)

    async def embed_texts(texts: list[str]) -> list[list[float]]:
        """适配 Store 要求的批量接口；当前通过 asyncio 并发单文本请求。"""
        return await asyncio.gather(*(embedding.embed(text, use_cache=False) for text in texts))

    async with _postgres_pool(settings) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        store = AsyncPostgresStore(
            pool,
            index={
                "dims": settings.embedding_dim,
                "embed": embed_texts,
                "fields": ["content"],
            },
        )
        await checkpointer.setup()
        await store.setup()
        yield GraphPersistence(checkpointer=checkpointer, store=store)


@asynccontextmanager
async def _postgres_pool(settings: Settings) -> AsyncIterator[AsyncConnectionPool]:
    """创建 psycopg 异步池，并保证上下文退出时关闭所有连接。"""
    pool = AsyncConnectionPool(
        conninfo=checkpoint_connection_string(settings),
        min_size=1,
        max_size=5,
        open=False,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )
    # 显式 open=False + await open() 让连接失败发生在可等待的启动阶段。
    await pool.open()
    try:
        yield pool
    finally:
        await pool.close()
