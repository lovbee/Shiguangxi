"""验证中文/英文句末标点会把口播切成适合字幕和 TTS 的片段。"""

from app.services.sentence_aggregator import split_sentences


def test_split_sentences():
    assert split_sentences("你好。再见！") == ["你好。", "再见！"]
