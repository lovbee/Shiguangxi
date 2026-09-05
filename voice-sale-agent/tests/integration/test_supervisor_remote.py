"""使用真实数据库、Redis、DashScope 和持久化运行一轮推荐主链。

这是最接近生产调用的后端集成测试：创建独立会话、调用编译后的 Supervisor，
断言推荐和口播，再清理业务表、Redis key 与 Checkpoint，避免污染后续测试。
"""

import uuid

import pytest
from sqlalchemy import delete

from app.agents.registry import build_agent_registry
from app.api.deps import build_deps
from app.core.config import get_settings
from app.graph.checkpoint import postgres_checkpointer
from app.graph.execution import ainvoke_turn
from app.graph.supervisor import build_voice_shopping_supervisor
from app.models.db import SessionState, ShoppingSession
from app.repositories.db import close_db, get_sessionmaker, init_db
from app.repositories.redis import close_redis, get_redis, init_redis


@pytest.mark.integration
async def test_remote_supervisor_returns_recommendations():
    """验证真实外部依赖下能完成意图 -> 推荐 -> 口播。"""
    session_id = f"integration-{uuid.uuid4().hex}"
    user_id = 1
    settings = get_settings().model_copy(update={"perspective_enabled": False})
    init_db(settings)
    await init_redis(settings)
    redis = get_redis()

    try:
        async with postgres_checkpointer(settings) as checkpointer:
            graph = build_voice_shopping_supervisor(checkpointer=checkpointer)
            agents = build_agent_registry(settings, redis)
            maker = get_sessionmaker()
            try:
                async with maker() as db:
                    context = build_deps(db, agents, settings)
                    result = await ainvoke_turn(
                        graph,
                        {
                            "session_id": session_id,
                            "user_id": user_id,
                            "utterance": "我想买一双1000元以内适合水泥路的跑鞋",
                            "channel": "HOME_ENTRY",
                        },
                        context,
                    )

                    assert result["phase"] == "RECOMMEND"
                    assert result["current_intent"] == "PRODUCT_RECOMMENDATION"
                    assert result["recommendations"]
                    assert result["speech_text"]
            finally:
                await checkpointer.adelete_thread(session_id)
                async with maker() as cleanup_db:
                    await cleanup_db.execute(delete(SessionState).where(SessionState.session_id == session_id))
                    await cleanup_db.execute(delete(ShoppingSession).where(ShoppingSession.id == session_id))
                    await cleanup_db.commit()
                keys = [key async for key in redis.scan_iter(match=f"vs:*:{user_id}:{session_id}*")]
                if keys:
                    await redis.delete(*keys)
    finally:
        await close_redis()
        await close_db()
