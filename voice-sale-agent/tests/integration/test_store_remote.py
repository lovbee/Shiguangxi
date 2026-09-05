"""验证 Postgres Store 的用户级语义记忆能跨会话召回。

写入偏好时记录来源 session，但 namespace 不含 session；随后用另一种自然语言
查询同一用户 namespace，确认 DashScope Embedding 与 Store 向量索引可用。
"""

import uuid

import pytest

from app.core.config import get_settings
from app.graph.checkpoint import postgres_graph_persistence
from app.services.semantic_memory import (
    save_semantic_memories,
    search_semantic_memories,
    semantic_memory_namespace,
)


@pytest.mark.integration
async def test_postgres_store_semantic_memory_crosses_threads():
    """真实写入、语义搜索并清理一条跨线程偏好记忆。"""
    user_id = 900_000_000 + uuid.uuid4().int % 99_999_999
    source_thread = f"integration-source-{uuid.uuid4().hex}"
    namespace = semantic_memory_namespace(user_id)

    async with postgres_graph_persistence(get_settings()) as persistence:
        try:
            await save_semantic_memories(
                persistence.store,
                user_id,
                source_thread,
                {"category": "跑鞋", "budget": 800, "scenario": "水泥路"},
            )

            memories = await search_semantic_memories(
                persistence.store,
                user_id,
                "新会话里继续推荐适合水泥路的跑鞋",
                {},
            )

            assert memories
            assert any(memory["kind"] == "scenario" for memory in memories)
            assert source_thread not in namespace
        finally:
            items = await persistence.store.asearch(namespace, limit=100)
            for item in items:
                await persistence.store.adelete(namespace, item.key)
