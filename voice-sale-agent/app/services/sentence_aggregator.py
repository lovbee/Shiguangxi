"""把完整口播或 token 流切成适合字幕/TTS 的句子。"""

import re
from collections.abc import Iterable

SENTENCE_END = re.compile(r"(?<=[。！？!?；;])")


def split_sentences(text: str, max_chars: int = 80) -> list[str]:
    """遇到中英文句末标点或达到长度上限时输出一个片段。"""
    if not text:
        return []
    output: list[str] = []
    buf = ""
    for part in SENTENCE_END.split(text):
        if not part:
            continue
        buf += part
        if SENTENCE_END.search(part[-1:]) or len(buf) >= max_chars:
            output.append(buf)
            buf = ""
    if buf:
        output.append(buf)
    return output


def aggregate_tokens(tokens: Iterable[str], max_chars: int = 80) -> list[str]:
    """先拼接模型增量 token，再复用同一切句规则。"""
    return split_sentences("".join(tokens), max_chars=max_chars)
