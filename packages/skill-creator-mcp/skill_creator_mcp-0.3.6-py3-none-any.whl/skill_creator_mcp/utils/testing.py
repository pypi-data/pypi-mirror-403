"""测试工具函数.

此模块包含用于验证 FastMCP Context API 能力的测试工具。
这些工具用于检测客户端对 sampling、elicitation 和状态管理的支持。
"""

import json
import re
from typing import Any

# 告诉 pytest 不要将此模块中的函数作为测试收集
__test__ = False

from fastmcp import Context


async def check_client_capabilities(ctx: Context) -> dict[str, Any]:
    """检测 MCP 客户端的能力支持情况.

    检测客户端是否支持高级 MCP 功能，如 sampling 和 elicitation。

    Returns:
        包含客户端能力检测结果的字典
    """
    from .capability_detection import get_client_capabilities

    return await get_client_capabilities(ctx)


async def test_llm_sampling(ctx: Context, prompt: str) -> dict[str, Any]:
    """测试 LLM Sampling 能力.

    验证 MCP Server 可以通过 ctx.sample() 调用客户端 LLM。

    Args:
        ctx: MCP 上下文
        prompt: 要发送给 LLM 的提示文本

    Returns:
        包含测试结果的字典，包括 LLM 响应文本和历史记录
    """
    try:
        result = await ctx.sample(
            messages=prompt,
            system_prompt="You are a helpful assistant for skill creation.",
            temperature=0.7,
        )

        return {
            "success": True,
            "test": "test_llm_sampling",
            "has_response": result.text is not None,
            "response_text": result.text or "",
            "has_history": result.history is not None,
            "history_length": len(result.history) if result.history else 0,
            "message": "LLM Sampling 能力验证通过",
        }
    except Exception as e:
        return {
            "success": False,
            "test": "test_llm_sampling",
            "error": str(e),
            "message": f"LLM Sampling 验证失败: {e}",
        }


async def test_user_elicitation(
    ctx: Context, prompt: str = "请提供技能名称（小写字母、数字、连字符）"
) -> dict[str, Any]:
    """测试用户征询 (User Elicitation) 能力.

    验证可以通过 ctx.elicit() 请求用户输入结构化数据。

    Args:
        ctx: MCP 上下文
        prompt: 向用户显示的提示文本

    Returns:
        包含测试结果的字典
    """
    try:
        result = await ctx.elicit(prompt)  # type: ignore[call-arg]

        # FastMCP 返回 AcceptedElicitation | DeclinedElicitation | CancelledElicitation
        if hasattr(result, "accepted") and result.accepted:  # type: ignore[union-attr]
            return {
                "success": True,
                "test": "test_user_elicitation",
                "action": "accept",
                "user_input": str(getattr(result, "data", "")) if hasattr(result, "data") else "",
                "message": "User Elicitation 能力验证通过 - 用户接受了输入请求",
            }
        else:
            return {
                "success": True,
                "test": "test_user_elicitation",
                "action": "cancel",
                "message": "User Elicitation 能力验证通过 - 用户取消了输入请求",
            }
    except Exception as e:
        return {
            "success": False,
            "test": "test_user_elicitation",
            "error": str(e),
            "message": f"User Elicitation 验证失败: {e}",
        }


async def test_conversation_loop(ctx: Context, user_input: str) -> dict[str, Any]:
    """测试对话循环和状态管理能力.

    验证可以在对话循环中使用 session state 保存历史，
    并且 LLM 可以利用对话历史生成更连贯的响应。

    Args:
        ctx: MCP 上下文
        user_input: 用户输入的文本

    Returns:
        包含测试结果的字典，包括 LLM 响应和会话状态
    """
    try:
        # 获取历史对话
        history_data = await ctx.get_state("test_conversation_history")
        history = list(history_data) if history_data else []

        # 添加用户输入
        history.append({"role": "user", "content": user_input})

        # 调用 LLM 生成响应
        result = await ctx.sample(
            messages=history,
            system_prompt="You are a skill creation consultant. Help users clarify their requirements.",
        )

        # 添加 AI 响应
        if result.text:
            history.append({"role": "assistant", "content": result.text})

        # 保存历史
        await ctx.set_state("test_conversation_history", history)  # type: ignore[func-returns-value]

        return {
            "success": True,
            "test": "test_conversation_loop",
            "has_llm_response": result.text is not None,
            "llm_response": result.text or "",
            "conversation_length": len(history),
            "history_saved": True,
            "message": "对话循环和状态管理验证通过",
        }
    except Exception as e:
        return {
            "success": False,
            "test": "test_conversation_loop",
            "error": str(e),
            "message": f"对话循环验证失败: {e}",
        }


async def test_requirement_completeness(ctx: Context, requirement: str) -> dict[str, Any]:
    """测试需求完整性判断能力.

    验证 LLM 能够判断需求是否完整，并识别缺失的关键信息。

    Args:
        ctx: MCP 上下文
        requirement: 技能创建需求描述

    Returns:
        包含测试结果的字典，包括完整性分析和缺失信息列表
    """
    try:
        prompt = f"""分析以下技能创建需求，判断是否包含所有必要信息：

{requirement}

必要信息包括：
1. skill_name - 技能名称
2. skill_function - 主要功能
3. use_cases - 使用场景
4. template_type - 模板类型

请返回 JSON 格式，包含：
- is_complete: bool（是否完整）
- missing_info: list[str]（缺失的信息列表）
- suggestions: list[str]（补充建议列表）
"""

        result = await ctx.sample(
            messages=prompt,
            system_prompt="You are a skill creation consultant. Analyze requirements for completeness.",
            temperature=0.3,
        )

        # 尝试解析 LLM 返回的 JSON
        json_match = re.search(r"\{.*\}", result.text or "", re.DOTALL)
        if json_match:
            try:
                analysis = json.loads(json_match.group())
                return {
                    "success": True,
                    "test": "test_requirement_completeness",
                    "llm_analysis": analysis,
                    "has_missing_info": "missing_info" in analysis,
                    "message": "需求完整性判断验证通过",
                }
            except json.JSONDecodeError:
                pass

        # 如果无法解析 JSON，返回原始响应
        return {
            "success": True,
            "test": "test_requirement_completeness",
            "llm_response": result.text or "",
            "json_parse_failed": True,
            "message": "需求完整性判断验证通过（但 JSON 解析失败）",
        }
    except Exception as e:
        return {
            "success": False,
            "test": "test_requirement_completeness",
            "error": str(e),
            "message": f"需求完整性判断验证失败: {e}",
        }
