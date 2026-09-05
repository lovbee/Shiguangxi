"""验证会话所有权和 Redis key 的用户隔离。

即使攻击者猜到别人的 session_id，也不能复用数据库会话；不同用户生成的
scope/state key 也必须不同，防止缓存层串数据。
"""

from types import SimpleNamespace

import pytest

from app.core.exceptions import SessionAccessError
from app.models.db import ShoppingSession
from app.repositories.session import SessionRepository
from app.services.session_keys import session_scope_key
from app.services.session_state import SessionStateService


class FakeDb:
    """只实现 SessionRepository 测试需要的 ``get`` 方法。"""

    def __init__(self, session):
        self.session = session

    async def get(self, model, _key):
        return self.session if model is ShoppingSession else None


@pytest.mark.asyncio
async def test_existing_session_rejects_another_user():
    repository = SessionRepository(FakeDb(SimpleNamespace(user_id=7)))

    with pytest.raises(SessionAccessError):
        await repository.open_if_absent("shared-session", 8)


def test_user_scoped_session_keys_do_not_collide():
    assert session_scope_key("session", 1) != session_scope_key("session", 2)
    service = SessionStateService(
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(session_ttl_seconds=60),
    )
    assert service.key("session", 1) != service.key("session", 2)
