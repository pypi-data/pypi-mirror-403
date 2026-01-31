"""需求收集问题获取工具模块.

提供原子化的问题获取工具，不包含工作流逻辑。
符合 ADR 001: MCP Server 只提供原子操作 + 文件I/O + 数据验证。
"""

import json
import re
from typing import Any

from fastmcp import Context


async def get_static_question(
    ctx: Context,
    mode: str,
    step_index: int,
) -> dict[str, Any]:
    """
    获取静态问题（用于 basic/complete 模式）.

    这是一个原子操作工具，只负责获取预定义的问题。
    不包含循环逻辑，循环由 Agent-Skill 编排。

    Args:
        ctx: MCP 上下文
        mode: 收集模式（basic/complete）
        step_index: 步骤索引（从0开始）

    Returns:
        包含问题信息的字典: {
            "question_key": str,
            "question_text": str,
            "validation": dict,
            "placeholder": str
        }
    """
    try:
        # 获取预定义步骤
        from ..constants import BASIC_REQUIREMENT_STEPS, COMPLETE_REQUIREMENT_STEPS

        all_steps = BASIC_REQUIREMENT_STEPS.copy()
        if mode == "complete":
            all_steps.extend(COMPLETE_REQUIREMENT_STEPS)

        # 检查步骤索引
        if step_index < 0 or step_index >= len(all_steps):
            return {
                "success": False,
                "error": f"无效的步骤索引: {step_index}",
                "valid_range": f"0-{len(all_steps) - 1}",
            }

        # 获取问题数据
        step_data = all_steps[step_index]

        return {
            "success": True,
            "question_key": step_data["key"],
            "question_text": step_data["prompt"],
            "validation": step_data["validation"],
            "placeholder": step_data.get("title", ""),
            "step_index": step_index,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"获取静态问题失败: {e}",
            "error_type": "internal_error",
        }


async def generate_dynamic_question(
    ctx: Context,
    mode: str,
    answers: dict[str, str],
    conversation_history: list[dict] | None = None,
    prompt_template: str | None = None,
) -> dict[str, Any]:
    """
    生成动态问题（用于 brainstorm/progressive 模式）.

    这是一个原子操作工具，使用 LLM 生成下一个问题。
    不包含循环逻辑，循环由 Agent-Skill 编排。

    Args:
        ctx: MCP 上下文
        mode: 收集模式（brainstorm/progressive）
        answers: 已收集的答案
        conversation_history: 对话历史（用于 brainstorm 模式）
        prompt_template: 自定义Prompt模板（可选，用于特殊场景）。
                        Prompt模板应由Agent-Skill提供，符合ADR 001架构原则。

    Returns:
        包含生成问题的字典: {
            "question_key": str,
            "question_text": str,
            "is_llm_generated": bool
        }
    """
    try:
        if mode == "brainstorm":
            return await _generate_brainstorm_question(ctx, answers, conversation_history or [], prompt_template)
        elif mode == "progressive":
            return await _generate_progressive_question(ctx, answers)
        else:
            return {
                "success": False,
                "error": f"动态模式只支持 brainstorm 和 progressive，收到: {mode}",
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"生成动态问题失败: {e}",
            "error_type": "internal_error",
        }


async def _generate_brainstorm_question(
    ctx: Context,
    answers: dict[str, str],
    conversation_history: list[dict[str, str]],
    prompt_template: str | None = None,
) -> dict[str, Any]:
    """使用 LLM 为 brainstorm 模式生成探索性问题.

    Args:
        ctx: MCP 上下文
        answers: 已收集的答案
        conversation_history: 对话历史
        prompt_template: 自定义Prompt模板（可选，用于特殊场景）。
                        Prompt模板应由Agent-Skill提供，符合ADR 001架构原则。
    """
    try:
        # 构建上下文
        context_parts = []
        if answers:
            context_parts.append("已收集的信息:")
            for key, value in answers.items():
                context_parts.append(f"- {key}: {value}")

        if conversation_history:
            context_parts.append("\n之前的对话:")
            for msg in conversation_history[-4:]:  # 只保留最近4条
                context_parts.append(f"{msg.get('role', '')}: {msg.get('content', '')}")

        context = "\n".join(context_parts) if context_parts else "这是对话的开始。"

        # 使用默认Prompt（向后兼容），或使用Agent-Skill提供的自定义Prompt
        if prompt_template is None:
            prompt_template = """你是一个技能创建顾问，正在帮助用户通过头脑风暴方式探索技能需求。

{context}

请生成一个开放性的探索性问题，帮助用户深入思考他们的技能需求。问题应该：
1. 基于已收集的信息进行深入
2. 探索用户可能未曾考虑的角度
3. 鼓励创造性思考
4. 避免重复已问过的内容

请只返回问题文本，不要其他内容。"""

        # 生成探索性问题
        prompt = prompt_template.format(context=context)

        result = await ctx.sample(
            messages=prompt,
            system_prompt="You are a creative skill development consultant specializing in brainstorming and exploration.",
            temperature=0.8,
        )

        question = result.text.strip() if result.text else "请描述您希望这个技能实现什么独特价值？"

        return {
            "success": True,
            "question_key": f"brainstorm_{len(answers)}",
            "question_text": question,
            "is_llm_generated": True,
        }

    except Exception as e:
        # 降级到预定义问题
        fallback_questions = [
            "这个技能的核心价值主张是什么？",
            "它与现有解决方案有什么不同？",
            "用户最痛的场景是什么？",
            "您希望用户使用后有什么感受？",
        ]
        index = min(len(answers), len(fallback_questions) - 1)

        return {
            "success": True,
            "question_key": f"brainstorm_{len(answers)}",
            "question_text": fallback_questions[index],
            "is_llm_generated": False,
            "fallback": True,
            "error": str(e),
        }


async def _generate_progressive_question(
    ctx: Context,
    answers: dict[str, str],
) -> dict[str, Any]:
    """使用 LLM 为 progressive 模式生成针对性的下一个问题."""
    try:
        # 分析已收集的答案，确定下一个最相关的问题
        context = json.dumps(answers, indent=2, ensure_ascii=False)

        prompt = f"""分析以下已收集的技能需求信息，确定下一个应该询问的最相关问题。

已收集的信息：
{context}

可选问题类型（按优先级排序）：
1. 如果缺少 skill_name，询问技能名称
2. 如果缺少 skill_function，询问主要功能
3. 如果缺少 use_cases，询问使用场景
4. 如果缺少 template_type，询问模板类型
5. 如果基本信息齐全，询问更深入的问题（target_users, tech_stack 等）

请返回 JSON 格式：
{{
    "next_question": "具体的问题文本",
    "question_key": "问题标识（如 skill_name, skill_function 等）",
    "reasoning": "选择这个问题的原因"
}}"""

        result = await ctx.sample(
            messages=prompt,
            system_prompt="You are a skill requirements analyst. Determine the most relevant next question based on collected information.",
            temperature=0.3,
        )

        # 尝试解析 JSON
        json_match = re.search(r"\{.*\}", result.text or "", re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return {
                    "success": True,
                    "question_key": parsed.get("question_key", "follow_up"),
                    "question_text": parsed.get("next_question", "请提供更多关于技能功能的细节？"),
                    "is_llm_generated": True,
                }
            except json.JSONDecodeError:
                pass

        # 降级：根据答案数量选择基础问题
        basic_questions = [
            ("skill_name", "请提供技能名称（小写字母、数字、连字符）"),
            ("skill_function", "请描述这个技能的主要功能"),
            ("use_cases", "请描述这个技能的使用场景"),
            ("template_type", "选择技能模板类型：minimal、tool-based、workflow-based、analyzer-based"),
        ]

        index = min(len(answers), len(basic_questions) - 1)
        key, question = basic_questions[index]

        return {
            "success": True,
            "question_key": key,
            "question_text": question,
            "is_llm_generated": False,
            "fallback": True,
        }

    except Exception as e:
        # 降级到基础问题
        basic_questions = [
            ("skill_name", "请提供技能名称（小写字母、数字、连字符）"),
            ("skill_function", "请描述这个技能的主要功能"),
            ("use_cases", "请描述这个技能的使用场景"),
            ("template_type", "选择技能模板类型：minimal、tool-based、workflow-based、analyzer-based"),
        ]

        index = min(len(answers), len(basic_questions) - 1)
        key, question = basic_questions[index]

        return {
            "success": True,
            "question_key": key,
            "question_text": question,
            "is_llm_generated": False,
            "fallback": True,
            "error": str(e),
        }


__all__ = [
    "get_static_question",
    "generate_dynamic_question",
]
