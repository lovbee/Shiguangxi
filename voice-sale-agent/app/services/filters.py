"""根据受控槽位和会话范围构建参数化 SQL 过滤条件。

``clause`` 只由服务器端固定模板拼接，用户值全部进入 ``params``，从源头避免
把自然语言直接当 SQL。向量检索和关键词降级共用同一过滤结果。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SqlFilter:
    """一段不含 WHERE 的 SQL 条件及其绑定参数。"""

    clause: str = ""
    params: dict[str, Any] = field(default_factory=dict)


def merge_filters(*filters: SqlFilter) -> SqlFilter:
    """用 AND 合并非空过滤器，并汇总参数字典。"""
    clauses = [f.clause for f in filters if f.clause]
    params: dict[str, Any] = {}
    for f in filters:
        params.update(f.params)
    return SqlFilter(" AND ".join(clauses), params)


class SqlFilterBuilder:
    """把 Intent slots 转为商品字段白名单过滤。"""

    @staticmethod
    def from_slots(slots: dict[str, Any] | None) -> SqlFilter:
        """构造品类、价格、性别、品牌和排除商品条件。"""
        slots = slots or {}
        clauses: list[str] = []
        params: dict[str, Any] = {}
        if slots.get("category"):
            clauses.append("category_l2 = :category")
            params["category"] = str(slots["category"])
        if isinstance(slots.get("budget"), (int, float)):
            clauses.append("price <= :budget")
            params["budget"] = slots["budget"]
        if isinstance(slots.get("priceMin"), (int, float)):
            clauses.append("price >= :price_min")
            params["price_min"] = slots["priceMin"]
        if slots.get("gender"):
            clauses.append("attributes->>'gender' IN (:gender, 'unisex')")
            params["gender"] = str(slots["gender"])
        if slots.get("brand"):
            clauses.append("brand = :brand")
            params["brand"] = str(slots["brand"])
        exclude = slots.get("excludeProductIds") or []
        if exclude:
            # 为每个 ID 生成独立参数名，不能把列表字符串直接拼入 SQL。
            names = []
            for idx, value in enumerate(exclude):
                key = f"exclude_id_{idx}"
                names.append(f":{key}")
                params[key] = int(value)
            clauses.append("id NOT IN (" + ", ".join(names) + ")")
        return SqlFilter(" AND ".join(clauses), params)

    @staticmethod
    def running_shoe_filter(slots: dict[str, Any] | None) -> SqlFilter:
        """把跑步路面场景映射到缓震/地形商品属性。"""
        scenario = (slots or {}).get("scenario")
        if scenario == "水泥路":
            return SqlFilter("attributes->>'cushion' IN ('high','medium') AND (attributes->>'terrain' IS NULL OR attributes->>'terrain' IN ('road'))")
        if scenario == "塑胶跑道":
            return SqlFilter("attributes->>'cushion' IN ('medium','low') AND (attributes->>'terrain' IS NULL OR attributes->>'terrain' IN ('road','track'))")
        if scenario == "越野":
            return SqlFilter("attributes->>'cushion' = 'high' AND attributes->>'terrain' = 'trail'")
        return SqlFilter()


class ScopeFilterBuilder:
    """把会话允许的商家 ID 转换成强制过滤条件。"""

    @staticmethod
    def build(scope: dict | None) -> SqlFilter:
        """无商家限制时返回空过滤器，有限制时生成参数化 IN。"""
        allowed = (scope or {}).get("allowedMerchantIds") or (scope or {}).get("allowed_merchant_ids")
        if not allowed:
            return SqlFilter()
        names = []
        params: dict[str, Any] = {}
        for idx, value in enumerate(allowed):
            key = f"merchant_id_{idx}"
            names.append(f":{key}")
            params[key] = int(value)
        return SqlFilter("merchant_id IN (" + ", ".join(names) + ")", params)
