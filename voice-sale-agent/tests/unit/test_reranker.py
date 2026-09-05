"""验证预算锚点规则会优先选择接近预算上限的合格商品。"""

from decimal import Decimal

from app.services.profile_reranker import ProfileReranker


def test_budget_anchor_boosts_near_budget():
    items = [
        {"product_id": 1, "price": Decimal(100), "match_score": 1.0, "attributes": {}},
        {"product_id": 2, "price": Decimal(450), "match_score": 1.0, "attributes": {}},
    ]
    ranked = ProfileReranker().rerank(items, None, {"budget": 500})
    assert ranked[0]["product_id"] == 2
