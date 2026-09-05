"""HTTP 与 WebSocket 共用的 Supervisor 调用入口。

这里集中设置稳定 thread_id、校验会话/Checkpoint 所有者，并把订单 interrupt
自动转换成 ``Command(resume=...)``，避免不同 API 各自实现一套恢复逻辑。
"""

from collections.abc import AsyncIterator
from typing import Any

from langgraph.types import Command

from app.core.exceptions import SessionAccessError
from app.graph.state import VoiceShoppingInput
from app.graph.supervisor import SupervisorDeps


def graph_config(session_id: str) -> dict[str, dict[str, str]]:
    """把业务 session_id 固定映射成 LangGraph thread_id。"""
    return {"configurable": {"thread_id": session_id}}


async def prepare_graph_turn(
    graph,
    request: VoiceShoppingInput,
    context: SupervisorDeps,
) -> tuple[VoiceShoppingInput | Command, dict[str, dict[str, str]]]:
    """在执行一轮前校验所有权，并判断是新输入还是恢复 interrupt。

    返回二元组：传给图的 Input/Command，以及带 thread_id 的 config。
    """
    session_id = request["session_id"]
    user_id = int(request["user_id"])
    await context.session_repo.open_if_absent(
        session_id,
        user_id,
        request.get("channel") or "HOME_ENTRY",
    )
    config = graph_config(session_id)
    snapshot = await graph.aget_state(config)
    # 即使业务 session 表校验通过，也要防止旧 Checkpoint 被另一用户复用。
    checkpoint_user_id = snapshot.values.get("user_id") if snapshot.values else None
    if checkpoint_user_id is not None and int(checkpoint_user_id) != user_id:
        raise SessionAccessError("Checkpoint does not belong to the current user")
    if snapshot.interrupts:
        # interrupt 已保存暂停节点；resume 只提交用户决定，不重新从 START 执行。
        return (
            Command(
                resume={
                    "session_id": session_id,
                    "user_id": user_id,
                    "utterance": request.get("utterance") or "",
                }
            ),
            config,
        )
    return request, config


async def ainvoke_turn(graph, request: VoiceShoppingInput, context: SupervisorDeps) -> dict[str, Any]:
    """完整执行一轮并一次返回最终状态，供文本接口使用。"""
    graph_input, config = await prepare_graph_turn(graph, request, context)
    return await graph.ainvoke(
        graph_input,
        config=config,
        context=context,
        durability="sync",
    )


async def astream_turn(
    graph,
    request: VoiceShoppingInput,
    context: SupervisorDeps,
) -> AsyncIterator[dict[str, Any]]:
    """按节点补丁流式返回执行进展，供 WebSocket 尽早推送商品。"""
    graph_input, config = await prepare_graph_turn(graph, request, context)
    async for update in graph.astream(
        graph_input,
        config=config,
        context=context,
        stream_mode="updates",
        durability="sync",
    ):
        yield update
