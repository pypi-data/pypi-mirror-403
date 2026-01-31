"""需求收集验证工具模块.

提供原子化的验证工具，不包含工作流逻辑。
符合 ADR 001: MCP Server 只提供原子操作 + 文件I/O + 数据验证。
"""

import re
from typing import Any

from fastmcp import Context

from ..utils.requirement_collection.llm_services import (
    check_requirement_completeness as _check_requirement_completeness,
)


async def validate_answer_format(
    ctx: Context,
    answer: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    """
    验证答案格式.

    这是一个原子操作工具，只负责验证单个答案。
    不包含重试逻辑，重试由 Agent-Skill 编排。

    Args:
        ctx: MCP 上下文
        answer: 用户输入的答案
        validation: 验证规则字典

    Returns:
        包含验证结果的字典: {
            "valid": bool,
            "error": str | None,
            "formatted_answer": str | None
        }
    """
    try:
        # 提取验证字段
        field = validation.get("field", "answer")
        required = validation.get("required", False)
        min_length = validation.get("min_length")
        max_length = validation.get("max_length")
        options = validation.get("options")
        pattern = validation.get("pattern")
        help_text = validation.get("help_text")

        # 检查必填
        if required and not answer.strip():
            return {
                "valid": False,
                "error": f"{field} 是必填项",
                "formatted_answer": None,
            }

        # 如果答案为空且非必填，直接通过
        if not answer.strip():
            return {
                "valid": True,
                "error": None,
                "formatted_answer": "",
            }

        # 检查长度
        if min_length and len(answer) < min_length:
            return {
                "valid": False,
                "error": help_text or f"最少需要 {min_length} 个字符",
                "formatted_answer": None,
            }

        if max_length and len(answer) > max_length:
            return {
                "valid": False,
                "error": help_text or f"最多允许 {max_length} 个字符",
                "formatted_answer": None,
            }

        # 检查选项
        if options:
            normalized_answer = answer.strip().lower()
            valid_options = [opt.lower() for opt in options]
            if normalized_answer not in valid_options:
                return {
                    "valid": False,
                    "error": f"无效的选项，请选择: {', '.join(options)}",
                    "formatted_answer": None,
                }

        # 检查正则表达式
        if pattern:
            if not re.match(pattern, answer.strip()):
                return {
                    "valid": False,
                    "error": help_text or "格式不正确",
                    "formatted_answer": None,
                }

        # 格式化答案
        formatted_answer = answer.strip()

        return {
            "valid": True,
            "error": None,
            "formatted_answer": formatted_answer,
        }

    except Exception as e:
        return {
            "valid": False,
            "error": f"验证过程出错: {e}",
            "formatted_answer": None,
        }


async def check_requirement_completeness(
    ctx: Context,
    answers: dict[str, str],
    prompt_template: str | None = None,
) -> dict[str, Any]:
    """
    检查需求完整性（MCP工具版本）.

    这是一个MCP工具包装函数，调用llm_services中的核心函数。
    返回值格式符合MCP工具规范（包含success键）。

    Args:
        ctx: MCP 上下文
        answers: 已收集的答案
        prompt_template: 自定义Prompt模板（可选）

    Returns:
        包含完整性检查结果的字典: {
            "success": bool,
            "complete": bool,
            "missing_items": list[str],
            "suggestions": list[str],
            "error": str | None (可选)
        }
    """
    result = await _check_requirement_completeness(ctx, answers, prompt_template)

    # 包装返回值，添加success键
    wrapped_result = {
        "success": True,
        "complete": result.get("complete", False),
        "missing_items": result.get("missing_items", []),
        "suggestions": result.get("suggestions", []),
    }

    # 如果有error键，传递它
    if "error" in result:
        wrapped_result["error"] = result["error"]

    return wrapped_result


__all__ = [
    "validate_answer_format",
    "check_requirement_completeness",
]
