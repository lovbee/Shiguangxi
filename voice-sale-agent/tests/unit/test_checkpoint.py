"""检查业务 asyncpg URL 能正确转换为 LangGraph psycopg 连接串。

这个小测试可提前发现驱动名或 ``sslmode=disable`` 丢失导致的启动失败。
"""

from types import SimpleNamespace

from app.graph.checkpoint import checkpoint_connection_string


def test_checkpoint_connection_uses_psycopg_and_ssl_setting():
    settings = SimpleNamespace(
        database_url="postgresql+asyncpg://user:pass@localhost:5432/shop",
        database_ssl=False,
    )

    value = checkpoint_connection_string(settings)

    assert value.startswith("postgresql://")
    assert "+asyncpg" not in value
    assert "sslmode=disable" in value
