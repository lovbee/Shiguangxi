"""从 YAML 读取不同品类的必填槽位规则。"""

from pathlib import Path

import yaml


class ClarifyRuleService:
    """用确定性规则判断推荐前还缺哪些购物条件。"""

    def __init__(self, path: Path | None = None):
        """读取 YAML；测试可传自定义规则文件。"""
        self.path = path or Path(__file__).resolve().parents[1] / "resources" / "clarify" / "required-slots.yml"
        self.rules = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}

    def missing_slots(self, category: str | None, slots: dict) -> list[str]:
        """按 YAML 中的 required 顺序返回空缺字段。

        未知/缺失品类使用 ``default`` 规则；nice_to_have 不会阻止推荐。
        """
        rule = self.rules.get(category) if category else None
        if not rule:
            rule = self.rules.get("default", {})
        ordered = list(rule.get("required", []))
        missing: list[str] = []
        for key in ordered:
            value = slots.get(key)
            if value is None or value == "":
                missing.append(key)
        return missing
