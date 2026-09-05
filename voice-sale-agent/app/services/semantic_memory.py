"""LangGraph Store 中的跨会话用户偏好记忆。

只保存品类、预算、场景、品牌和适用人群等稳定结构化槽位，不永久保存完整
用户原话。namespace 包含 user_id 但不含 session_id，因此新会话也能召回。
"""

import hashlib
import json
from typing import Any

from app.services.memory import now_millis

MEMORY_NAMESPACE_ROOT = ("voice-shopping", "users")
MEMORY_FIELDS = {
    "category": "商品品类",
    "budget": "预算",
    "scenario": "使用场景",
    "brand": "品牌",
    "gender": "适用人群",
}


def semantic_memory_namespace(user_id: int) -> tuple[str, ...]:
    """返回严格按用户隔离的 preference namespace。"""
    return (*MEMORY_NAMESPACE_ROOT, str(user_id), "preferences")


def semantic_memory_query(utterance: str, slots: dict[str, Any]) -> str:
    """把当前话术和已有槽位拼成 Store 语义搜索查询。"""
    slot_text = " ".join(str(slots.get(field)) for field in MEMORY_FIELDS if slots.get(field) is not None)
    return " ".join(part for part in (utterance.strip(), slot_text) if part)


async def search_semantic_memories(
    store: Any,
    user_id: int,
    utterance: str,
    slots: dict[str, Any],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """语义召回用户偏好，并把 Store Item 转成普通字典。"""
    if store is None:
        return []
    query = semantic_memory_query(utterance, slots)
    if not query:
        return []
    items = await store.asearch(semantic_memory_namespace(user_id), query=query, limit=limit)
    return [
        {
            "key": item.key,
            "content": item.value.get("content", ""),
            "kind": item.value.get("kind"),
            "value": item.value.get("value"),
            "score": item.score,
        }
        for item in items
    ]


async def save_semantic_memories(
    store: Any,
    user_id: int,
    session_id: str,
    slots: dict[str, Any],
) -> int:
    """把非空稳定槽位逐项写入 Store，返回写入数量。

    稳定 key 让同一品类/字段的新值覆盖旧值；品类本身跨品类共享一个身份，
    其他字段以 ``category:field`` 区分，例如跑鞋预算与手表预算互不覆盖。
    """
    if store is None:
        return 0
    namespace = semantic_memory_namespace(user_id)
    category = str(slots.get("category") or "general")
    saved = 0
    for field, label in MEMORY_FIELDS.items():
        value = slots.get(field)
        if value is None or value == "":
            continue
        identity = f"{value}" if field == "category" else f"{category}:{field}"
        # Store key 使用固定长度哈希，避免中文/特殊字符影响底层键格式。
        key = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        await store.aput(
            namespace,
            key,
            {
                "content": f"用户的{label}偏好是{serialized}",
                "kind": field,
                "value": value,
                "source_session_id": session_id,
                "updated_at": now_millis(),
            },
        )
        saved += 1
    return saved
