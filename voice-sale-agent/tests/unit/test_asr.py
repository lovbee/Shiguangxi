"""不连接 DashScope 的 ASR 回调时序单元测试。

通过 monkeypatch 把 ``dashscope.audio.asr`` 替换成可控类，覆盖两个生产风险：
``stop`` 返回后最终句才到达；SDK 永远不发 ``on_complete``。测试确保前者不会
丢字，后者不会让异步迭代器无限挂起。
"""

import asyncio
import sys
import threading
import types
from types import SimpleNamespace

import pytest

from app.services import asr as asr_module
from app.services.asr import AsrService


class _FakeSentenceResult:
    """模拟 DashScope 回调对象，只暴露服务真正读取的方法。"""

    def __init__(self, text: str, is_final: bool):
        self.text = text
        self.is_final = is_final

    def get_sentence(self) -> dict:
        return {"text": self.text, "is_final": self.is_final}


def install_fake_dashscope(monkeypatch: pytest.MonkeyPatch, recognition_cls: type) -> None:
    """把假 SDK 模块安装进 sys.modules，让被测代码的局部 import 命中它。"""
    dashscope = types.ModuleType("dashscope")
    audio = types.ModuleType("dashscope.audio")
    asr = types.ModuleType("dashscope.audio.asr")

    class RecognitionCallback:
        pass

    class RecognitionResult:
        @staticmethod
        def is_sentence_end(sentence: dict) -> bool:
            return bool(sentence.get("is_final"))

    asr.Recognition = recognition_cls
    asr.RecognitionCallback = RecognitionCallback
    asr.RecognitionResult = RecognitionResult
    audio.asr = asr
    dashscope.audio = audio

    monkeypatch.setitem(sys.modules, "dashscope", dashscope)
    monkeypatch.setitem(sys.modules, "dashscope.audio", audio)
    monkeypatch.setitem(sys.modules, "dashscope.audio.asr", asr)


def make_settings() -> SimpleNamespace:
    """构造 ASR 所需的最小配置，避免加载真实 ``.env``。"""
    return SimpleNamespace(dashscope_api_key="test-key", asr_model="test-asr")


@pytest.mark.asyncio
async def test_dashscope_asr_waits_for_final_callback_after_stop(monkeypatch: pytest.MonkeyPatch):
    class Recognition:
        def __init__(self, *, callback, **_kwargs):
            self.callback = callback

        def start(self) -> None:
            pass

        def send_audio_frame(self, _chunk: bytes) -> None:
            pass

        def stop(self) -> None:
            threading.Timer(0.01, self._complete).start()

        def _complete(self) -> None:
            self.callback.on_event(_FakeSentenceResult("我要买一瓶洗发水", True))
            self.callback.on_complete()

    install_fake_dashscope(monkeypatch, Recognition)
    monkeypatch.setattr(asr_module, "ASR_COMPLETE_TIMEOUT_SECONDS", 0.2)
    audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    await audio_queue.put(b"pcm")
    await audio_queue.put(None)

    results = [result async for result in AsrService(make_settings()).recognize(audio_queue)]

    assert results[-1].text == "我要买一瓶洗发水"
    assert results[-1].is_final is True


@pytest.mark.asyncio
async def test_dashscope_asr_ends_when_complete_callback_is_missing(monkeypatch: pytest.MonkeyPatch):
    class Recognition:
        def __init__(self, **_kwargs):
            pass

        def start(self) -> None:
            pass

        def send_audio_frame(self, _chunk: bytes) -> None:
            pass

        def stop(self) -> None:
            pass

    install_fake_dashscope(monkeypatch, Recognition)
    monkeypatch.setattr(asr_module, "ASR_COMPLETE_TIMEOUT_SECONDS", 0.01)
    audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    await audio_queue.put(None)

    results = [result async for result in AsrService(make_settings()).recognize(audio_queue)]

    assert results == []
