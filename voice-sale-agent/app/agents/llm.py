"""DashScope 文本大模型的异步适配层。

DashScope Generation SDK 的主调用是同步的，所以完整回复放进工作线程；
调用方只依赖本类，不需要处理供应商响应对象和重试细节。
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any, TypeVar

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.json_utils import extract_json_object
from app.core.config import Settings

T = TypeVar("T", bound=BaseModel)
log = logging.getLogger(__name__)


class ChatClient:
    """提供纯文本、结构化 JSON 和流式文本三种统一调用方式。"""

    def __init__(self, settings: Settings):
        """保存 DashScope API Key 和默认模型等配置。"""
        self.settings = settings

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=0.5, max=3))
    async def complete_text(self, *, model: str, system: str, user: str) -> str:
        """在线程中请求完整回复，临时失败时指数退避并最多尝试两次。"""
        return await asyncio.to_thread(self._complete_text_sync, model, system, user)

    async def complete_json(self, *, model: str, system: str, user: str, schema: type[T]) -> T:
        """请求文本、提取 JSON，再用调用方指定的 Pydantic Schema 校验。"""
        text = await self.complete_text(model=model, system=system, user=user)
        return schema.model_validate(extract_json_object(text))

    async def stream_text(self, *, model: str, system: str, user: str) -> AsyncIterator[str]:
        """逐块返回增量文本；流式链路失败时降级为一次完整回复。"""
        try:
            async for chunk in self._stream_text_impl(model=model, system=system, user=user):
                yield chunk
        except Exception:
            log.exception("DashScope streaming failed; falling back to complete_text")
            yield await self.complete_text(model=model, system=system, user=user)

    async def _stream_text_impl(self, *, model: str, system: str, user: str) -> AsyncIterator[str]:
        """创建供应商流式迭代器并转换成纯文本块。"""
        def make_iterator():
            """在线程边界内初始化 DashScope 的同步迭代器。"""
            import dashscope
            from dashscope import Generation

            dashscope.api_key = self.settings.dashscope_api_key
            return Generation.call(
                model=model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                result_format="message",
                stream=True,
                incremental_output=True,
            )

        iterator = await asyncio.to_thread(make_iterator)
        # SDK 迭代器本身是同步对象；当前实现逐项读取，主链尚未使用此方法。
        for response in iterator:
            text = self._extract_text(response)
            if text:
                yield text

    def _complete_text_sync(self, model: str, system: str, user: str) -> str:
        """真正执行同步 Generation.call，并拒绝空响应。"""
        import dashscope
        from dashscope import Generation

        dashscope.api_key = self.settings.dashscope_api_key
        response = Generation.call(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            result_format="message",
        )
        text = self._extract_text(response)
        if not text:
            raise RuntimeError(f"Empty DashScope response: {response!r}")
        return text

    @staticmethod
    def _extract_text(response: Any) -> str:
        """兼容 DashScope 对象/字典两种响应形态，提取第一条文本。"""
        output = getattr(response, "output", None)
        if output is None and isinstance(response, dict):
            output = response.get("output")
        if isinstance(output, dict):
            choices = output.get("choices") or []
            if choices:
                message = choices[0].get("message") or {}
                content = message.get("content")
                if isinstance(content, str):
                    return content
            text = output.get("text")
            if isinstance(text, str):
                return text
        return ""
