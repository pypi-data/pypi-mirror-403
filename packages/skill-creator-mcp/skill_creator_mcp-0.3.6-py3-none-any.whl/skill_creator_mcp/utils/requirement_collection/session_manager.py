"""会话状态管理模块（简化版）.

只提供基础的会话状态操作，不包含业务逻辑。
符合 ADR 001: MCP Server 只提供原子操作。
"""

from typing import Any

from fastmcp import Context


async def load_session_state(ctx: Context, session_id: str) -> Any:
    """加载会话状态.

    Args:
        ctx: MCP 上下文
        session_id: 会话ID

    Returns:
        会话状态对象，如果不存在则返回 None
    """
    from ...models.skill_config import SessionState

    state_key = f"requirement_{session_id}"
    state_data = await ctx.get_state(state_key)

    if state_data:
        return SessionState.model_validate(state_data)
    return None


async def save_session_state(ctx: Context, session_id: str, state: Any) -> None:
    """保存会话状态.

    Args:
        ctx: MCP 上下文
        session_id: 会话ID
        state: 会话状态对象
    """
    state_key = f"requirement_{session_id}"
    await ctx.set_state(state_key, state.model_dump())  # type: ignore[func-returns-value]


__all__ = [
    "load_session_state",
    "save_session_state",
]
