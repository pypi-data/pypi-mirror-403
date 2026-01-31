"""验证模块（简化版）.

只提供格式验证功能，不包含业务逻辑和工作流。
符合 ADR 001: MCP Server 只提供原子操作 + 数据验证。
"""

import re
from typing import Any


def validate_requirement_answer(
    answer: str,
    validation: Any,
) -> dict[str, Any]:
    """验证需求收集的用户答案（格式验证）.

    Args:
        answer: 用户输入的答案
        validation: 验证规则（dict 或 ValidationRule 对象）

    Returns:
        包含验证结果的字典
    """
    # 提取验证字段
    field = validation.get("field") if isinstance(validation, dict) else validation.field
    required = validation.get("required") if isinstance(validation, dict) else validation.required
    min_length = (
        validation.get("min_length") if isinstance(validation, dict) else validation.min_length
    )
    max_length = (
        validation.get("max_length") if isinstance(validation, dict) else validation.max_length
    )
    options = validation.get("options") if isinstance(validation, dict) else validation.options
    pattern = validation.get("pattern") if isinstance(validation, dict) else validation.pattern
    help_text = (
        validation.get("help_text") if isinstance(validation, dict) else validation.help_text
    )

    # 检查必填
    if required and not answer.strip():
        return {
            "valid": False,
            "error": f"{field} 是必填项",
        }

    # 如果答案为空且非必填，直接通过
    if not answer.strip():
        return {"valid": True}

    # 检查长度
    if min_length and len(answer) < min_length:
        return {
            "valid": False,
            "error": help_text or f"最少需要 {min_length} 个字符",
        }

    if max_length and len(answer) > max_length:
        return {
            "valid": False,
            "error": help_text or f"最多允许 {max_length} 个字符",
        }

    # 检查选项
    if options:
        normalized_answer = answer.strip().lower()
        valid_options = [opt.lower() for opt in options]
        if normalized_answer not in valid_options:
            return {
                "valid": False,
                "error": f"无效的选项，请选择: {', '.join(options)}",
            }

    # 检查正则表达式
    if pattern:
        if not re.match(pattern, answer.strip()):
            return {
                "valid": False,
                "error": help_text or "格式不正确",
            }

    return {"valid": True}


__all__ = [
    "validate_requirement_answer",
]
