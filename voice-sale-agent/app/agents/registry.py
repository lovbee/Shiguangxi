"""启动期 Agent 注册表和依赖组装。

四个 Worker 子图在应用启动时构建一次。请求级数据库服务不放在这里，而由
``app.api.deps.build_deps`` 通过 LangGraph Runtime context 注入。
"""

from dataclasses import dataclass

from langchain_community.chat_models.tongyi import ChatTongyi

from app.agents.clarification import RequirementClarificationAgent
from app.agents.emotion import EmotionResponseAgent
from app.agents.intent import IntentUnderstandingAgent
from app.agents.llm import ChatClient
from app.agents.prompts import PromptLoader
from app.agents.recommendation import ProductRecommendationAgent
from app.core.config import Settings
from app.services.clarify_rules import ClarifyRuleService
from app.services.mood import SessionMoodDetector
from app.services.profile_reranker import ProfileReranker
from app.services.recommend_reason import RecommendReasonService


@dataclass(frozen=True)
class AgentRegistry:
    """应用生命周期内可安全复用的 Worker 与无状态辅助服务集合。"""

    intent: IntentUnderstandingAgent
    clarification: RequirementClarificationAgent
    recommendation: ProductRecommendationAgent
    emotion: EmotionResponseAgent
    reranker: ProfileReranker
    reason_service: RecommendReasonService


def build_agent_registry(settings: Settings, redis) -> AgentRegistry:
    """创建模型客户端、Prompt 加载器并编译四个 Worker 子图。"""
    prompts = PromptLoader()
    chat = ChatClient(settings)
    reranker = ProfileReranker()
    reason_service = RecommendReasonService(
        chat,
        prompts,
        settings,
        ProductRecommendationAgent.prompt_path,
    )
    # 推荐 Worker 使用 LangChain ChatTongyi 的 bind_tools 能力进行受控工具规划；
    # 其他 Worker 通过上面的 ChatClient 使用 DashScope 原生调用。
    tool_model = ChatTongyi(
        model=settings.llm_light_model,
        api_key=settings.dashscope_api_key,
        max_retries=2,
    )
    return AgentRegistry(
        intent=IntentUnderstandingAgent(chat, prompts, redis, settings),
        clarification=RequirementClarificationAgent(chat, prompts, ClarifyRuleService()),
        recommendation=ProductRecommendationAgent(prompts, tool_model),
        emotion=EmotionResponseAgent(chat, prompts, settings, SessionMoodDetector()),
        reranker=reranker,
        reason_service=reason_service,
    )
