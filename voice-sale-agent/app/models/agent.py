"""跨 Agent 传递的轻量错误协议。"""

from typing import TypedDict


class AgentError(TypedDict):
    """可降级错误的固定结构。

    ``agent`` 标识来源，``code`` 供日志和前端判断，``recoverable`` 表示本轮
    是否仍能给用户一个有用回复。TypedDict 只做静态类型描述，不创建对象。
    """

    agent: str
    code: str
    recoverable: bool
