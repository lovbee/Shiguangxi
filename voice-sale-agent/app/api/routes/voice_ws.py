"""单轮语音导购 WebSocket 协议。

客户端发送 16kHz/16bit/单声道 PCM 字节，结束时发送
``{"type": "audio_end"}``。服务端依次返回 ASR 文本、推荐卡片、字幕、
PCM 音频和 complete 事件。每条连接只处理一个最终句，多轮靠复用 sessionId。
"""

import asyncio
import json
import logging
import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.api.deps import build_deps
from app.core.config import get_settings
from app.core.gateway_identity import user_id_from_gateway_headers
from app.graph.execution import astream_turn
from app.repositories.db import get_sessionmaker
from app.repositories.redis import get_redis
from app.services.asr import AsrService
from app.services.sentence_aggregator import split_sentences
from app.services.session_execution_lock import SessionExecutionLock
from app.services.tts import TtsService

router = APIRouter(tags=["voice"])
log = logging.getLogger(__name__)


async def send_json_or_log(websocket: WebSocket, payload: dict, context: str) -> None:
    """尽力发送 JSON；连接已关闭时只记调试日志，不制造二次异常。"""
    try:
        await websocket.send_json(payload)
    except Exception:
        log.debug("websocket send_json skipped after close: %s", context, exc_info=True)


async def close_or_log(websocket: WebSocket, context: str) -> None:
    """幂等式关闭连接；多个 finally 同时收尾也不会掩盖原始错误。"""
    try:
        await websocket.close()
    except Exception:
        log.debug("websocket close skipped: %s", context, exc_info=True)


def is_audio_end_message(message: dict) -> bool:
    """严格识别客户端音频结束控制消息。

    普通文本、非法 JSON 或仅包含相似字段的对象都不能停止音频流，避免误把
    PCM 传输提前截断。
    """
    text = message.get("text")
    if not text:
        return False
    try:
        payload = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and payload.get("type") == "audio_end"


async def receive_audio(websocket: WebSocket, audio_queue: asyncio.Queue[bytes | None]) -> None:
    """把 WebSocket 二进制帧转交 ASR 队列，结束时放入 ``None`` 哨兵。

    ``finally`` 保证断连、控制消息或异常三种路径都会通知 ASR sender 停止。
    """
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect" or is_audio_end_message(message):
                break
            data = message.get("bytes")
            if data is not None:
                await audio_queue.put(data)
    except WebSocketDisconnect:
        pass
    finally:
        await audio_queue.put(None)


@router.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket, sessionId: str | None = None):
    """建立一轮语音会话并并发运行“接收音频”和“处理识别结果”。"""
    settings = get_settings()
    # Gateway 在握手升级前完成 Sa-Token 校验，并写入可信身份头。
    # 此服务不接受 URL token，也不能信任浏览器自行传入的用户 ID。
    try:
        user_id = user_id_from_gateway_headers(websocket.headers)
    except HTTPException:
        await websocket.close(code=1008)
        return
    session_id = sessionId or f"voice-{uuid.uuid4().hex}"
    await websocket.accept()
    audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=100)
    asr = AsrService(settings)
    tts = TtsService(get_redis(), settings)

    async def process_asr() -> None:
        """转发 ASR 结果，并在第一条有效最终句上启动完整业务图。"""
        saw_asr_result = False
        async for result in asr.recognize(audio_queue):
            saw_asr_result = True
            await websocket.send_json({"type": "asr", "text": result.text, "final": result.is_final})
            if result.is_final and result.text.strip():
                try:
                    # 图执行与 TTS 完成前连接保持打开；任何业务异常转成 error 事件。
                    audio_available = await run_graph_and_stream(websocket, session_id, user_id, result.text, tts)
                    await websocket.send_json({"type": "complete", "audioAvailable": audio_available})
                except Exception as exc:
                    log.exception("voice round failed: session_id=%s user_id=%s", session_id, user_id)
                    await send_json_or_log(websocket, {"type": "error", "message": str(exc)}, "voice round error")
                finally:
                    await close_or_log(websocket, "voice round complete")
                return
        # 区分“有空识别结果”和“SDK 完全无回调”，方便用户和排障人员判断。
        message = "没有识别到有效语音，请靠近麦克风后重试。" if saw_asr_result else "语音识别未返回结果，请重试。"
        await send_json_or_log(websocket, {"type": "error", "message": message}, "voice asr empty result")

    try:
        # 两个协程通过有界 Queue 解耦，防止网络突发帧无限占用内存。
        await asyncio.gather(receive_audio(websocket, audio_queue), process_asr())
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        log.exception("voice websocket failed")
        await send_json_or_log(websocket, {"type": "error", "message": str(exc)}, "voice websocket error")
    finally:
        await close_or_log(websocket, "voice websocket finalizer")


async def run_graph_and_stream(websocket: WebSocket, session_id: str, user_id: int, utterance: str, tts: TtsService) -> bool:
    """流式执行 Supervisor，并向前端发送商品、字幕和音频。

    返回值表示本轮是否成功提供音频。TTS 失败不会让已经生成的文字回复丢失，
    后续句子会跳过语音并向客户端发送一次 warning。
    """
    maker = get_sessionmaker()
    async with maker() as db:
        graph = websocket.app.state.voice_graph
        context = build_deps(db, websocket.app.state.agent_registry)
        sent_products = False
        final_state: dict = {}
        lock = SessionExecutionLock(context.redis, get_settings().agent_turn_lock_ttl_seconds)
        async with lock.hold(session_id, user_id):
            async for update in astream_turn(
                graph,
                {"session_id": session_id, "user_id": user_id, "utterance": utterance, "channel": "HOME_ENTRY"},
                context,
            ):
                # stream_mode="updates" 返回 {节点名: 本节点补丁}，这里只合并公开结果。
                for patch in update.values():
                    if not isinstance(patch, dict):
                        continue
                    final_state.update(patch)
                    # 商品一旦确定就先推卡片，不必等待口播和 TTS，降低用户感知延迟。
                    if not sent_products and patch.get("display_blocks"):
                        await websocket.send_json({"type": "recommendation", "items": normalize_items(patch["display_blocks"])})
                        sent_products = True
        speech = final_state.get("speech_text") or ""
        audio_available = True
        # 逐句合成既能及时显示字幕，也能更早播放第一段音频。
        for sentence in split_sentences(speech):
            await websocket.send_json({"type": "caption", "text": sentence})
            if not audio_available:
                continue
            try:
                async for chunk in tts.synthesize(sentence):
                    await websocket.send_bytes(chunk)
            except WebSocketDisconnect:
                raise
            except Exception:
                audio_available = False
                log.exception("TTS synthesis failed; keeping text reply: session_id=%s", session_id)
                await websocket.send_json(
                    {
                        "type": "warning",
                        "message": "文字回复已生成，但语音合成暂时不可用。",
                    }
                )
        return audio_available


def normalize_items(items: list[dict]) -> list[dict]:
    """把内部 snake_case/Decimal 商品结构转换成浏览器可 JSON 化的格式。"""
    output = []
    for item in items:
        output.append(
            {
                "productId": item.get("product_id") or item.get("productId"),
                "name": item.get("name"),
                "price": str(item.get("price")) if isinstance(item.get("price"), Decimal) else item.get("price"),
                "reason": item.get("reason"),
                "matchScore": item.get("match_score") or item.get("matchScore"),
                "attributes": item.get("attributes") or {},
            }
        )
    return output
