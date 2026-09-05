"""验证商品向量文本的字段、卖点权重和属性中文化。

测试使用 SimpleNamespace 模拟 ORM 商品，因为这里只关心纯文本构建逻辑。
"""

from types import SimpleNamespace

from app.services.product_text_builder import ProductTextBuilder


def test_product_text_builder_matches_java_weighting_and_humanized_attributes():
    product = SimpleNamespace(
        name="Pegasus 40",
        brand="Nike",
        category_l2="跑鞋",
        selling_points="缓震强",
        description="适合日常慢跑",
        attributes={"cushion": "high", "gender": "unisex", "terrain": "road"},
    )

    value = ProductTextBuilder().build(product)

    assert "Nike 跑鞋" in value
    assert value.count("缓震强") == 2
    assert "缓震是high" in value
    assert "适合性别是unisex" in value
    assert "terrain是road" in value
