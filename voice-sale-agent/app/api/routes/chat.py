"""Java 门面调用的文本导购备用入口。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import AgentRegistry
from app.api.deps import (
    build_deps,
    get_agent_registry,
    get_current_user_id,
    get_db,
    get_voice_graph,
)
from app.core.config import get_settings
from app.graph.execution import ainvoke_turn
from app.models.dto import ChatTextRequest, ChatTextResponse
from app.services.session_execution_lock import SessionExecutionLock

router = APIRouter(prefix="/internal/v1/chat", tags=["internal-chat"])


@router.post("/text", response_model=ChatTextResponse, response_model_by_alias=True)
async def chat_text(
    req: ChatTextRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    graph=Depends(get_voice_graph),
    agents: AgentRegistry = Depends(get_agent_registry),
) -> ChatTextResponse:
    """执行一轮文本导购，供 Java 门面在无麦克风场景下调用。"""
    context = build_deps(db, agents)
    lock = SessionExecutionLock(context.redis, get_settings().agent_turn_lock_ttl_seconds)
    async with lock.hold(req.session_id, user_id):
        result = await ainvoke_turn(
            graph,
            {"session_id": req.session_id, "user_id": user_id, "utterance": req.utterance, "channel": "HOME_ENTRY"},
            context,
        )
    return ChatTextResponse(
        speechText=result.get("speech_text") or "",
        displayBlocks=result.get("display_blocks") or [],
        intent=result.get("revised_intent") or result.get("current_intent"),
        phase=result.get("phase"),
    )
