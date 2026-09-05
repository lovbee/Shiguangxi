"""验证 Agent 轮次锁的获取、冲突和令牌安全释放。"""

import pytest

from app.core.exceptions import SessionTurnInProgressError
from app.services.session_execution_lock import SessionExecutionLock


class FakeRedis:
    """仅实现锁服务所需的 Redis SET/EVAL 行为。"""

    def __init__(self):
        self.data: dict[str, str] = {}
        self.set_calls: list[tuple[str, str, int, bool]] = []
        self.eval_calls: list[tuple[str, int, str, str]] = []

    async def set(self, key, value, *, ex, nx):
        self.set_calls.append((key, value, ex, nx))
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True

    async def eval(self, script, key_count, key, token):
        self.eval_calls.append((script, key_count, key, token))
        if self.data.get(key) == token:
            del self.data[key]
            return 1
        return 0


@pytest.mark.asyncio
async def test_turn_lock_sets_user_scoped_key_and_releases_after_turn():
    redis = FakeRedis()
    lock = SessionExecutionLock(redis, ttl_seconds=180)

    async with lock.hold("s1", 7):
        key = "vs:lock:turn:7:s1"
        assert key in redis.data
        assert redis.set_calls[0][0] == key
        assert redis.set_calls[0][2:] == (180, True)

    assert redis.data == {}
    assert redis.eval_calls[0][1:3] == (1, "vs:lock:turn:7:s1")


@pytest.mark.asyncio
async def test_turn_lock_rejects_concurrent_turn_for_same_user_and_session():
    redis = FakeRedis()
    lock = SessionExecutionLock(redis, ttl_seconds=180)

    async with lock.hold("s1", 7):
        with pytest.raises(SessionTurnInProgressError, match="当前会话正在处理中"):
            async with lock.hold("s1", 7):
                pass


@pytest.mark.asyncio
async def test_turn_lock_does_not_remove_lock_reacquired_after_expiry():
    redis = FakeRedis()
    lock = SessionExecutionLock(redis, ttl_seconds=180)
    key = "vs:lock:turn:7:s1"

    async with lock.hold("s1", 7):
        redis.data[key] = "new-owner-token"

    assert redis.data[key] == "new-owner-token"
