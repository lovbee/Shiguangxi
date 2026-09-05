"""验证模型 JSON 容错工具能处理代码围栏及前后解释文字。"""

from app.agents.json_utils import extract_json_array, extract_json_object


def test_extract_json_object_from_fence():
    assert extract_json_object('```json\n{"a":1}\n```') == {"a": 1}


def test_extract_json_array_from_text():
    assert extract_json_array('prefix [{"a":1}] suffix') == [{"a": 1}]
