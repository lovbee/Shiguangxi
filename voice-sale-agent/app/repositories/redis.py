"""Redis 异步客户端的进程级生命周期管理。"""

import redis.asyncio as redis

from app.core.config import Settings

_client: redis.Redis | None = None


async def init_redis(settings: Settings) -> None:
    """创建客户端并立刻 PING，确保错误在启动阶段暴露。"""
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
        await _client.ping()


async def close_redis() -> None:
    """关闭连接池并清除全局客户端。"""
    global _client
    if _client is not None:
        await _client.aclose()
    _client = None


def get_redis() -> redis.Redis:
    """返回共享 Redis 客户端；未初始化时给出明确异常。"""
    if _client is None:
        raise RuntimeError("Redis is not initialized")
    return _client
