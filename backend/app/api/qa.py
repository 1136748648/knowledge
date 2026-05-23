from fastapi import APIRouter, Depends

from app.core.security import get_current_active_user
from app.models.schemas import UserContext, QARequest, QAResponse
from app.agents.router import RouterAgent

router = APIRouter()


@router.post("/ask", response_model=QAResponse)
async def ask_question(
    data: QARequest,
    current_user: UserContext = Depends(get_current_active_user),
):
    """智能问答入口"""
    agent = RouterAgent(current_user)
    result = await agent.route(data.question)
    return QAResponse(
        answer=result["answer"],
        sources=result["sources"],
        intent=result["intent"],
        confidence=result["confidence"],
    )
