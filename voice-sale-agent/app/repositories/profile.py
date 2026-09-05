"""用户静态/动态画像读取。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import UserProfileDynamic, UserProfileStatic


class ProfileRepository:
    """把两张画像表合并成推荐重排容易消费的普通字典。"""

    def __init__(self, db: AsyncSession):
        """绑定当前请求的数据库 Session。"""
        self.db = db

    async def load_snapshot(self, user_id: int) -> dict:
        """读取用户画像快照；任一表缺失时相应字段使用空值/空集合。"""
        static = await self.db.get(UserProfileStatic, user_id)
        dynamic = await self.db.get(UserProfileDynamic, user_id)
        return {
            "user_id": user_id,
            "gender": getattr(static, "gender", None),
            "age": getattr(static, "age", None),
            "height_cm": getattr(static, "height_cm", None),
            "weight_kg": getattr(static, "weight_kg", None),
            "skin_type": getattr(static, "skin_type", None),
            "budget_band": getattr(static, "budget_band", None),
            "category_affinity": getattr(dynamic, "category_affinity", None) or {},
            "brand_affinity": getattr(dynamic, "brand_affinity", None) or {},
            "recent_viewed": getattr(dynamic, "recent_viewed", None) or [],
            "recent_purchased": getattr(dynamic, "recent_purchased", None) or [],
            "price_sensitivity": getattr(dynamic, "price_sensitivity", None),
            "avg_order_amount": getattr(dynamic, "avg_order_amount", None),
        }
