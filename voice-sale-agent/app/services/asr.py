"""DashScope 实时 ASR 的 asyncio 适配器。

浏览器音频来自异步 Queue，DashScope Recognition 却是同步/回调式 SDK。
本模块用工作线程发送音频，用 ``loop.call_soon_threadsafe`` 把 SDK 回调安全地
送回事件循环，并在 stop 后限时等待迟到的最终句和完成事件。
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import suppress
from dataclasses import dataclass

from app.core.config import Settings

log = logging.getLogger(__name__)
ASR_COMPLETE_TIMEOUT_SECONDS = 3.0
_STOP_FINISHED = object()


@dataclass
class AsrResult:
    """一段识别文本及其是否为完整句。"""

    text: str
    is_final: bool


class AsrService:
    """把音频 Queue 转换成可 ``async for`` 消费的识别结果流。"""

    def __init__(self, settings: Settings):
        """保存 ASR 模型和 DashScope 凭据配置。"""
        self.settings = settings

    async def recognize(self, audio_queue: asyncio.Queue[bytes | None]) -> AsyncIterator[AsrResult]:
        """公开识别入口；当前只实现 DashScope Provider。"""
        async for result in self._recognize_dashscope(audio_queue):
            yield result

    async def _recognize_dashscope(self, audio_queue: asyncio.Queue[bytes | None]) -> AsyncIterator[AsrResult]:
        """桥接 DashScope 回调、音频发送协程和异步结果迭代器。"""
        import dashscope
        from dashscope.audio.asr import (
            Recognition,
            RecognitionCallback,
            RecognitionResult,
        )

        dashscope.api_key = self.settings.dashscope_api_key
        loop = asyncio.get_running_loop()
        result_queue: asyncio.Queue[AsrResult | Exception | object | None] = asyncio.Queue()

        class Callback(RecognitionCallback):
            """运行在 SDK 线程中的回调，不能直接操作 asyncio Queue。"""

            def on_event(self, result):  # type: ignore[no-untyped-def]
                """把中间/最终识别句安全投递回主事件循环。"""
                try:
                    sentence = result.get_sentence()
                    text = sentence.get("text", "") if isinstance(sentence, dict) else getattr(sentence, "text", "")
                    is_final = RecognitionResult.is_sentence_end(sentence)
                    loop.call_soon_threadsafe(result_queue.put_nowait, AsrResult(text=text or "", is_final=bool(is_final)))
                except Exception as exc:  # noqa: BLE001 - SDK callback errors must be forwarded to async loop
                    loop.call_soon_threadsafe(result_queue.put_nowait, exc)

            def on_error(self, message):  # type: ignore[no-untyped-def]
                """把 SDK 错误转换成异常事件，由消费端统一抛出。"""
                detail = getattr(message, "message", None) or getattr(message, "text", None) or str(message)
                loop.call_soon_threadsafe(result_queue.put_nowait, RuntimeError(detail))

            def on_complete(self):  # type: ignore[no-untyped-def]
                """用 ``None`` 告知消费端 SDK 已完成全部回调。"""
                loop.call_soon_threadsafe(result_queue.put_nowait, None)

        recognition = Recognition(
            model=self.settings.asr_model,
            format="pcm",
            sample_rate=16000,
            callback=Callback(),
        )
        # start/send/stop 都可能阻塞，不能直接运行在 FastAPI 事件循环线程。
        await asyncio.to_thread(recognition.start)

        stop_finished = asyncio.Event()

        async def sender() -> None:
            """持续把 PCM 帧发给 SDK，收到 None 哨兵后调用 stop。"""
            pending_error: Exception | None = None
            try:
                while True:
                    chunk = await audio_queue.get()
                    if chunk is None:
                        break
                    await asyncio.to_thread(recognition.send_audio_frame, chunk)
            except Exception as exc:  # noqa: BLE001 - SDK errors must be forwarded to async loop
                pending_error = exc
            finally:
                try:
                    await asyncio.to_thread(recognition.stop)
                except Exception as exc:  # noqa: BLE001 - SDK errors must be forwarded to async loop
                    pending_error = pending_error or exc
                stop_finished.set()
                if pending_error is not None:
                    await result_queue.put(pending_error)
                # stop() 返回不代表 on_complete/final 已到，单独哨兵只表示发送结束。
                await result_queue.put(_STOP_FINISHED)

        sender_task = asyncio.create_task(sender())
        try:
            while True:
                try:
                    if stop_finished.is_set():
                        # stop 后若 SDK 漏发 on_complete，最多再等固定时间，避免连接挂死。
                        event = await asyncio.wait_for(result_queue.get(), timeout=ASR_COMPLETE_TIMEOUT_SECONDS)
                    else:
                        event = await result_queue.get()
                except TimeoutError:
                    log.warning("ASR complete callback timed out after recognition.stop(); ending result stream")
                    break
                if event is None:
                    break
                if event is _STOP_FINISHED:
                    continue
                if isinstance(event, Exception):
                    raise event
                yield event
        finally:
            # 消费端异常/取消时也必须回收 sender，防止后台继续读取音频。
            if not sender_task.done():
                sender_task.cancel()
            with suppress(asyncio.CancelledError):
                await sender_task
