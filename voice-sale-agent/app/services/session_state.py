"""会话业务状态的 PostgreSQL + Redis cache-aside 服务。

数据库 ``session_state`` 是长期事实，Redis 是按 TTL 加速的副本。所有 key 和
Repository 调用都包含 user_id，避免相同 session_id 在不同用户间串数据。
"""

import json

from redis.asyncio import Redis

from app.core.config import Settings
from app.repositories.session import SessionStateRepository


class SessionStateService:
    """加载、保存并同步精简会话状态。"""

    def __init__(self, repo: SessionStateRepository, redis: Redis, settings: Settings):
        """注入数据库 Repository、Redis 缓存和 TTL 配置。"""
        self.repo = repo
        self.redis = redis
        self.settings = settings

    def key(self, session_id: str, user_id: int) -> str:
        """生成用户隔离的状态缓存 key。"""
        return f"vs:session:{user_id}:{session_id}"

    async def load(self, session_id: str, user_id: int) -> dict:
        """优先读 Redis；未命中时读 PostgreSQL并回填缓存。"""
        raw = await self.redis.get(self.key(session_id, user_id))
        if raw:
            return json.loads(raw)
        db_state = await self.repo.get(session_id, user_id)
        if db_state is None:
            # 新会话尚未走到 memory_update 时没有状态行，返回明确初始状态。
            return {"session_id": session_id, "phase": "INTENT", "slots": {}, "last_recommendations": []}
        data = {
            "session_id": db_state.session_id,
            "phase": db_state.phase,
            "current_intent": db_state.current_intent,
            "slots": db_state.slots or {},
            "pending_ask": db_state.pending_ask,
            "last_recommendations": db_state.last_recommendations or [],
        }
        await self._sync(data, user_id)
        return data

    async def save(self, data: dict, user_id: int) -> None:
        """先提交数据库，再同步 Redis；数据库仍是最终事实来源。"""
        await self.repo.save(data, user_id)
        await self._sync(data, user_id)

    async def _sync(self, data: dict, user_id: int) -> None:
        """把可 JSON 化状态写入 Redis，并设置会话 TTL。"""
        await self.redis.set(
            self.key(data["session_id"], user_id),
            json.dumps(data, ensure_ascii=False, default=str),
            ex=self.settings.session_ttl_seconds,
        )
