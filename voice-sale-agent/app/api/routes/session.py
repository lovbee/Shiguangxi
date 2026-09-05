"""创建会话并确定本会话允许检索的商家范围。"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id, get_db
from app.core.config import get_settings
from app.models.dto import SessionScopeDto, StartSessionRequest
from app.models.enums import Channel
from app.repositories.product import ProductRepository
from app.repositories.redis import get_redis
from app.repositories.session import SessionRepository
from app.services.session_keys import session_scope_key

router = APIRouter(prefix="/internal/v1/sessions", tags=["internal-session"])


@router.post("/start", response_model=SessionScopeDto, response_model_by_alias=True)
async def start_session(req: StartSessionRequest, user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)) -> SessionScopeDto:
    """创建或复用会话，并把入口范围缓存到 Redis。

    商品详情页只能推荐该商品所属商家，商家主页只能推荐指定商家；首页默认
    不限制商家。范围 key 同时包含用户和会话 ID，避免跨用户碰撞。
    """
    allowed = None
    product_repo = ProductRepository(db)
    if req.channel == Channel.PRODUCT_PAGE:
        if req.bound_product_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PRODUCT_PAGE must include boundProductId")
        product = await product_repo.get(req.bound_product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found")
        allowed = [product.merchant_id]
    elif req.channel == Channel.MERCHANT_HOME:
        if req.merchant_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MERCHANT_HOME must include merchantId")
        allowed = [req.merchant_id]
    await SessionRepository(db).open_if_absent(req.session_id, user_id, req.channel.value, req.merchant_id, req.bound_product_id)
    # Redis 中保存的是 JSON，而不是 ORM 对象，便于 Supervisor 快速读取。
    scope = {"userId": user_id, "allowedMerchantIds": allowed, "boundProductId": req.bound_product_id}
    await get_redis().set(
        session_scope_key(req.session_id, user_id),
        json.dumps(scope, ensure_ascii=False),
        ex=get_settings().session_ttl_seconds,
    )
    return SessionScopeDto(userId=user_id, allowedMerchantIds=allowed, boundProductId=req.bound_product_id)
