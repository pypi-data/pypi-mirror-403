"""需求收集会话管理工具模块.

提供原子化的会话管理工具，不包含工作流逻辑。
符合 ADR 001: MCP Server 只提供原子操作 + 文件I/O + 数据验证。
"""

from datetime import datetime
from datetime import timezone as tz
from typing import Any

from fastmcp import Context


async def create_requirement_session(
    ctx: Context,
    mode: str = "basic",
    total_steps: int | None = None,
) -> dict[str, Any]:
    """
    创建新的需求收集会话.

    这是一个原子操作工具，只负责创建会话状态。
    工作流编排由 Agent-Skill 负责。

    Args:
        ctx: MCP 上下文
        mode: 收集模式（basic/complete/brainstorm/progressive）
        total_steps: 总步骤数（可选，默认根据模式自动计算）

    Returns:
        包含会话信息的字典: {
            "session_id": str,
            "mode": str,
            "total_steps": int,
            "current_step": int,
            "started_at": str,
            "answers": dict
        }
    """
    try:
        # 验证模式
        valid_modes = ["basic", "complete", "brainstorm", "progressive"]
        if mode not in valid_modes:
            return {
                "success": False,
                "error": f"无效的模式: {mode}",
                "valid_modes": valid_modes,
            }

        # 计算总步骤数
        if total_steps is None:
            from ..constants import BASIC_REQUIREMENT_STEPS, COMPLETE_REQUIREMENT_STEPS

            if mode in ("brainstorm", "progressive"):
                total_steps = 100  # 动态模式，无固定步骤
            elif mode == "complete":
                total_steps = len(BASIC_REQUIREMENT_STEPS) + len(COMPLETE_REQUIREMENT_STEPS)
            else:  # basic
                total_steps = len(BASIC_REQUIREMENT_STEPS)

        # 生成会话ID
        from ..models.skill_config import SessionState

        session_id = f"req_{datetime.now(tz.utc).isoformat()}"

        # 创建会话状态
        session_state = SessionState(
            current_step_index=0,
            answers={},
            started_at=datetime.now(tz.utc).isoformat(),
            completed=False,
            mode=mode,  # type: ignore[arg-type]
            total_steps=total_steps,
        )

        # 保存到 MCP session state
        state_key = f"requirement_{session_id}"
        await ctx.set_state(state_key, session_state.model_dump())  # type: ignore[func-returns-value]

        return {
            "success": True,
            "session_id": session_id,
            "mode": mode,
            "total_steps": total_steps,
            "current_step": 0,
            "started_at": session_state.started_at,
            "answers": session_state.answers,
            "completed": False,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"创建会话失败: {e}",
            "error_type": "internal_error",
        }


async def get_requirement_session(
    ctx: Context,
    session_id: str,
) -> dict[str, Any]:
    """
    获取需求收集会话状态.

    这是一个原子操作工具，只负责读取会话状态。

    Args:
        ctx: MCP 上下文
        session_id: 会话ID

    Returns:
        包含会话状态的字典: {
            "session_id": str,
            "mode": str,
            "current_step": int,
            "total_steps": int,
            "answers": dict,
            "completed": bool,
            "started_at": str
        }
    """
    try:
        # 从 MCP session state 读取
        state_key = f"requirement_{session_id}"
        state_data = await ctx.get_state(state_key)

        if not state_data:
            return {
                "success": False,
                "error": f"会话不存在: {session_id}",
                "error_type": "session_not_found",
            }

        from ..models.skill_config import SessionState

        session_state = SessionState.model_validate(state_data)

        return {
            "success": True,
            "session_id": session_id,
            "mode": session_state.mode,
            "current_step": session_state.current_step_index,
            "total_steps": session_state.total_steps,
            "answers": session_state.answers,
            "completed": session_state.completed,
            "started_at": session_state.started_at,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"获取会话失败: {e}",
            "error_type": "internal_error",
        }


async def update_requirement_answer(
    ctx: Context,
    session_id: str,
    question_key: str,
    answer: str,
) -> dict[str, Any]:
    """
    更新需求收集会话中的答案.

    这是一个原子操作工具，只负责更新单个答案。
    不包含验证逻辑，验证由专门的工具处理。

    Args:
        ctx: MCP 上下文
        session_id: 会话ID
        question_key: 问题键（如 skill_name, skill_function）
        answer: 用户答案

    Returns:
        包含更新结果的字典: {
            "success": bool,
            "session_id": str,
            "updated": bool,
            "current_step": int,
            "completed": bool
        }
    """
    try:
        # 获取当前会话状态
        state_key = f"requirement_{session_id}"
        state_data = await ctx.get_state(state_key)

        if not state_data:
            return {
                "success": False,
                "error": f"会话不存在: {session_id}",
                "error_type": "session_not_found",
            }

        from ..models.skill_config import SessionState

        session_state = SessionState.model_validate(state_data)

        # 更新答案
        session_state.answers[question_key] = answer

        # 保存更新后的状态
        await ctx.set_state(state_key, session_state.model_dump())  # type: ignore[func-returns-value]

        return {
            "success": True,
            "session_id": session_id,
            "updated": True,
            "current_step": session_state.current_step_index,
            "completed": session_state.completed,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"更新答案失败: {e}",
            "error_type": "internal_error",
        }


__all__ = [
    "create_requirement_session",
    "get_requirement_session",
    "update_requirement_answer",
]
