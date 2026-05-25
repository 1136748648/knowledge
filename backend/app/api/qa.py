from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.models.schemas import UserContext, QARequest, QAResponse
from app.services import get_qa_service, QAService
from app.dal import get_db

router = APIRouter()


@router.post("/ask", response_model=QAResponse)
async def ask_question(
    data: QARequest,
    service: QAService = Depends(get_qa_service),
    current_user: UserContext = Depends(get_current_active_user),
    db_session: AsyncSession = Depends(get_db),
):
    """智能问答入口 - 按新架构流程处理"""
    result = await service.ask_question(current_user, data.question, db_session)
    return QAResponse(
        answer=result["answer"],
        sources=result["sources"],
        intent=result["intent"],
        confidence=result["confidence"],
    )