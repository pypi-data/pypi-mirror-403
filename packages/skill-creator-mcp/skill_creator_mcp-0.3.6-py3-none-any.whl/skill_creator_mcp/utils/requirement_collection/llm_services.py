"""LLM 服务模块（简化版）.

只提供 LLM 调用功能，不包含 Prompt 模板和业务逻辑。
Prompt 模板应放在 Agent-Skill references/ 中。
符合 ADR 001: MCP Server 只提供原子操作，不传递业务知识。
"""

import json
from typing import Any

from fastmcp import Context


async def check_requirement_completeness(
    ctx: Context,
    answers: dict[str, str],
    prompt_template: str | None = None,
) -> dict[str, Any]:
    """使用 LLM 检查需求完整性.

    Args:
        ctx: MCP 上下文
        answers: 已收集的答案
        prompt_template: 自定义Prompt模板（可选，用于特殊场景）。
                        默认使用内置Prompt，保持向后兼容。
                        Prompt模板应在Agent-Skill中定义，符合ADR 001。

    Returns:
        包含完整性检查结果的字典
    """
    try:
        # 使用默认Prompt（向后兼容），或使用Agent-Skill提供的自定义Prompt
        if prompt_template is None:
            prompt_template = """分析以下技能创建需求，判断是否包含所有必要信息：

已收集的信息：
{answers}

必要信息包括：
1. skill_name - 技能名称
2. skill_function - 主要功能
3. use_cases - 使用场景
4. template_type - 模板类型

请返回 JSON 格式，包含：
- complete: bool（是否完整）
- missing_items: list[str]（缺失的信息列表）
- suggestions: list[str]（补充建议列表）

只返回 JSON，不要其他内容。"""

        prompt = prompt_template.format(
            answers=json.dumps(answers, indent=2, ensure_ascii=False)
        )

        result = await ctx.sample(
            messages=prompt,
            system_prompt="你是一个技能创建顾问，负责评估需求的完整性。",
            temperature=0.3,
        )

        if result.text:
            try:
                # 提取 JSON 部分
                json_start = result.text.find("{")
                json_end = result.text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = result.text[json_start:json_end]
                    parsed = json.loads(json_str)
                    return parsed  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass

        # 默认返回（如果 LLM 解析失败）
        required_keys = ["skill_name", "skill_function", "use_cases", "template_type"]
        missing = [k for k in required_keys if k not in answers or not answers[k]]

        return {
            "complete": len(missing) == 0,
            "missing_items": missing,
            "suggestions": [] if len(missing) == 0 else ["请补充缺失的关键信息"],
        }

    except Exception as e:
        # 如果 LLM 调用失败，进行简单的完整性检查
        required_keys = ["skill_name", "skill_function", "use_cases", "template_type"]
        missing = [k for k in required_keys if k not in answers or not answers[k]]

        return {
            "complete": len(missing) == 0,
            "missing_items": missing,
            "suggestions": ["请补充缺失的关键信息"] if missing else [],
            "error": str(e),
        }


__all__ = [
    "check_requirement_completeness",
]
