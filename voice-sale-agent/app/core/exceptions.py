"""项目级异常类型。

自定义类型让上层能够区分“业务拒绝”和“系统崩溃”。当前会话越权已接入
FastAPI 403 处理器；LLM 与订单异常类型为后续统一错误处理预留。
"""

class AppError(Exception):
    """所有可识别应用异常的基类。"""


class LlmOutputError(AppError):
    """大模型输出无法解析或不符合结构协议。"""


class OrderError(AppError):
    """订单预览、确认或库存处理中的业务错误。"""


class SessionAccessError(AppError):
    """会话不存在，或当前登录用户不是该会话所有者。"""


class SessionTurnInProgressError(AppError):
    """同一用户会话已有 Agent 轮次正在执行。"""
