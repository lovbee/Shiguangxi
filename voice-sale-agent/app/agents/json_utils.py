"""容错提取大模型返回的 JSON。

模型偶尔会包上 Markdown 代码围栏或解释文字，本模块只负责剥离这些包装；
真正的字段合法性仍由 Pydantic 校验，语法错误也会明确抛出。
"""

import json
import re
from typing import Any


def strip_code_fence(text: str) -> str:
    """去掉开头/结尾的 ```json 或 ```text 代码围栏。"""
    value = text.strip()
    value = re.sub(r"^```(?:json|text)?\s*", "", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"\s*```$", "", value, flags=re.DOTALL)
    return value.strip()


def extract_json_object(text: str) -> dict[str, Any]:
    """截取最外层花括号并解析 JSON 对象。"""
    cleaned = strip_code_fence(text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def extract_json_array(text: str) -> list[Any]:
    """截取最外层方括号并解析 JSON 数组。"""
    cleaned = strip_code_fence(text)
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)
