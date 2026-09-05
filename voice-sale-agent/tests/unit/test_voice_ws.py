"""验证 WebSocket 音频结束控制协议和队列收尾。

重点防止普通文本/非法 JSON 被误当成 audio_end，以及结束消息后的 PCM 仍被
送入 ASR。FakeWebSocket 用预设消息序列替代真实网络连接。
"""

import asyncio

import pytest

from app.api.routes.voice_ws import is_audio_end_message, receive_audio


class FakeWebSocket:
    """按顺序返回预设帧的最小 WebSocket 替身。"""

    def __init__(self, messages):
        self.messages = list(messages)
        self.receive_count = 0

    async def receive(self):
        message = self.messages.pop(0)
        self.receive_count += 1
        return message


def test_audio_end_control_message_is_strictly_parsed():
    assert is_audio_end_message({"text": '{"type":"audio_end"}'}) is True
    assert is_audio_end_message({"text": "audio_end"}) is False
    assert is_audio_end_message({"bytes": b"audio_end"}) is False


@pytest.mark.asyncio
async def test_receive_audio_stops_at_audio_end_message():
    websocket = FakeWebSocket(
        [
            {"type": "websocket.receive", "bytes": b"pcm"},
            {"type": "websocket.receive", "text": '{"type":"audio_end"}'},
            {"type": "websocket.receive", "bytes": b"late-pcm"},
        ]
    )
    audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    await receive_audio(websocket, audio_queue)

    assert await audio_queue.get() == b"pcm"
    assert await audio_queue.get() is None
    assert audio_queue.empty()
    assert websocket.receive_count == 2
