"""MCP 客户端能力检测."""

from typing import Any

from fastmcp import Context


async def check_sampling_capability(ctx: Context) -> dict[str, Any]:
    """检测客户端是否支持 LLM sampling.

    Args:
        ctx: MCP 上下文

    Returns:
        包含检测结果和详细信息的字典
    """
    try:
        await ctx.sample(
            messages="test",
            max_tokens=1,
        )
        return {
            "supported": True,
            "method": "sample",
            "details": "LLM sampling is supported",
        }
    except Exception as e:
        error_msg = str(e)
        if "does not support sampling" in error_msg.lower():
            return {
                "supported": False,
                "method": "sample",
                "details": "Client does not declare sampling capability",
                "error": error_msg,
            }
        return {
            "supported": False,
            "method": "sample",
            "details": f"Unexpected error: {error_msg}",
            "error": error_msg,
        }


async def check_elicitation_capability(ctx: Context) -> dict[str, Any]:
    """检测客户端是否支持 user elicitation.

    Args:
        ctx: MCP 上下文

    Returns:
        包含检测结果和详细信息的字典
    """
    try:
        result = await ctx.elicit("capability check")  # type: ignore[call-arg]
        return {
            "supported": True,
            "method": "elicit",
            "details": "User elicitation is supported",
            "result_type": type(result).__name__,
        }
    except Exception as e:
        error_msg = str(e)
        if "method not found" in error_msg.lower() or "not found" in error_msg.lower():
            return {
                "supported": False,
                "method": "elicit",
                "details": "Client does not support elicitation method",
                "error": error_msg,
            }
        return {
            "supported": False,
            "method": "elicit",
            "details": f"Unexpected error: {error_msg}",
            "error": error_msg,
        }


async def get_client_capabilities(ctx: Context) -> dict[str, Any]:
    """获取客户端的所有 MCP 能力.

    Args:
        ctx: MCP 上下文

    Returns:
        包含所有能力检测结果的字典
    """
    sampling_result = await check_sampling_capability(ctx)
    elicitation_result = await check_elicitation_capability(ctx)

    return {
        "sampling": sampling_result,
        "elicitation": elicitation_result,
        "summary": {
            "advanced_apis_supported": (
                sampling_result.get("supported", False) and
                elicitation_result.get("supported", False)
            ),
            "fallback_required": not (
                sampling_result.get("supported", False) and
                elicitation_result.get("supported", False)
            ),
        }
    }
