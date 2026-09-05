"""DashScope 流式 TTS 的 asyncio 适配器与 Redis 音频缓存。

同一句文本优先读取 24 小时缓存；未命中时把回调式音频帧转成异步字节流，
一边返回浏览器一边收集完整 PCM，完成后以十六进制写入 Redis。
"""

import asyncio
import hashlib
import logging
from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.core.config import Settings

log = logging.getLogger(__name__)


class TtsService:
    """把文本转换为可逐块发送的 16kHz 单声道 PCM。"""

    def __init__(self, redis: Redis, settings: Settings):
        """注入音频缓存和 DashScope TTS 配置。"""
        self.redis = redis
        self.settings = settings

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        """优先返回缓存音频，否则请求供应商并在完成后缓存。"""
        if not text:
            return
        key = "vs:tts:" + hashlib.md5(text.encode("utf-8")).hexdigest()
        cached = await self.redis.get(key)
        if cached:
            yield bytes.fromhex(cached)
            return
        # 必须收集完整帧才能缓存；同时 yield 保证首帧无需等待整段合成结束。
        chunks: list[bytes] = []
        async for chunk in self._synthesize_dashscope(text):
            chunks.append(chunk)
            yield chunk
        if chunks:
            await self.redis.set(key, b"".join(chunks).hex(), ex=86400)

    async def _synthesize_dashscope(self, text: str) -> AsyncIterator[bytes]:
        """桥接 SpeechSynthesizer 回调到 asyncio Queue。"""
        import dashscope
        from dashscope.audio.tts_v2 import (
            AudioFormat,
            ResultCallback,
            SpeechSynthesizer,
        )

        dashscope.api_key = self.settings.dashscope_api_key
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[bytes | Exception | None] = asyncio.Queue()

        class Callback(ResultCallback):
            """在 SDK 线程中接收音频/完成/错误事件。"""

            def on_event(self, result):  # type: ignore[no-untyped-def]
                """提取非空音频帧并线程安全地送入主事件循环。"""
                try:
                    frame = result.get_audio_frame()
                    if frame is not None and len(frame) > 0:
                        loop.call_soon_threadsafe(queue.put_nowait, bytes(frame))
                except Exception as exc:  # noqa: BLE001  # pragma: no cover - SDK callback path
                    loop.call_soon_threadsafe(queue.put_nowait, exc)

            def on_complete(self):  # type: ignore[no-untyped-def]
                """用 ``None`` 标记音频流正常结束。"""
                loop.call_soon_threadsafe(queue.put_nowait, None)

            def on_error(self, message):  # type: ignore[no-untyped-def]
                """把 SDK 错误作为异常事件交给消费端。"""
                loop.call_soon_threadsafe(queue.put_nowait, RuntimeError(str(message)))

        fmt = getattr(AudioFormat, "PCM_16000HZ_MONO_16BIT", None) or "pcm_16000hz_mono_16bit"
        synthesizer = SpeechSynthesizer(
            model=self.settings.tts_model,
            voice=self.settings.tts_voice,
            format=fmt,
            callback=Callback(),
        )

        async def produce() -> None:
            """在线程中执行同步 synthesizer.call。"""
            try:
                await asyncio.to_thread(synthesizer.call, text)
            except Exception as exc:  # noqa: BLE001 - SDK errors must be forwarded through the audio queue
                await queue.put(exc)

        producer = asyncio.create_task(produce())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                if isinstance(event, Exception):
                    raise event
                yield event
        finally:
            # 浏览器断连或消费端异常时停止等待生产任务。
            producer.cancel()
