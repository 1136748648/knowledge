from fastapi import APIRouter, Depends

from app.core.security import get_current_active_user
from app.models.schemas import UserContext, QARequest, QAResponse
from app.services import get_qa_service, QAService

router = APIRouter()


@router.post("/ask", response_model=QAResponse)
async def ask_question(
    data: QARequest,
    service: QAService = Depends(get_qa_service),
    current_user: UserContext = Depends(get_current_active_user),
):
    """智能问答入口"""
    result = await service.ask_question(current_user, data.question)
    return QAResponse(
        answer=result["answer"],
        sources=result["sources"],
        intent=result["intent"],
        confidence=result["confidence"],
    )