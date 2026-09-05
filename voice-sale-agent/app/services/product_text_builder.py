"""构建离线商品 Embedding 使用的自然语言文本。"""

from typing import ClassVar

from app.models.db import Product


class ProductTextBuilder:
    """把商品公共字段和异构 JSON 属性拼成适合语义向量化的文本。"""

    ATTRIBUTE_LABELS: ClassVar[dict[str, str]] = {
        "cushion": "缓震",
        "weight": "重量",
        "gender": "适合性别",
        "waterproof": "防水",
        "finish": "妆感",
        "color": "颜色",
        "movement": "机芯",
        "material": "材质",
    }

    def build(self, product: Product) -> str:
        """生成商品向量文本；卖点重复一次以提高其语义权重。"""
        selling_points = product.selling_points or ""
        brand_category = " ".join(part for part in [product.brand, product.category_l2] if part)
        parts = [
            product.name,
            brand_category,
            selling_points,
            selling_points,
            product.description or "",
            self.humanize(product.attributes or {}),
        ]
        return "。".join(str(part) for part in parts if part)

    @classmethod
    def humanize(cls, attributes: dict) -> str:
        """把 ``cushion=high`` 一类属性转成人类可读的“缓震是high”。"""
        return "，".join(
            f"{cls.ATTRIBUTE_LABELS.get(key, key)}是{value}"
            for key, value in attributes.items()
        )
