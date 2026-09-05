"""多处业务共用的简短中文确认/否定规则。"""

import re

COMMON_CONFIRMERS = {"嗯", "好", "好的", "对", "是", "行", "可以", "继续", "下一个", "再来", "换一个"}


def is_common_confirmer(utterance: str | None) -> bool:
    """判断是否为最多三字的常见短确认词。

    这里只识别词形，不决定具体意图；调用方必须结合订单阶段或推荐历史。
    """
    if utterance is None:
        return False
    value = re.sub(r"[，。！？,.!?\s]", "", utterance.strip())
    return len(value) <= 3 and value in COMMON_CONFIRMERS


def contains_yes(text: str | None) -> bool:
    """订单确认阶段判断话术是否包含肯定表达。"""
    return bool(text) and any(w in text for w in ["确认", "可以", "就这", "对", "好", "嗯", "下单"])


def contains_no(text: str | None) -> bool:
    """订单确认阶段判断话术是否包含取消表达。"""
    return bool(text) and any(w in text for w in ["不要", "算了", "取消", "再想想", "等下"])
