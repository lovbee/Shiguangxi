"""验证槽位和会话商家范围会生成正确的参数化 SQL 条件。

测试关注条件模板和参数分离，防止未来重构把用户值直接拼进 SQL。
"""

from app.services.filters import ScopeFilterBuilder, SqlFilterBuilder


def test_filter_from_slots():
    f = SqlFilterBuilder.from_slots({"category": "跑鞋", "budget": 500, "brand": "Asics"})
    assert "category_l2" in f.clause
    assert f.params["budget"] == 500


def test_scope_filter():
    f = ScopeFilterBuilder.build({"allowedMerchantIds": [1, 2]})
    assert "merchant_id IN" in f.clause
    assert f.params["merchant_id_0"] == 1
