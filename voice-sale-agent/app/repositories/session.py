"""会话元数据与精简业务状态的数据访问层。

所有读取和写入都先校验 ``session_id`` 的所有者，防止不同用户猜到相同会话
ID 后读取或覆盖对方状态。
"""

from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import SessionAccessError
from app.models.db import AppUser, SessionState, ShoppingSession


class SessionRepository:
    """创建会话并执行统一的会话所有权校验。"""

    def __init__(self, db: AsyncSession):
        """绑定当前请求的数据库 Session。"""
        self.db = db

    async def open_if_absent(
        self,
        session_id: str,
        user_id: int,
        channel: str = "HOME_ENTRY",
        merchant_id: int | None = None,
        bound_product_id: int | None = None,
    ) -> ShoppingSession:
        """不存在时创建会话，存在时只验证所有者并复用。

        并发创建可能触发唯一键冲突；此时回滚当前事务，再读取并校验最终记录，
        让相同用户的重复请求安全收敛。
        """
        existing = await self.db.get(ShoppingSession, session_id)
        if existing is not None:
            self._ensure_owner(existing, user_id)
            return existing
        await self.ensure_user_projection(user_id)
        session = ShoppingSession(
            id=session_id,
            user_id=user_id,
            merchant_id=merchant_id,
            channel=channel,
            bound_product_id=bound_product_id,
            started_at=datetime.now(),
            locale="zh_cn",
            total_tokens=0,
        )
        self.db.add(session)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            return await self.require_owner(session_id, user_id)
        return session

    async def ensure_user_projection(self, user_id: int) -> AppUser:
        """按 Java 用户 ID 创建最小 Agent 用户投影。

        ``app_user`` 仍是 Agent 数据表外键的目标，但不再是登录或账号的事实来源。
        并发首访时由主键冲突后的重读收敛到同一投影记录。
        """
        user = await self.db.get(AppUser, user_id)
        if user is not None:
            return user
        user = AppUser(id=user_id, username=f"java-user-{user_id}", status="ACTIVE")
        self.db.add(user)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            user = await self.db.get(AppUser, user_id)
            if user is None:
                raise
        return user

    async def require_owner(self, session_id: str, user_id: int) -> ShoppingSession:
        """返回属于指定用户的会话，否则抛出 ``SessionAccessError``。"""
        session = await self.db.get(ShoppingSession, session_id)
        if session is None:
            raise SessionAccessError("Session not found")
        self._ensure_owner(session, user_id)
        return session

    @staticmethod
    def _ensure_owner(session: ShoppingSession, user_id: int) -> None:
        """集中比较所有者，避免不同仓库方法遗漏权限检查。"""
        if int(session.user_id) != int(user_id):
            raise SessionAccessError("Session does not belong to the current user")


class SessionStateRepository:
    """持久化会话阶段、槽位和上次推荐等精简业务状态。"""

    def __init__(self, db: AsyncSession):
        """绑定当前请求的数据库 Session。"""
        self.db = db

    async def get(self, session_id: str, user_id: int) -> SessionState | None:
        """校验所有者后读取状态；新会话可能尚无状态记录。"""
        await SessionRepository(self.db).require_owner(session_id, user_id)
        return await self.db.get(SessionState, session_id)

    async def save(self, data: dict, user_id: int) -> SessionState:
        """以 session_id 执行插入或更新并提交事务。

        这里只保存恢复业务所需字段，完整 LangGraph 状态由 Checkpointer 负责。
        """
        await SessionRepository(self.db).require_owner(data["session_id"], user_id)
        state = await self.db.get(SessionState, data["session_id"])
        if state is None:
            state = SessionState(session_id=data["session_id"])
            self.db.add(state)
        state.phase = data.get("phase") or "INTENT"
        state.current_intent = data.get("current_intent")
        state.slots = data.get("slots") or {}
        state.pending_ask = data.get("pending_ask")
        state.last_recommendations = data.get("last_recommendations")
        state.updated_at = datetime.now()
        await self.db.commit()
        return state
