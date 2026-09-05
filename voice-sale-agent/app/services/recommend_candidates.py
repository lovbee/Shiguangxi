"""把过滤、召回和 ORM 商品恢复组合成统一候选列表。"""

from app.repositories.product import ProductRepository
from app.services.filters import ScopeFilterBuilder, SqlFilterBuilder, merge_filters
from app.services.vector_search import ProductVectorService


class RecommendCandidatesService:
    """Recommendation 工具背后的确定性商品目录服务。"""

    def __init__(self, vector: ProductVectorService, product_repo: ProductRepository):
        """注入召回服务和当前请求的商品 Repository。"""
        self.vector = vector
        self.product_repo = product_repo

    async def fetch_candidates(self, query: str, slots: dict, scope: dict | None, top_n: int = 20) -> list[dict]:
        """按槽位/跑鞋场景/商家范围召回，并转换成内部商品字典。"""
        base_filter = SqlFilterBuilder.from_slots(slots)
        if slots.get("category") == "跑鞋":
            base_filter = merge_filters(base_filter, SqlFilterBuilder.running_shoe_filter(slots))
        final_filter = merge_filters(base_filter, ScopeFilterBuilder.build(scope))
        ids = await self.vector.search(query, final_filter.clause, final_filter.params, top_n)
        if not ids:
            return []
        allowed = (scope or {}).get("allowedMerchantIds") or (scope or {}).get("allowed_merchant_ids")
        # Repository 再检查一次商家范围，避免未来替换召回服务时绕过会话隔离。
        products = await self.product_repo.find_by_ids_with_scope(ids, allowed)
        items: list[dict] = []
        for idx, product in enumerate(products):
            attrs = dict(product.attributes or {})
            if product.brand:
                attrs.setdefault("brand", product.brand)
            attrs.setdefault("category_l2", product.category_l2)
            # 当前向量 SQL 只返回 ID，没有返回真实距离，因此先用名次构造基础分。
            score = 1.0 - idx * 0.03
            items.append(
                {
                    "product_id": product.id,
                    "productId": product.id,
                    "name": product.name,
                    "price": product.price,
                    "reason": None,
                    "match_score": score,
                    "matchScore": score,
                    "attributes": attrs,
                }
            )
        return items
