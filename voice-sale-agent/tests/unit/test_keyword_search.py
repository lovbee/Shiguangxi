"""验证关键词降级的分词、SQL 参数化和结构化过滤保留。

其中恶意文本用例确保用户输入只出现在参数字典，不会进入 SQL 源码。
"""

from app.services.keyword_search import build_keyword_search_sql, extract_keyword_tokens


def test_extract_keyword_tokens_keeps_product_terms():
    tokens = extract_keyword_tokens("我想要一双缓震跑鞋")

    assert "跑鞋" in tokens
    assert "缓震" in tokens
    assert "预算" not in extract_keyword_tokens("预算 500 以内")


def test_keyword_sql_parameterizes_user_terms():
    sql, params = build_keyword_search_sql("跑鞋'; DROP TABLE product; --", "", {}, 5)

    assert "DROP TABLE" not in sql
    assert ":keyword_0" in sql
    assert params["keyword_limit"] == 5
    assert all("DROP TABLE" not in str(value) for value in params.values())


def test_keyword_sql_preserves_structured_filters():
    sql, params = build_keyword_search_sql("跑鞋", "category_l2 = :category", {"category": "跑鞋"}, 3)

    assert "category_l2 = :category" in sql
    assert params["category"] == "跑鞋"
    assert params["keyword_limit"] == 3
