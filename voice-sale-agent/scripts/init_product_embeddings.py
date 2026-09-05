"""批量生成/重建商品向量的命令行脚本。

脚本读取商品 ORM，使用 ``ProductTextBuilder`` 构建文本，调用 DashScope
Embedding 后通过原生 SQL 写入 pgvector 列。每件商品单独提交，单个失败不会
中断整个批次，最终用进程退出码告诉自动化任务是否存在失败。
"""

import argparse
import asyncio
import logging
import time

from sqlalchemy import select, text

from app.core.config import get_settings
from app.models.db import Product
from app.repositories.db import close_db, get_sessionmaker, init_db
from app.services.embedding import EmbeddingService
from app.services.product_text_builder import ProductTextBuilder
from app.services.vector_search import vector_literal

log = logging.getLogger("init_product_embeddings")


async def initialize_embeddings(
    *,
    only_missing: bool = False,
    include_off_sale: bool = False,
    limit: int | None = None,
    delay_seconds: float = 0.0,
) -> tuple[int, int]:
    """处理符合条件的商品，返回 ``(成功数, 失败数)``。

    ``only_missing`` 用于增量补空向量，``include_off_sale`` 控制是否处理下架
    商品，``limit``/``delay_seconds`` 便于小批验证和供应商限流。
    """
    settings = get_settings()
    init_db(settings)
    success = 0
    failures = 0

    try:
        maker = get_sessionmaker()
        async with maker() as db:
            stmt = select(Product).order_by(Product.id)
            if only_missing:
                stmt = stmt.where(text("product.embedding IS NULL"))
            if not include_off_sale:
                stmt = stmt.where(Product.status == "ON_SALE")
            if limit is not None:
                stmt = stmt.limit(max(1, limit))

            products = list((await db.execute(stmt)).scalars().all())
            log.info("found %d products to embed", len(products))
            embedder = EmbeddingService(None, settings)
            text_builder = ProductTextBuilder()
            # 先在 Session 活跃时提取 ID/文本，后续循环只持有普通值。
            product_payloads = [(product.id, text_builder.build(product)) for product in products]

            for product_id, product_text in product_payloads:
                if not product_text:
                    log.warning("skip product_id=%s: empty product text", product_id)
                    failures += 1
                    continue

                try:
                    vector = await embedder.embed(product_text, use_cache=False)
                    if len(vector) != settings.embedding_dim:
                        raise ValueError(
                            f"embedding dimension mismatch: expected {settings.embedding_dim}, got {len(vector)}"
                        )
                    await db.execute(
                        text(
                            "UPDATE product "
                            "SET embedding = CAST(:embedding AS vector), updated_at = NOW() "
                            "WHERE id = :product_id"
                        ),
                        {"embedding": vector_literal(vector), "product_id": product_id},
                    )
                    # 每个商品独立事务，后面的失败不会回滚前面已成功的向量。
                    await db.commit()
                    success += 1
                    log.info("embedded product_id=%s (%d/%d)", product_id, success + failures, len(products))
                except Exception:
                    await db.rollback()
                    failures += 1
                    log.exception("failed product_id=%s", product_id)

                if delay_seconds > 0:
                    await asyncio.sleep(delay_seconds)
    finally:
        await close_db()

    return success, failures


def parse_args() -> argparse.Namespace:
    """定义并解析命令行参数。"""
    parser = argparse.ArgumentParser(description="Initialize product embeddings in PostgreSQL.")
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Only process products whose embedding is NULL. By default all on-sale products are reindexed.",
    )
    parser.add_argument("--include-off-sale", action="store_true", help="Also process products not currently on sale.")
    parser.add_argument("--limit", type=int, default=None, help="Process at most N products.")
    parser.add_argument("--delay", type=float, default=0.0, help="Sleep N seconds between embedding requests.")
    return parser.parse_args()


def main() -> int:
    """同步 CLI 入口：运行异步任务、记录耗时，并按失败数返回退出码。"""
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    started_at = time.perf_counter()
    success, failures = asyncio.run(
        initialize_embeddings(
            only_missing=args.only_missing,
            include_off_sale=args.include_off_sale,
            limit=args.limit,
            delay_seconds=max(0.0, args.delay),
        )
    )
    elapsed = time.perf_counter() - started_at
    log.info("embedding initialization finished: success=%d failures=%d elapsed=%.2fs", success, failures, elapsed)
    return 1 if failures else 0


if __name__ == "__main__":
    # 只有 ``python -m scripts.init_product_embeddings`` 直接运行时才退出进程；
    # 测试导入本模块不会自动访问数据库或调用 DashScope。
    raise SystemExit(main())
