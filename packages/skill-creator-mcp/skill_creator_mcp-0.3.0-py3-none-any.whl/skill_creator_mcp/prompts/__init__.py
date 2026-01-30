"""MCP Prompts 模块.

提供可重用的提示模板，用于指导 AI 完成特定任务。
"""

from skill_creator_mcp.prompts.create_skill import get_create_skill_prompt
from skill_creator_mcp.prompts.refactor_skill import get_refactor_skill_prompt
from skill_creator_mcp.prompts.validate_skill import get_validate_skill_prompt

__all__ = [
    "get_create_skill_prompt",
    "get_validate_skill_prompt",
    "get_refactor_skill_prompt",
]
