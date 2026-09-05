"""商品 pgvector 召回及关键词自动降级。

查询先调用 Embedding，再按 cosine distance ``<=>`` 取商品 ID。模型失败、
维度不一致、SQL 异常或零命中都会进入关键词搜索，以提高服务可用性。
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding import EmbeddingService
from app.services.keyword_search import build_keyword_search_sql

log = logging.getLogger(__name__)


def vector_literal(values: list[float]) -> str:
    """把浮点数组序列化为 pgvector 可 CAST 的 ``[v1,v2,...]`` 文本。"""
    return "[" + ",".join(f"{v:.8f}" for v in values) + "]"


class ProductVectorService:
    """共享结构化过滤条件的向量/关键词两级召回服务。"""

    def __init__(self, db: AsyncSession, embedding: EmbeddingService):
        """绑定当前请求数据库 Session 和查询向量服务。"""
        self.db = db
        self.embedding = embedding

    async def search(self, query: str, extra_filter: str, extra_params: dict, top_k: int) -> list[int]:
        """优先返回向量近邻 ID；任何不可用情况都调用关键词降级。"""
        try:
            qvec = await self.embedding.embed(query)
            expected_dim = getattr(self.embedding.settings, "embedding_dim", None)
            if not qvec:
                raise ValueError("empty query embedding")
            if expected_dim and len(qvec) != expected_dim:
                raise ValueError(f"embedding dimension mismatch: expected {expected_dim}, got {len(qvec)}")

            # extra_filter 只允许来自 SqlFilterBuilder，用户值全部在 params 中绑定。
            sql = "SELECT id FROM product WHERE status = 'ON_SALE' AND embedding IS NOT NULL"
            params = dict(extra_params)
            if extra_filter:
                sql += " AND " + extra_filter
            sql += " ORDER BY embedding <=> CAST(:query_embedding AS vector) LIMIT :top_k"
            params["query_embedding"] = vector_literal(qvec)
            params["top_k"] = max(1, int(top_k))
            result = await self.db.execute(text(sql), params)
            ids = [int(row[0]) for row in result.all()]
            if ids:
                return ids
            log.info("vector search returned no hits; using keyword fallback")
        except Exception as exc:  # noqa: BLE001 - fallback must cover provider and driver failures
            log.warning("vector search unavailable; using keyword fallback: %s", exc)
        return await self.keyword_search(query, extra_filter, extra_params, top_k)

    async def keyword_search(self, query: str, extra_filter: str, extra_params: dict, top_k: int) -> list[int]:
        """执行参数化 ILIKE 加权检索并返回商品 ID。"""
        sql, params = build_keyword_search_sql(query, extra_filter, extra_params, top_k)
        result = await self.db.execute(text(sql), params)
        return [int(row[0]) for row in result.all()]
