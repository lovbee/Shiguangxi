"""为最终前三商品生成与用户需求对应的简短推荐理由。"""

import json
from decimal import Decimal

from app.agents.json_utils import extract_json_array
from app.agents.llm import ChatClient
from app.agents.prompts import PromptLoader
from app.core.config import Settings


class RecommendReasonService:
    """调用主模型返回 productId/reason 数组，并合并回权威商品字典。"""

    def __init__(
        self,
        chat: ChatClient,
        prompts: PromptLoader,
        settings: Settings,
        prompt_path: str = "prompts/recommend-reason.txt",
    ):
        """注入模型、Prompt、配置和可替换的理由 Prompt 路径。"""
        self.chat = chat
        self.prompts = prompts
        self.settings = settings
        self.prompt_path = prompt_path

    async def attach_reasons(self, session_id: str, user_needs: str, products: list[dict]) -> list[dict]:
        """给商品附加理由；模型或 JSON 失败时保留原商品和原理由。

        ``session_id`` 当前为后续日志/缓存扩展保留，尚未参与 Prompt。
        """
        if not products:
            return products
        payload = {
            "userNeeds": user_needs,
            "products": [
                {
                    "productId": p["product_id"],
                    "name": p["name"],
                    "price": str(p.get("price")) if isinstance(p.get("price"), Decimal) else p.get("price"),
                    "attributes": p.get("attributes") or {},
                }
                for p in products
            ],
        }
        try:
            text = await self.chat.complete_text(
                model=self.settings.llm_main_model,
                system=self.prompts.load(self.prompt_path),
                user=json.dumps(payload, ensure_ascii=False, default=str),
            )
            parsed = extract_json_array(text)
            # 按 ID 合并而不是相信模型数组顺序，防止漏项或顺序漂移。
            reason_map = {int(row["productId"]): row.get("reason") or "" for row in parsed if "productId" in row}
            return [self._with_reason(p, reason_map.get(int(p["product_id"]), "")) for p in products]
        except Exception:  # noqa: BLE001 - recommendation reasons are optional enrichment
            return [self._with_reason(p, p.get("reason") or "") for p in products]

    @staticmethod
    def _with_reason(product: dict, reason: str) -> dict:
        """复制商品后设置理由，避免原候选列表被意外原地修改。"""
        out = dict(product)
        out["reason"] = reason
        return out
