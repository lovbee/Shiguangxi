"""基于 LangGraph messages 的有界短期对话记忆。

短期消息由 PostgresSaver 随图状态持久化，不再放 Redis List。这里负责忽略
handoff 工具消息、重建最近用户/助手轮次，并用 RemoveMessage 控制窗口大小。
"""

import time
import uuid
from typing import Any

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, RemoveMessage


def recent_turns(messages: list[AnyMessage], limit: int) -> list[dict[str, Any]]:
    """从消息轨迹中提取最近 ``limit`` 轮真实用户/最终助手对话。

    带 tool_calls 的 AIMessage 是节点交接，不是给用户说的话，因此主动跳过。
    """
    turns: list[dict[str, Any]] = []
    user_text: str | None = None
    for message in messages:
        if isinstance(message, HumanMessage):
            user_text = str(message.content)
            continue
        if not isinstance(message, AIMessage) or message.tool_calls or not user_text:
            continue
        assistant_text = str(message.content)
        turns.append(
            {
                "role": "TURN",
                "text": f"用户：{user_text} / 助手：{assistant_text}",
                "assistant_text": assistant_text,
            }
        )
        user_text = None
    return turns[-limit:]


def turn_messages(user_utterance: str, assistant_text: str) -> list[AnyMessage]:
    """为本轮用户和助手消息生成唯一 ID，便于后续精确删除。"""
    turn_id = uuid.uuid4().hex
    return [
        HumanMessage(content=user_utterance, id=f"user-{turn_id}"),
        AIMessage(content=assistant_text, id=f"assistant-{turn_id}"),
    ]


def bounded_message_update(
    current: list[AnyMessage],
    new: list[AnyMessage],
    max_history_turns: int,
) -> list[AnyMessage]:
    """返回旧消息删除指令加新消息，限制 Checkpoint 轨迹增长。

    每轮除两条真实消息外还有多个 handoff 消息，因此容量按每轮最多八条估算，
    并至少保留 16 条，避免很小配置导致上下文立即清空。
    """
    max_messages = max(max_history_turns * 8, 16)
    overflow = max(0, len(current) + len(new) - max_messages)
    removals = [RemoveMessage(id=message.id) for message in current[:overflow] if message.id]
    return [*removals, *new]


def now_millis() -> int:
    """返回 Unix 毫秒时间戳，写入长期记忆元数据。"""
    return int(time.time() * 1000)
