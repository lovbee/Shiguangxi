"""构造可观测的 Agent/节点交接命令。

除了 ``Command.goto``，每次交接还写入配对的 AI tool call 与 ToolMessage。
这样 Checkpoint/Trace 能看见“谁把任务交给谁、为什么”，同时消息协议符合
LangChain 对 tool_call_id 一一配对的要求。
"""

import json
import uuid
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import Command


def handoff_command(
    *,
    source: str,
    target: str,
    goto: str,
    reason: str,
    update: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> Command:
    """返回同时携带状态补丁、目标节点和交接消息的 Command。

    ``payload`` 只用于可观测摘要，真正写入父状态的内容必须放进 ``update``。
    """
    tool_call_id = f"handoff-{uuid.uuid4().hex}"
    tool_name = f"transfer_to_{target}"
    transfer = AIMessage(
        content="",
        name=source,
        tool_calls=[
            {
                "name": tool_name,
                "args": {"reason": reason},
                "id": tool_call_id,
                "type": "tool_call",
            }
        ],
    )
    acknowledgement = ToolMessage(
        content=json.dumps(
            {"from": source, "to": target, "reason": reason, "payload": payload or {}},
            ensure_ascii=False,
            default=str,
        ),
        name=tool_name,
        tool_call_id=tool_call_id,
    )
    # 复制字典而不是原地修改调用方对象，避免复用补丁时出现隐藏副作用。
    patch = dict(update or {})
    patch["messages"] = [transfer, acknowledgement]
    return Command(update=patch, goto=goto)
