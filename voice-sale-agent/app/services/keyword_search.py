"""向量检索不可用时的参数化关键词降级 SQL。

中文没有空格分词，本模块删除常见购物噪声后保留短词和二元词；名称、品牌、
品类的命中权重高于描述和 JSON 属性。用户 token 始终作为绑定参数传给 SQL。
"""

import re
from typing import Any

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,}|[\u4e00-\u9fff]+")
_NOISE_PHRASES = (
    "我想要",
    "我想买",
    "帮我",
    "给我",
    "推荐",
    "一双",
    "一款",
    "适合",
    "预算",
    "以内",
    "左右",
    "有没有",
    "看看",
    "想买",
)
_NOISE_TOKENS = {
    "我",
    "想",
    "要",
    "买",
    "帮",
    "给",
    "一",
    "双",
    "款",
    "的",
    "了",
    "吗",
    "请",
    "在",
    "和",
    "或",
    "再",
    "更",
    "比较",
    "什么",
    "哪款",
    "商品",
    "产品",
}
_PRODUCT_TEXT = (
    "concat_ws(' ', "
    "coalesce(name, ''), coalesce(brand, ''), coalesce(category_l1, ''), "
    "coalesce(category_l2, ''), coalesce(sku_code, ''), "
    "coalesce(description, ''), coalesce(selling_points, ''), "
    "coalesce(attributes::text, ''))"
)


def extract_keyword_tokens(query: str, max_tokens: int = 12) -> list[str]:
    """提取英文词和中文二元词，去重并限制最多 ``max_tokens`` 个。"""
    normalized = query or ""
    for phrase in _NOISE_PHRASES:
        normalized = normalized.replace(phrase, " ")

    tokens: list[str] = []
    seen: set[str] = set()
    for chunk in _TOKEN_RE.findall(normalized):
        if chunk.isascii():
            candidates = [chunk.lower()] if not chunk.isdigit() else []
        else:
            # 长中文串拆成二元词，兼顾简单实现与部分词语命中能力。
            candidates = [chunk[i : i + 2] for i in range(len(chunk) - 1)]
            if len(chunk) <= 4:
                candidates.insert(0, chunk)

        for token in candidates:
            if token in _NOISE_TOKENS or len(token) < 2 or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
            if len(tokens) >= max_tokens:
                return tokens
    return tokens


def build_keyword_search_sql(
    query: str,
    extra_filter: str,
    extra_params: dict[str, Any],
    top_k: int,
) -> tuple[str, dict[str, Any]]:
    """返回可直接交给 SQLAlchemy ``text`` 的 SQL 与参数。

    ``extra_filter`` 必须来自 filters.py 的受控模板；本函数只把用户关键词放进
    ``:keyword_n`` 参数，绝不插入 SQL 源码。
    """
    tokens = extract_keyword_tokens(query)
    params = dict(extra_params)
    params["keyword_limit"] = max(1, int(top_k))

    conditions = ["status = 'ON_SALE'"]
    if extra_filter:
        conditions.append(extra_filter)

    if not tokens:
        # 没有有效词时仍保留结构化过滤，按 ID 给出确定性结果而不是报错。
        sql = (
            "SELECT id FROM product "
            f"WHERE {' AND '.join(conditions)} "
            "ORDER BY id LIMIT :keyword_limit"
        )
        return sql, params

    predicates: list[str] = []
    score_parts: list[str] = []
    for index, token in enumerate(tokens):
        key = f"keyword_{index}"
        params[key] = f"%{token}%"
        predicates.append(f"{_PRODUCT_TEXT} ILIKE :{key}")
        # 不同字段给不同权重，让商品名/品牌命中优先于描述或 JSON 属性。
        score_parts.append(
            "("
            f"CASE WHEN coalesce(name, '') ILIKE :{key} THEN 10 ELSE 0 END + "
            f"CASE WHEN coalesce(brand, '') ILIKE :{key} THEN 8 ELSE 0 END + "
            f"CASE WHEN coalesce(category_l2, '') ILIKE :{key} THEN 7 ELSE 0 END + "
            f"CASE WHEN coalesce(description, '') ILIKE :{key} "
            f"OR coalesce(selling_points, '') ILIKE :{key} THEN 4 ELSE 0 END + "
            f"CASE WHEN coalesce(attributes::text, '') ILIKE :{key} THEN 2 ELSE 0 END"
            ")"
        )

    sql = (
        "SELECT id, "
        + " + ".join(score_parts)
        + " AS keyword_score FROM product "
        f"WHERE {' AND '.join(conditions)} AND ({' OR '.join(predicates)}) "
        "ORDER BY keyword_score DESC, id LIMIT :keyword_limit"
    )
    return sql, params
