"""读取由 Gateway/Java 门面注入的用户身份。

Python 服务只部署在内部网络，Gateway 会在完成 Sa-Token 校验后删除客户端
伪造的 ``X-Agent-*`` 请求头，并写入本模块读取的用户 ID。本服务不解析或签发
面向浏览器的令牌；一旦服务需要对公网开放，必须重新增加服务端认证边界。
"""

from collections.abc import Mapping

from fastapi import HTTPException, status

GATEWAY_USER_ID_HEADER = "X-Agent-User-Id"


def parse_gateway_user_id(value: str | None) -> int:
    """验证 Gateway 用户头为正整数，缺失或异常值统一视为未认证。"""
    if value is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing gateway user identity")
    try:
        user_id = int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid gateway user identity") from exc
    if user_id <= 0 or str(user_id) != value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid gateway user identity")
    return user_id


def user_id_from_gateway_headers(headers: Mapping[str, str]) -> int:
    """从 HTTP 或 WebSocket 握手头中获取已由上游认证的用户 ID。"""
    return parse_gateway_user_id(headers.get(GATEWAY_USER_ID_HEADER))
