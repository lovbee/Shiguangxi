"""用可解释规则判断当前会话情绪。"""

import re


class SessionMoodDetector:
    """识别急躁、负面、正面、犹豫和中性五种状态。"""

    impatient = re.compile(r"(算了|不要|别说了|快点|到底|跳过)")
    positive = re.compile(r"(好的|可以|不错|挺好|行|ok)", re.IGNORECASE)
    negative = re.compile(r"(贵|太贵|不喜欢|丑|不行|不对)")

    async def detect(self, current_utterance: str, recent_turns: list[dict]) -> str:
        """优先判断当前话术；连续被提问两轮时推断为犹豫。"""
        if self.impatient.search(current_utterance or ""):
            return "impatient"
        if self.negative.search(current_utterance or ""):
            return "negative"
        if self.positive.search(current_utterance or ""):
            return "positive"
        # recent_turns 来自 Checkpoint 的最终对话，不统计 handoff ToolMessage。
        ask_turns = [
            turn
            for turn in recent_turns[-4:]
            if turn.get("role") in {"ASSISTANT", "TURN"}
            and str(turn.get("assistant_text") or turn.get("text") or "").rstrip().endswith("？")
        ]
        return "hesitant" if len(ask_turns) >= 2 else "neutral"
