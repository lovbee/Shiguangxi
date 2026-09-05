"""使用预算和用户画像对召回候选进行规则重排。"""

from decimal import Decimal


class ProfileReranker:
    """为每个候选复制并计算新分数，不修改调用方原字典。"""

    def rerank(self, candidates: list[dict], profile: dict | None, slots: dict | None) -> list[dict]:
        """计算分数后按降序返回新列表。"""
        scored = []
        for item in candidates:
            clone = dict(item)
            score = self.compute_score(clone, profile, slots or {})
            clone["match_score"] = score
            clone["matchScore"] = score
            scored.append(clone)
        return sorted(scored, key=lambda i: i.get("match_score", 0.0), reverse=True)

    def compute_score(self, item: dict, profile: dict | None, slots: dict) -> float:
        """叠加预算锚点、品牌偏好、价格敏感和避免重复购买等规则。"""
        score = float(item.get("match_score") or item.get("matchScore") or 0.0)
        budget = slots.get("budget")
        price = item.get("price")
        if isinstance(budget, (int, float)) and price is not None:
            price_value = Decimal(str(price))
            budget_value = Decimal(str(budget))
            if budget_value > 0 and price_value <= budget_value:
                ratio = price_value / budget_value
                # 接近但不超过预算的商品更符合“预算锚点”，过低可能偏离需求档次。
                if ratio >= Decimal("0.6"):
                    score += 0.25
                elif ratio >= Decimal("0.4"):
                    score += 0.05
                else:
                    score -= 0.10
        if profile:
            brand = str((item.get("attributes") or {}).get("brand") or "")
            score += float((profile.get("brand_affinity") or {}).get(brand, 0.0)) * 0.2
            avg = profile.get("avg_order_amount")
            if avg and price:
                ratio = Decimal(str(price)) / Decimal(str(avg))
                if ratio > Decimal("1.5"):
                    sensitivity = Decimal(str(profile.get("price_sensitivity") or "0.5"))
                    score -= float(Decimal("0.15") * sensitivity)
            if item.get("product_id") in (profile.get("recent_purchased") or []):
                score -= 0.3
        return score
