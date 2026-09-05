"""验证短期消息过滤、handoff 消息配对和跨会话长期偏好。

FakeStore 把写入保存在内存，既检查 namespace 是否包含 user_id，又检查它没有
session_id，从而保证同一用户的新会话能搜索旧偏好而不同用户不能串数据。
"""

from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.graph.handoff import handoff_command
from app.services.memory import recent_turns
from app.services.semantic_memory import (
    save_semantic_memories,
    search_semantic_memories,
    semantic_memory_namespace,
)


class FakeStore:
    """实现 semantic_memory 所需 aput/asearch 的内存 Store。"""

    def __init__(self):
        self.values = {}
        self.searches = []

    async def aput(self, namespace, key, value):
        self.values[(namespace, key)] = value

    async def asearch(self, namespace, *, query, limit):
        self.searches.append((namespace, query, limit))
        return [
            SimpleNamespace(key=key, value=value, score=0.9)
            for (item_namespace, key), value in self.values.items()
            if item_namespace == namespace
        ][:limit]


def test_recent_turns_ignores_handoff_tool_messages():
    messages = [
        HumanMessage(content="想买跑鞋"),
        AIMessage(content="", tool_calls=[{"name": "transfer", "args": {}, "id": "handoff"}]),
        AIMessage(content="推荐结果"),
    ]

    turns = recent_turns(messages, 3)

    assert turns == [
        {
            "role": "TURN",
            "text": "用户：想买跑鞋 / 助手：推荐结果",
            "assistant_text": "推荐结果",
        }
    ]


def test_handoff_command_carries_tool_messages_and_state_update():
    command = handoff_command(
        source="intent_agent",
        target="recommendation_agent",
        goto="recommend",
        reason="requirements are complete",
        update={"phase": "RECOMMEND"},
    )

    transfer, acknowledgement = command.update["messages"]
    assert command.goto == "recommend"
    assert command.update["phase"] == "RECOMMEND"
    assert transfer.tool_calls[0]["id"] == acknowledgement.tool_call_id
    assert acknowledgement.name == "transfer_to_recommendation_agent"


@pytest.mark.asyncio
async def test_semantic_memory_uses_user_namespace_across_sessions():
    store = FakeStore()
    await save_semantic_memories(store, 7, "thread-a", {"category": "跑鞋", "budget": 800})

    memories = await search_semantic_memories(store, 7, "再推荐一双跑鞋", {}, limit=5)

    assert store.searches == [(semantic_memory_namespace(7), "再推荐一双跑鞋", 5)]
    assert {memory["kind"] for memory in memories} == {"category", "budget"}
    assert all("thread-a" not in part for part in semantic_memory_namespace(7))
    assert not await search_semantic_memories(store, 8, "再推荐一双跑鞋", {})
