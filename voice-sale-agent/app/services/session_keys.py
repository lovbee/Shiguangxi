"""集中生成包含用户维度的 Redis 会话 key。"""

def session_scope_key(session_id: str, user_id: int) -> str:
    """返回会话检索范围 key，避免不同用户复用 session_id 时碰撞。"""
    return f"vs:scope:{user_id}:{session_id}"
