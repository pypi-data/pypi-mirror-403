#!/usr/bin/env python3
"""开发工具脚本.

此脚本包含Phase 0验证工具，用于开发环境测试MCP Server的FastMCP Context API功能。

这些工具仅在开发环境有用，不应作为MCP工具暴露给普通用户：
- check_client_capabilities: 检测MCP客户端能力
- test_llm_sampling: 测试 ctx.sample() API
- test_user_elicitation: 测试 ctx.elicit() API
- test_conversation_loop: 测试会话状态管理
- test_requirement_completeness: 测试需求完整性判断

使用方法:
    python -m scripts.dev-tools check-capabilities
    python -m scripts.dev-tools test-sampling "测试提示"
    python -m scripts.dev-tools test-elicit "请提供输入"
    python -m scripts.dev-tools test-conversation "用户输入"
    python -m scripts.dev-tools test-completeness "需求描述"

注意：这些工具需要真实的MCP Context才能运行。
直接运行此脚本将仅输出使用说明。
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def print_usage():
    """打印使用说明."""
    print("""
开发工具脚本 - Phase 0 验证工具
================================

这些工具用于开发环境测试MCP Server的FastMCP Context API功能。

可用命令:
    check-capabilities     检测MCP客户端能力支持
    test-sampling          测试 LLM Sampling 能力
    test-elicit           测试用户征询能力
    test-conversation     测试对话循环和状态管理
    test-completeness     测试需求完整性判断

使用方法:
    python -m scripts.dev-tools <command> [args]

示例:
    python -m scripts.dev-tools check-capabilities
    python -m scripts.dev-tools test-sampling "测试提示"
    python -m scripts.dev-tools test-elicit "请提供技能名称"
    python -m scripts.dev-tools test-conversation "用户输入"
    python -m scripts.dev-tools test-completeness "创建一个新技能"

注意:
    这些工具需要真实的MCP Context才能运行。
    它们仅在开发环境有用，不应作为MCP工具暴露给普通用户。

相关文档:
    - 计划: .claude/plans/archive/ (Phase 0 验证计划)
    - 测试: tests/test_utils/test_testing.py
""")


def main():
    """主函数."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    # 这些命令需要在MCP Server上下文中运行
    # 这里仅提供命令接口定义，实际功能在MCP Server中实现

    if command == "check-capabilities":
        print("检测MCP客户端能力支持")
        print("注意: 此功能需要MCP Context，请在MCP Server中使用")
        print("相关工具: check_client_capabilities_impl (utils/capability_detection.py)")

    elif command == "test-sampling":
        prompt = sys.argv[2] if len(sys.argv) > 2 else "测试提示"
        print(f"测试 LLM Sampling 能力: {prompt}")
        print("注意: 此功能需要MCP Context，请在MCP Server中使用")
        print("相关工具: test_llm_sampling_impl (utils/testing.py)")

    elif command == "test-elicit":
        prompt = sys.argv[2] if len(sys.argv) > 2 else "请提供技能名称"
        print(f"测试用户征询能力: {prompt}")
        print("注意: 此功能需要MCP Context，请在MCP Server中使用")
        print("相关工具: test_user_elicitation_impl (utils/testing.py)")

    elif command == "test-conversation":
        user_input = sys.argv[2] if len(sys.argv) > 2 else "用户输入"
        print(f"测试对话循环: {user_input}")
        print("注意: 此功能需要MCP Context，请在MCP Server中使用")
        print("相关工具: test_conversation_loop_impl (utils/testing.py)")

    elif command == "test-completeness":
        requirement = sys.argv[2] if len(sys.argv) > 2 else "创建一个新技能"
        print(f"测试需求完整性判断: {requirement}")
        print("注意: 此功能需要MCP Context，请在MCP Server中使用")
        print("相关工具: test_requirement_completeness_impl (utils/testing.py)")

    else:
        print(f"未知命令: {command}")
        print()
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
