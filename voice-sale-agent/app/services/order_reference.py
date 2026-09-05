"""把“第几款”解析为上次推荐列表中的商品 ID。"""

import re

ORDINAL = re.compile(r"第?([一二三四五1-5])款?")


def resolve_order_reference(state: dict, utterance: str) -> int | None:
    """解析中文/数字序号及开头、最后、中间等相对位置。

    只会从 ``last_recommendations`` 选择，不能让用户借此下单未推荐商品。
    当前尚不支持按商品名或 SKU 匹配。
    """
    last = state.get("last_recommendations") or []
    if not last:
        return None
    match = ORDINAL.search(utterance or "")
    if match:
        idx = ordinal_to_index(match.group(1))
        if 0 <= idx < len(last):
            return int(last[idx])
    if "第一" in utterance or "开头" in utterance:
        return int(last[0])
    if "最后" in utterance:
        return int(last[-1])
    if "中间" in utterance:
        return int(last[len(last) // 2])
    return None


def ordinal_to_index(value: str) -> int:
    """把一到五的中文或数字表示转换为从 0 开始的列表下标。"""
    return {"一": 0, "1": 0, "二": 1, "2": 1, "三": 2, "3": 2, "四": 3, "4": 3, "五": 4, "5": 4}.get(value, -1)
