"""绕过 Agent 的独立商品搜索接口，主要用于验证检索能力。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.core.config import get_settings
from app.models.dto import ProductOut
from app.repositories.product import ProductRepository
from app.repositories.redis import get_redis
from app.services.embedding import EmbeddingService
from app.services.vector_search import ProductVectorService

router = APIRouter(prefix="/internal/v1/search", tags=["internal-search"])


@router.get("", response_model=list[ProductOut], response_model_by_alias=True)
async def search(q: str = Query(...), budget: int | None = None, _user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """按查询文本和可选预算返回前五个商品。

    该接口要求 Gateway 注入用户身份，但不会加载用户画像、商家会话范围或生成推荐理由；
    向量服务失败/零命中时会自动转为参数化关键词检索。
    """
    settings = get_settings()
    vector = ProductVectorService(db, EmbeddingService(get_redis(), settings))
    # extra_filter 只能由服务器端白名单逻辑生成，不能直接接收用户 SQL。
    params = {}
    clause = ""
    if budget is not None:
        clause = "price <= :budget"
        params["budget"] = budget
    ids = await vector.search(q, clause, params, 5)
    return await ProductRepository(db).find_by_ids(ids)
