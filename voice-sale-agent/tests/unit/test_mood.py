"""验证连续收到助手问句时，会话情绪会从 neutral 变为 hesitant。"""

import pytest

from app.services.mood import SessionMoodDetector


@pytest.mark.asyncio
async def test_turn_memory_questions_produce_hesitant_mood():
    mood = await SessionMoodDetector().detect(
        "我再想想",
        [
            {"role": "TURN", "assistant_text": "预算大概多少？"},
            {"role": "TURN", "assistant_text": "主要在哪种路面跑？"},
        ],
    )

    assert mood == "hesitant"
