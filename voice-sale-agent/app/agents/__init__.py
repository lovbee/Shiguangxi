"""四个 Worker Agent 及其输入输出协议的公共导出入口。

外部代码可以从 ``app.agents`` 导入稳定名称，而不必知道具体文件位置。
``__all__`` 也明确了这个包承诺提供哪些公开对象。
"""

from app.agents.clarification import RequirementClarificationAgent
from app.agents.contracts import (
    EmotionResponseInput,
    EmotionResponseOutput,
    IntentUnderstandingInput,
    IntentUnderstandingOutput,
    ProductRecommendationInput,
    ProductRecommendationOutput,
    RequirementClarificationInput,
    RequirementClarificationOutput,
)
from app.agents.emotion import EmotionResponseAgent
from app.agents.intent import IntentUnderstandingAgent
from app.agents.recommendation import ProductRecommendationAgent

__all__ = [
    "EmotionResponseAgent",
    "EmotionResponseInput",
    "EmotionResponseOutput",
    "IntentUnderstandingAgent",
    "IntentUnderstandingInput",
    "IntentUnderstandingOutput",
    "ProductRecommendationAgent",
    "ProductRecommendationInput",
    "ProductRecommendationOutput",
    "RequirementClarificationAgent",
    "RequirementClarificationInput",
    "RequirementClarificationOutput",
]
