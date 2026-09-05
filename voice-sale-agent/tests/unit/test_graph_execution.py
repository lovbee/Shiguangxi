"""验证执行入口的 thread_id、interrupt 恢复和 Checkpoint 用户隔离。

Fake Graph 只返回预设 StateSnapshot，因此测试可以专注 ``prepare_graph_turn``
是否生成普通输入或 ``Command(resume=...)``，无需编译真实 Supervisor。
"""

from types import SimpleNamespace

import pytest
from langgraph.types import Command

from app.core.exceptions import SessionAccessError
from app.graph.execution import graph_config, prepare_graph_turn


class SessionRepo:
    """记录 open_if_absent 参数，证明执行前先绑定业务会话。"""

    def __init__(self):
        self.calls = []

    async def open_if_absent(self, session_id, user_id, channel):
        self.calls.append((session_id, user_id, channel))


class Graph:
    """返回调用方提供快照的最小 LangGraph 替身。"""

    def __init__(self, snapshot):
        self.snapshot = snapshot

    async def aget_state(self, config):
        assert config == graph_config("s1")
        return self.snapshot


@pytest.mark.asyncio
async def test_prepare_graph_turn_uses_session_id_as_thread_id():
    repo = SessionRepo()
    graph = Graph(SimpleNamespace(values={}, interrupts=()))
    request = {"session_id": "s1", "user_id": 7, "utterance": "hello", "channel": "HOME_ENTRY"}

    graph_input, config = await prepare_graph_turn(graph, request, SimpleNamespace(session_repo=repo))

    assert graph_input == request
    assert config == {"configurable": {"thread_id": "s1"}}
    assert repo.calls == [("s1", 7, "HOME_ENTRY")]


@pytest.mark.asyncio
async def test_prepare_graph_turn_resumes_interrupt_for_same_user():
    graph = Graph(SimpleNamespace(values={"user_id": 7}, interrupts=(object(),)))
    request = {"session_id": "s1", "user_id": 7, "utterance": "确认", "channel": "HOME_ENTRY"}

    graph_input, _config = await prepare_graph_turn(
        graph,
        request,
        SimpleNamespace(session_repo=SessionRepo()),
    )

    assert isinstance(graph_input, Command)
    assert graph_input.resume["utterance"] == "确认"


@pytest.mark.asyncio
async def test_prepare_graph_turn_rejects_checkpoint_from_another_user():
    graph = Graph(SimpleNamespace(values={"user_id": 8}, interrupts=()))
    request = {"session_id": "s1", "user_id": 7, "utterance": "hello", "channel": "HOME_ENTRY"}

    with pytest.raises(SessionAccessError):
        await prepare_graph_turn(graph, request, SimpleNamespace(session_repo=SessionRepo()))
