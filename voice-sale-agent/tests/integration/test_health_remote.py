"""验证当前 ``.env`` 指向的 PostgreSQL 和 Redis 确实可连接。

该测试会访问真实外部服务，所以带 integration 标记；它只检查基础连通性，
不会验证 LLM、向量检索或语音供应商。
"""

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.repositories.db import close_db, init_db, session_scope
from app.repositories.redis import close_redis, get_redis, init_redis


@pytest.mark.integration
async def test_remote_postgres_and_redis_are_healthy():
    """执行数据库 SELECT 1 和 Redis PING，并在 finally 中关闭全局资源。"""
    settings = get_settings()
    init_db(settings)
    await init_redis(settings)
    try:
        async for db in session_scope():
            assert (await db.execute(text("SELECT 1"))).scalar_one() == 1
        assert await get_redis().ping() is True
    finally:
        await close_redis()
        await close_db()
