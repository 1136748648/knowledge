"""Intent Classifier Skill - 意图分类"""

from .skill import IntentClassifierSkill

__all__ = ["IntentClassifierSkill", "execute"]


async def execute(question: str) -> dict:
    """执行意图分类"""
    skill = IntentClassifierSkill()
    return await skill.classify(question)
