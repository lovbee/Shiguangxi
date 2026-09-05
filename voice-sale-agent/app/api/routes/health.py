"""基础健康检查接口。"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.redis import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """验证 PostgreSQL 和 Redis 可用。

    这不是全链路探针：它不会调用 DashScope，也不会检查 pgvector 查询质量。
    """
    await db.execute(text("SELECT 1"))
    pong = await get_redis().ping()
    return {"status": "ok", "db": "ok", "redis": bool(pong)}
