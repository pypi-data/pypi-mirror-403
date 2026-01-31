"""问题模块（简化版）.

只提供静态问题获取功能，不包含动态问题生成逻辑。
动态问题生成逻辑应由 Agent-Skill 编排 LLM 工具完成。
符合 ADR 001: MCP Server 只提供原子操作。
"""

from typing import Any

from fastmcp import Context


def get_static_questions(mode: str) -> list[dict[str, Any]]:
    """获取指定模式的静态问题列表.

    Args:
        mode: 收集模式 (basic/complete)

    Returns:
        问题列表（动态模式返回空列表）
    """
    if mode in ("brainstorm", "progressive"):
        return []

    from ...constants import BASIC_REQUIREMENT_STEPS, COMPLETE_REQUIREMENT_STEPS

    all_steps = BASIC_REQUIREMENT_STEPS.copy()
    if mode == "complete":
        all_steps.extend(COMPLETE_REQUIREMENT_STEPS)
    return all_steps  # type: ignore[no-any-return]


async def get_next_static_question(
    ctx: Context,
    mode: str,
    step_index: int,
) -> dict[str, Any]:
    """获取下一个静态问题.

    Args:
        ctx: MCP 上下文
        mode: 收集模式 (basic/complete)
        step_index: 步骤索引

    Returns:
        包含问题数据的响应字典
    """
    all_steps = get_static_questions(mode)

    if step_index >= len(all_steps):
        return {
            "success": True,
            "completed": True,
            "message": "所有步骤已完成",
        }

    step_data = all_steps[step_index]
    return {
        "success": True,
        "question_key": step_data["key"],
        "question_text": step_data["prompt"],
        "validation": step_data["validation"],
        "title": step_data.get("title", ""),
        "step_index": step_index,
        "completed": False,
    }


__all__ = [
    "get_static_questions",
    "get_next_static_question",
]
