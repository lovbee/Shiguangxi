"""使用真实 PostgreSQL 验证 LangGraph Checkpointer 的完整往返。

测试创建唯一 thread，写入一个最小 StateGraph，读取快照后删除测试线程，
用于发现连接驱动、表初始化、序列化和 thread_id 配置问题。
"""

import uuid
from typing import TypedDict

import pytest
from langgraph.graph import END, START, StateGraph

from app.core.config import get_settings
from app.graph.checkpoint import postgres_checkpointer


class CheckpointState(TypedDict, total=False):
    """集成测试使用的最小图状态。"""

    value: int


@pytest.mark.integration
async def test_postgres_checkpointer_round_trip():
    """真实执行、读取并清理一个 Checkpoint。"""
    thread_id = f"integration-{uuid.uuid4().hex}"
    config = {"configurable": {"thread_id": thread_id}}

    async def increment(state: CheckpointState) -> dict[str, int]:
        return {"value": int(state.get("value", 0)) + 1}

    async with postgres_checkpointer(get_settings()) as checkpointer:
        builder = StateGraph(CheckpointState)
        builder.add_node("increment", increment)
        builder.add_edge(START, "increment")
        builder.add_edge("increment", END)
        graph = builder.compile(checkpointer=checkpointer)

        result = await graph.ainvoke({"value": 1}, config=config, durability="sync")
        snapshot = await graph.aget_state(config)

        assert result["value"] == 2
        assert snapshot.values["value"] == 2
        await checkpointer.adelete_thread(thread_id)
