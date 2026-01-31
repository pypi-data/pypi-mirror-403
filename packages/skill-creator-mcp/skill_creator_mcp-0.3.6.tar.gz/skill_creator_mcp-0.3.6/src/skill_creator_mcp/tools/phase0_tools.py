"""测试工具模块.

包含技术验证和测试的 MCP 工具函数。
"""

from typing import Any

from fastmcp import Context, FastMCP


async def check_client_capabilities(ctx: Context, mcp: FastMCP) -> dict[str, Any]:
    """检测 MCP 客户端的能力支持情况.

    检测客户端是否支持高级 MCP 功能，如 sampling 和 elicitation。

    Args:
        ctx: MCP 上下文
        mcp: FastMCP 实例

    Returns:
        包含客户端能力检测结果的字典
    """
    from ..utils.capability_detection import get_client_capabilities

    return await get_client_capabilities(ctx)


async def test_llm_sampling(ctx: Context, mcp: FastMCP, prompt: str) -> dict[str, Any]:
    """测试 LLM Sampling 能力.

    验证 MCP Server 可以通过 ctx.sample() 调用客户端 LLM。

    Args:
        ctx: MCP 上下文
        mcp: FastMCP 实例
        prompt: 要发送给 LLM 的提示文本

    Returns:
        包含测试结果的字典，包括 LLM 响应文本和历史记录
    """
    from ..utils import testing

    return await testing.test_llm_sampling(ctx, prompt)


async def test_user_elicitation(
    ctx: Context, mcp: FastMCP, prompt: str = "请提供技能名称（小写字母、数字、连字符）"
) -> dict[str, Any]:
    """测试用户征询 (User Elicitation) 能力.

    验证可以通过 ctx.elicit() 请求用户输入结构化数据。

    Args:
        ctx: MCP 上下文
        mcp: FastMCP 实例
        prompt: 向用户显示的提示文本

    Returns:
        包含测试结果的字典
    """
    from ..utils import testing

    return await testing.test_user_elicitation(ctx, prompt)


async def test_conversation_loop(ctx: Context, mcp: FastMCP, user_input: str) -> dict[str, Any]:
    """测试对话循环和状态管理能力.

    验证可以在对话循环中使用 session state 保存历史，
    并且 LLM 可以利用对话历史生成更连贯的响应。

    Args:
        ctx: MCP 上下文
        mcp: FastMCP 实例
        user_input: 用户输入的文本

    Returns:
        包含测试结果的字典，包括 LLM 响应和会话状态
    """
    from ..utils import testing

    return await testing.test_conversation_loop(ctx, user_input)


async def test_requirement_completeness(ctx: Context, mcp: FastMCP, requirement: str) -> dict[str, Any]:
    """测试需求完整性判断能力.

    验证 LLM 能够判断需求是否完整，并识别缺失的关键信息。

    Args:
        ctx: MCP 上下文
        mcp: FastMCP 实例
        requirement: 技能创建需求描述

    Returns:
        包含测试结果的字典，包括完整性分析和缺失信息列表
    """
    from ..utils import testing

    return await testing.test_requirement_completeness(ctx, requirement)


__all__ = [
    "check_client_capabilities",
    "test_llm_sampling",
    "test_user_elicitation",
    "test_conversation_loop",
    "test_requirement_completeness",
]
