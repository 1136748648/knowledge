"""Mermaid Renderer Skill - 思维导图和流程图渲染"""

from .skill import MermaidRendererSkill

__all__ = ["MermaidRendererSkill", "execute"]


async def execute(data: dict, format_type: str = "mermaid", depth: int = 3) -> dict:
    """执行思维导图渲染"""
    skill = MermaidRendererSkill()
    return await skill.render(data, format_type, depth)
