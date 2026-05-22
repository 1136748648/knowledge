from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_active_user
from app.models.schemas import UserContext, QARequest, QAResponse
from app.agents.router import RouterAgent

router = APIRouter()


@router.post("/ask", response_model=QAResponse)
async def ask_question(
    data: QARequest,
    current_user: UserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """智能问答入口"""
    agent = RouterAgent(db, current_user)
    result = await agent.route(data.question)
    return QAResponse(
        answer=result["answer"],
        sources=result["sources"],
        intent=result["intent"],
        confidence=result["confidence"],
    )
