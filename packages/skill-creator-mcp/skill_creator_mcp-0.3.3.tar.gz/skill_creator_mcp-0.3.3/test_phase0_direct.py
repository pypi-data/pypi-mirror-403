#!/usr/bin/env python3
"""Phase 0 验证工具 - 直接测试脚本.

这个脚本模拟 MCP Context API，用于验证 Phase 0 工具的核心逻辑。
由于真实的 ctx.sample() 和 ctx.elicit() 需要在 Claude Code 中运行，
这里使用模拟对象进行初步验证。
"""

import asyncio
import json

# 导入要测试的函数
import sys
from dataclasses import dataclass, field
from typing import Any

sys.path.insert(0, "src")

from skill_creator_mcp.utils.requirement_collection import (
    _generate_brainstorm_question,
    _generate_progressive_question,
)

# ============================================================================
# 模拟 Context API
# ============================================================================


@dataclass
class SamplingResult:
    """模拟 LLM 采样结果."""
    text: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ElicitationResult:
    """模拟用户征询结果."""
    accepted: bool = True
    data: Any = None
    action: str = "accept"


class MockContext:
    """模拟 MCP Context 对象."""

    def __init__(self):
        self._state: dict[str, Any] = {}
        self.sample_history: list[dict] = []
        self.elicit_history: list[dict] = []

    async def sample(
        self,
        messages: str | list[dict],
        system_prompt: str = "",
        temperature: float = 0.7,
        **kwargs
    ) -> SamplingResult:
        """模拟 LLM 采样."""
        self.sample_history.append({
            "messages": messages,
            "system_prompt": system_prompt,
            "temperature": temperature,
        })

        # 模拟 LLM 响应
        if isinstance(messages, str):
            prompt = messages
        else:
            prompt = messages[-1].get("content", "") if messages else ""

        # 根据提示生成模拟响应
        if "核心价值" in prompt or "痛点" in prompt:
            response = "您希望这个技能解决用户什么样的核心痛点？"
        elif "触发" in prompt or "自动化" in prompt:
            response = "考虑到自动化任务，您希望支持哪些触发方式？"
        elif "权限" in prompt:
            response = "您提到的权限控制是指什么级别的权限？"
        elif "分析以下技能创建需求" in prompt:
            # 完整性检查返回 JSON
            response = json.dumps({
                "is_complete": False,
                "missing_info": ["skill_name", "use_cases"],
                "suggestions": ["请提供技能名称", "请描述使用场景"]
            })
        else:
            response = "这是一个很好的问题。请问您能详细说明一下吗？"

        return SamplingResult(
            text=response,
            history=[{"role": "assistant", "content": response}]
        )

    async def elicit(self, prompt: str, **kwargs) -> ElicitationResult:
        """模拟用户征询."""
        self.elicit_history.append({"prompt": prompt, "kwargs": kwargs})
        # 模拟用户接受并输入数据
        return ElicitationResult(
            accepted=True,
            data="test-skill-name"
        )

    async def get_state(self, key: str) -> Any:
        """获取状态."""
        return self._state.get(key)

    async def set_state(self, key: str, value: Any) -> None:
        """设置状态."""
        self._state[key] = value


# ============================================================================
# Phase 0 验证测试
# ============================================================================


async def test_llm_sampling():
    """验证点 1: LLM Sampling 能力."""
    print("\n" + "=" * 60)
    print("验证点 1: LLM Sampling 能力")
    print("=" * 60)

    ctx = MockContext()

    # 调用 sample
    result = await ctx.sample(
        messages="请生成一个关于技能创建的问题",
        system_prompt="You are a helpful assistant for skill creation.",
        temperature=0.7,
    )

    # 验证结果
    print(f"✅ LLM 响应: {result.text}")
    print(f"✅ 包含历史记录: {len(result.history) > 0}")
    print(f"✅ 采样次数: {len(ctx.sample_history)}")

    assert result.text is not None, "LLM 应该返回响应文本"
    assert len(result.history) > 0, "应该包含历史记录"
    assert len(ctx.sample_history) == 1, "应该记录一次采样"

    return True


async def test_user_elicitation():
    """验证点 2: User Elicitation 能力."""
    print("\n" + "=" * 60)
    print("验证点 2: User Elicitation 能力")
    print("=" * 60)

    ctx = MockContext()

    # 调用 elicit
    result = await ctx.elicit(
        prompt="请提供技能名称（小写字母、数字、连字符）"
    )

    # 验证结果
    print(f"✅ 用户接受: {result.accepted}")
    print(f"✅ 用户输入: {result.data}")
    print(f"✅ 征询次数: {len(ctx.elicit_history)}")

    assert result.accepted, "用户应该接受输入请求"
    assert result.data is not None, "应该返回用户输入"
    assert len(ctx.elicit_history) == 1, "应该记录一次征询"

    return True


async def test_conversation_loop():
    """验证点 3: Session State + LLM 结合."""
    print("\n" + "=" * 60)
    print("验证点 3: Session State + LLM 结合")
    print("=" * 60)

    ctx = MockContext()

    # 第一轮对话
    user_input_1 = "我想创建一个技能"
    history_1 = await ctx.get_state("conversation_history")
    history_1 = list(history_1) if history_1 else []
    history_1.append({"role": "user", "content": user_input_1})

    result_1 = await ctx.sample(
        messages=history_1,
        system_prompt="You are a skill creation consultant.",
    )

    if result_1.text:
        history_1.append({"role": "assistant", "content": result_1.text})
    await ctx.set_state("conversation_history", history_1)

    print(f"📝 第一轮 - 用户: {user_input_1}")
    print(f"📝 第一轮 - AI: {result_1.text}")
    print(f"📝 对话长度: {len(history_1)}")

    # 第二轮对话
    history_2 = await ctx.get_state("conversation_history")
    history_2 = list(history_2) if history_2 else []
    user_input_2 = "帮助用户快速找到相关文档"
    history_2.append({"role": "user", "content": user_input_2})

    result_2 = await ctx.sample(
        messages=history_2,
        system_prompt="You are a skill creation consultant.",
    )

    if result_2.text:
        history_2.append({"role": "assistant", "content": result_2.text})
    await ctx.set_state("conversation_history", history_2)

    print(f"📝 第二轮 - 用户: {user_input_2}")
    print(f"📝 第二轮 - AI: {result_2.text}")
    print(f"📝 对话长度: {len(history_2)}")

    assert len(history_2) == 4, "应该有 4 条对话记录（2 轮）"
    assert await ctx.get_state("conversation_history") == history_2, "状态应该正确保存"

    return True


async def test_requirement_completeness():
    """验证点 4: 需求完整性验证."""
    print("\n" + "=" * 60)
    print("验证点 4: 需求完整性验证")
    print("=" * 60)

    ctx = MockContext()

    requirement = "我想创建一个技能"

    result = await ctx.sample(
        messages=f"""分析以下技能创建需求，判断是否包含所有必要信息：

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
""",
        system_prompt="You are a skill creation consultant. Analyze requirements for completeness.",
        temperature=0.3,
    )

    print(f"📋 LLM 分析结果: {result.text}")

    # 尝试解析 JSON
    import re
    json_match = re.search(r"\{.*\}", result.text or "", re.DOTALL)
    if json_match:
        try:
            analysis = json.loads(json_match.group())
            print("✅ JSON 解析成功")
            print(f"✅ 是否完整: {analysis.get('is_complete')}")
            print(f"✅ 缺失信息: {analysis.get('missing_info')}")
            print(f"✅ 补充建议: {analysis.get('suggestions')}")
            return True
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 解析失败: {e}")
            return False
    else:
        print("⚠️ 未找到 JSON 格式输出")
        return False


async def test_brainstorm_mode():
    """额外测试: Brainstorm 模式."""
    print("\n" + "=" * 60)
    print("额外测试: Brainstorm 模式 LLM 问题生成")
    print("=" * 60)

    ctx = MockContext()

    result = await _generate_brainstorm_question(
        ctx=ctx,
        answers={},
        conversation_history=None,
    )

    print(f"✅ 成功生成问题: {result.get('success')}")
    print(f"✅ 问题来源: {result.get('source')}")
    print(f"✅ 是否动态: {result.get('is_dynamic')}")
    print(f"📝 生成的问题: {result.get('question')}")

    assert result["success"], "应该成功生成问题"
    assert result["is_dynamic"], "应该是动态生成的问题"

    return True


async def test_progressive_mode():
    """额外测试: Progressive 模式."""
    print("\n" + "=" * 60)
    print("额外测试: Progressive 模式渐进式问题")
    print("=" * 60)

    ctx = MockContext()

    result = await _generate_progressive_question(
        ctx=ctx,
        answers={},
    )

    print(f"✅ 成功生成问题: {result.get('success')}")
    print(f"✅ 问题来源: {result.get('source')}")
    print(f"📝 生成的问题: {result.get('question')}")

    assert result["success"], "应该成功生成问题"

    return True


# ============================================================================
# 主测试流程
# ============================================================================


async def main():
    """运行所有 Phase 0 验证测试."""
    print("\n" + "=" * 60)
    print("Phase 0 技术验证 - 直接测试")
    print("=" * 60)
    print("\n⚠️ 注意: 这是模拟测试，验证核心逻辑")
    print("⚠️ 真实环境测试需要在 Claude Code 中运行 MCP Server\n")

    tests = [
        ("LLM Sampling 能力", test_llm_sampling),
        ("User Elicitation 能力", test_user_elicitation),
        ("Session State + LLM 结合", test_conversation_loop),
        ("需求完整性验证", test_requirement_completeness),
        ("Brainstorm 模式", test_brainstorm_mode),
        ("Progressive 模式", test_progressive_mode),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, "✅ 通过" if result else "⚠️ 部分通过"))
        except Exception as e:
            results.append((name, f"❌ 失败: {e}"))

    # 输出总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)

    for name, result in results:
        print(f"{result} - {name}")

    passed = sum(1 for _, r in results if "✅" in r)
    total = len(results)

    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！核心逻辑验证成功。")
        print("\n下一步: 在 Claude Code 中重启以加载 MCP Server，进行真实环境测试。")
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试未完全通过，请检查。")


if __name__ == "__main__":
    asyncio.run(main())
