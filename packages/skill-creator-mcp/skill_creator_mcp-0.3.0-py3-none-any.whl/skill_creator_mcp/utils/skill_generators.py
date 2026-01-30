"""技能生成辅助函数.

此模块包含用于生成技能目录结构和模板文件的辅助函数。
这些函数被 `init_skill` MCP 工具使用。
"""

from pathlib import Path

from .file_ops import write_file_async


def _generate_skill_md_content(name: str, template: str) -> str:
    """生成 SKILL.md 内容.

    Args:
        name: 技能名称
        template: 模板类型

    Returns:
        SKILL.md 文件内容
    """
    skill_title = name.replace("-", " ").replace("_", " ").title()

    descriptions = {
        "minimal": "最小化技能模板，适用于简单功能。",
        "tool-based": "基于工具的技能模板，适用于封装特定工具或 API。",
        "workflow-based": "基于工作流的技能模板，适用于多步骤任务。",
        "analyzer-based": "基于分析的技能模板，适用于数据分析或代码分析。",
    }

    description = descriptions.get(template, descriptions["minimal"])

    allowed_tools = {
        "minimal": "Read, Write, Edit, Bash",
        "tool-based": "Read, Write, Edit, Bash",
        "workflow-based": "Read, Write, Edit, Bash, Glob, Grep",
        "analyzer-based": "Read, Glob, Grep, Bash",
    }

    tools = allowed_tools.get(template, allowed_tools["minimal"])

    return f"""---
name: {name}
description: |
  {description}

  何时使用：
  - [描述使用场景 1]
  - [描述使用场景 2]

  触发词：[列出触发词]
allowed-tools: {tools}
mcp_servers: []
---

# {skill_title}

## 技能概述

[简要描述这个技能的功能和用途]

## 核心能力

1. **[能力 1]**：[描述]
2. **[能力 2]**：[描述]
3. **[能力 3]**：[描述]

## 使用方法

### 基本用法

[描述基本使用方法]

### 高级用法

[描述高级使用方法]

## 注意事项

- [注意事项 1]
- [注意事项 2]

## 参考资源

- [相关链接 1]
- [相关链接 2]
"""


async def _create_reference_files(skill_dir: Path, template_type: str) -> None:
    """创建引用文件.

    Args:
        skill_dir: 技能目录路径
        template_type: 模板类型
    """
    refs_dir = skill_dir / "references"

    ref_mapping = {
        "tool-based": [
            ("tool-integration.md", "# 工具集成\n\n本文档说明如何将 MCP 工具集成到技能中。\n\n## 工具列表\n\n- `tool_name_1`: 说明工具用途\n- `tool_name_2`: 说明工具用途\n\n## 集成步骤\n\n1. 在 SKILL.md 中声明工具\n2. 在技能代码中调用工具\n3. 处理工具返回结果"),
            ("usage-examples.md", "# 使用示例\n\n本文档提供技能的使用示例。\n\n## 示例 1: 基础用法\n\n```\n用户请求：[描述用户输入]\n\n技能响应：[描述技能处理流程]\n```\n\n## 示例 2: 高级用法\n\n```\n用户请求：[描述复杂场景]\n\n技能响应：[描述处理方式]\n```"),
        ],
        "workflow-based": [
            ("workflow-steps.md", "# 工作流步骤\n\n本文档描述技能的工作流程。\n\n## 流程图\n\n```\n[步骤 1] → [步骤 2] → [步骤 3] → [完成]\n```\n\n## 详细步骤\n\n### 步骤 1: [名称]\n- **输入**: [描述输入]\n- **处理**: [描述处理逻辑]\n- **输出**: [描述输出]\n\n### 步骤 2: [名称]\n..."),
            ("decision-points.md", "# 决策点\n\n本文档描述技能中的关键决策点。\n\n## 决策点 1: [名称]\n\n**条件**: [描述触发条件]\n- **选项 A**: [描述选项及结果]\n- **选项 B**: [描述选项及结果]\n\n**决策依据**: [说明如何做出决策]"),
        ],
        "analyzer-based": [
            ("analysis-methods.md", "# 分析方法\n\n本文档描述技能使用的分析方法。\n\n## 方法 1: [名称]\n\n**目的**: [描述分析目的]\n- **输入**: [描述输入数据]\n- **算法**: [描述分析方法]\n- **输出**: [描述输出结果]\n\n## 方法 2: [名称]\n..."),
            ("metrics.md", "# 指标\n\n本文档定义技能使用的评估指标。\n\n## 准确性指标\n\n- **准确率**: 定义和计算方式\n- **精确率**: 定义和计算方式\n- **召回率**: 定义和计算方式\n\n## 效率指标\n\n- **响应时间**: 定义和目标\n- **资源消耗**: 定义和目标"),
        ],
    }

    refs = ref_mapping.get(template_type, [])

    for filename, content in refs:
        await write_file_async(refs_dir / filename, content)


async def _create_example_scripts(skill_dir: Path) -> None:
    """创建示例脚本.

    Args:
        skill_dir: 技能目录路径
    """
    scripts_dir = skill_dir / "scripts"

    helper_content = '''#!/usr/bin/env python3
"""示例辅助脚本"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="示例辅助脚本")
    parser.add_argument("--option", help="选项说明")
    args = parser.parse_args()

    print(f"执行示例脚本，选项: {args.option}")


if __name__ == "__main__":
    main()
'''
    await write_file_async(scripts_dir / "helper.py", helper_content)

    validate_content = '''#!/usr/bin/env python3
"""技能验证脚本"""

import sys
from pathlib import Path


def validate_skill():
    """验证技能结构"""
    skill_dir = Path(__file__).parent.parent

    required_files = ["SKILL.md"]
    missing_files = []

    for file in required_files:
        if not (skill_dir / file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"缺少必需文件: {', '.join(missing_files)}")
        return False

    print("技能结构验证通过")
    return True


if __name__ == "__main__":
    sys.exit(0 if validate_skill() else 1)
'''
    await write_file_async(scripts_dir / "validate.py", validate_content)


async def _create_example_examples(skill_dir: Path, name: str) -> None:
    """创建使用示例.

    Args:
        skill_dir: 技能目录路径
        name: 技能名称
    """
    examples_dir = skill_dir / "examples"

    skill_title = name.replace("-", " ").replace("_", " ").title()

    example_content = f"""# {skill_title} 使用示例

## 示例 1：基本用法

描述基本使用方法和预期结果。

## 示例 2：高级用法

描述高级使用方法和预期结果。

## 示例 3：错误处理

描述错误情况的处理方式。
"""
    await write_file_async(examples_dir / "basic-usage.md", example_content)
