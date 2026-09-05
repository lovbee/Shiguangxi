"""最终口播的轻量确定性合规清洗。

当前实现只替换绝对化用词并屏蔽演示敏感词，不能代替生产内容审核服务。
放在 Supervisor 公共出口可确保澄清、推荐、闲聊和订单话术都经过它。
"""

from pathlib import Path

ABSOLUTE_REPLACEMENTS = {
    "最好": "比较合适",
    "第一": "常用",
    "保证": "通常",
    "绝对": "基本",
}


class ComplianceChecker:
    """加载敏感词并对用户可见文本执行字符串级清洗。"""

    def __init__(self, sensitive_path: Path | None = None):
        """从指定或默认文件加载非空敏感词列表。"""
        path = sensitive_path or Path(__file__).resolve().parents[1] / "resources" / "compliance" / "sensitive-words.txt"
        self.sensitive_words = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []

    def clean_text(self, text: str | None) -> str:
        """替换绝对化表达，并用等长星号屏蔽敏感词。"""
        if not text:
            return ""
        cleaned = text
        for src, dst in ABSOLUTE_REPLACEMENTS.items():
            cleaned = cleaned.replace(src, dst)
        for word in self.sensitive_words:
            cleaned = cleaned.replace(word, "*" * len(word))
        return cleaned

    def ensure_compliant_state(self, state: dict) -> dict:
        """返回仅包含清洗后 speech_text 的父图状态补丁。"""
        return {"speech_text": self.clean_text(state.get("speech_text"))}
