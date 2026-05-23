from app.agents.router import RouterAgent
from app.models.schemas import UserContext


class QAService:
    def __init__(self):
        pass

    async def ask_question(self, user: UserContext, question: str) -> dict:
        agent = RouterAgent(user)
        result = await agent.route(question)
        return result