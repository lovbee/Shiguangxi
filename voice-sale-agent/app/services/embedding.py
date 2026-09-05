"""DashScope 文本向量化及 Redis 缓存。

查询文本会转换成固定维度浮点数组供 pgvector 检索。同一文本默认缓存 24 小时；
离线建索引和 LangGraph Store 可传 ``use_cache=False`` 保证直接请求模型。
"""

import asyncio
import hashlib
import json
from typing import Any

from redis.asyncio import Redis

from app.core.config import Settings


class EmbeddingService:
    """把同步 DashScope Embedding SDK 包装成异步服务。"""

    def __init__(self, redis: Redis | None, settings: Settings):
        """注入可选 Redis 缓存和 Embedding 模型配置。"""
        self.redis = redis
        self.settings = settings

    async def embed(self, text: str, *, use_cache: bool = True) -> list[float]:
        """返回文本向量；空白文本直接返回空列表。

        Redis 可选，因此离线脚本和 Store 初始化无需构造虚假客户端。
        """
        if not text.strip():
            return []
        # key 只存文本哈希，避免超长中文直接进入 Redis key。
        cache_key = "vs:embed:" + hashlib.md5(text.encode("utf-8")).hexdigest()
        if use_cache and self.redis is not None:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        vector = await asyncio.to_thread(self._embed_sync, text)
        if use_cache and self.redis is not None:
            await self.redis.set(cache_key, json.dumps(vector), ex=86400)
        return vector

    def _embed_sync(self, text: str) -> list[float]:
        """在线程内调用同步 SDK，并把所有元素规范成 float。"""
        import dashscope
        from dashscope import TextEmbedding

        dashscope.api_key = self.settings.dashscope_api_key
        response = TextEmbedding.call(
            model=self.settings.embedding_model,
            input=text,
            dimension=self.settings.embedding_dim,
        )
        vector = self._extract_vector(response)
        if not vector:
            raise RuntimeError(f"Empty embedding response: {response!r}")
        return [float(v) for v in vector]

    @staticmethod
    def _extract_vector(response: Any) -> list[float]:
        """兼容 DashScope 对象/字典及两种 embedding 字段形态。"""
        output = getattr(response, "output", None)
        if output is None and isinstance(response, dict):
            output = response.get("output")
        if isinstance(output, dict):
            embeddings = output.get("embeddings") or output.get("text_embedding") or []
            if embeddings:
                first = embeddings[0]
                if isinstance(first, dict):
                    return first.get("embedding") or []
                return first
        return []
