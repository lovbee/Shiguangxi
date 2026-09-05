"""同一用户会话内 Agent 轮次的 Redis 分布式互斥锁。"""

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from redis.asyncio import Redis

from app.core.exceptions import SessionTurnInProgressError

log = logging.getLogger(__name__)

# 只能删除自己持有的锁。锁超时后被另一请求取得时，旧请求的 finally 不得删除新锁。
_RELEASE_IF_OWNER_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


class SessionExecutionLock:
    """以用户和业务会话为粒度，串行化一次 LangGraph 执行。"""

    def __init__(self, redis: Redis, ttl_seconds: int):
        if ttl_seconds <= 0:
            raise ValueError("agent turn lock TTL must be positive")
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def key(session_id: str, user_id: int) -> str:
        """构造用户隔离的 Redis 锁 key。"""
        return f"vs:lock:turn:{user_id}:{session_id}"

    @asynccontextmanager
    async def hold(self, session_id: str, user_id: int) -> AsyncIterator[None]:
        """在锁持有期间执行一轮 Agent，冲突时明确拒绝后到请求。"""
        lock_key = self.key(session_id, user_id)
        token = uuid.uuid4().hex
        acquired = await self.redis.set(lock_key, token, ex=self.ttl_seconds, nx=True)
        if not acquired:
            raise SessionTurnInProgressError("当前会话正在处理中，请稍后再试")
        try:
            yield
        finally:
            try:
                await self.redis.eval(_RELEASE_IF_OWNER_SCRIPT, 1, lock_key, token)
            except Exception:
                # 让锁自然过期比在未知归属下直接 delete 更安全，也不能掩盖图执行结果。
                log.warning("failed to release agent turn lock: %s", lock_key, exc_info=True)
