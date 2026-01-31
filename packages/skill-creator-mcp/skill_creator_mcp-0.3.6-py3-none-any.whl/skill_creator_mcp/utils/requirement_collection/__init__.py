"""需求收集辅助函数（简化版）.

此模块包含简化的需求收集辅助函数。
符合 ADR 001: MCP Server 只提供原子操作，不包含工作流逻辑。
"""

# 会话状态管理
# LLM 服务
from .llm_services import (
    check_requirement_completeness,
)

# 问题
from .questions import (
    get_next_static_question,
    get_static_questions,
)
from .session_manager import (
    load_session_state,
    save_session_state,
)

# 验证
from .validation import (
    validate_requirement_answer,
)

__all__ = [
    # 会话状态管理
    "load_session_state",
    "save_session_state",
    # 验证
    "validate_requirement_answer",
    # 问题
    "get_static_questions",
    "get_next_static_question",
    # LLM 服务
    "check_requirement_completeness",
]
