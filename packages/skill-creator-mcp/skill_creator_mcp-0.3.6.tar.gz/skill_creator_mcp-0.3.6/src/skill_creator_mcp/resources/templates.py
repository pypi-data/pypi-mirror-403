"""技能模板资源.

提供各种技能类型的模板内容。
"""

from typing import Literal

# 支持的模板类型
TemplateType = Literal["minimal", "tool-based", "workflow-based", "analyzer-based"]

# 模板描述
TEMPLATE_DESCRIPTIONS: dict[TemplateType, str] = {
    "minimal": "最小化技能模板，适用于简单功能。",
    "tool-based": "基于工具的技能模板，适用于封装特定工具或 API。",
    "workflow-based": "基于工作流的技能模板，适用于多步骤任务。",
    "analyzer-based": "基于分析的技能模板，适用于数据分析或代码分析。",
}

# 模板默认工具
TEMPLATE_TOOLS: dict[TemplateType, str] = {
    "minimal": "Read, Write, Edit, Bash",
    "tool-based": "Read, Write, Edit, Bash",
    "workflow-based": "Read, Write, Edit, Bash, Glob, Grep",
    "analyzer-based": "Read, Glob, Grep, Bash",
}

# 模板必需引用文件
TEMPLATE_REFERENCES: dict[TemplateType, list[str]] = {
    "minimal": [],
    "tool-based": ["tool-integration.md", "usage-examples.md"],
    "workflow-based": ["workflow-steps.md", "decision-points.md"],
    "analyzer-based": ["analysis-methods.md", "metrics.md"],
}


def list_templates() -> list[dict[str, str]]:
    """列出所有可用的模板类型.

    Returns:
        模板类型列表，包含名称和描述
    """
    return [{"type": t, "description": TEMPLATE_DESCRIPTIONS[t]} for t in TEMPLATE_DESCRIPTIONS]


def get_template_content(template_type: TemplateType) -> str:
    r"""获取指定模板类型的 SKILL.md 内容.

    Args:
        template_type: 模板类型

    Returns:
        SKILL.md 模板内容
    """
    skill_title = "{{NAME}}"
    description = TEMPLATE_DESCRIPTIONS.get(template_type, TEMPLATE_DESCRIPTIONS["minimal"])
    tools = TEMPLATE_TOOLS.get(template_type, TEMPLATE_TOOLS["minimal"])

    return f"""---
name: {{NAME}}
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


def get_template_references(template_type: TemplateType) -> list[tuple[str, str]]:
    """获取指定模板类型的引用文件内容.

    Args:
        template_type: 模板类型

    Returns:
        (文件名, 内容) 元组列表
    """
    reference_mapping = {
        "tool-based": [
            (
                "tool-integration.md",
                r"""# 工具集成

本文档描述如何集成外部工具或 API。

## 工具清单

- [工具1]：用途描述
- [工具2]：用途描述

## 集成步骤

1. [步骤1]
2. [步骤2]

## 示例代码

\`\`\`python
# 示例代码
\`\`\`
""",
            ),
            (
                "usage-examples.md",
                """# 使用示例

本文档提供各种使用场景的示例。

## 基本用法

[描述基本用法示例]

## 高级用法

[描述高级用法示例]

## 常见问题

### 问题1

**问题描述**：[描述]

**解决方案**：[描述]
""",
            ),
        ],
        "workflow-based": [
            (
                "workflow-steps.md",
                r"""# 工作流步骤

本文档描述技能的工作流程。

## 流程图

\`\`\`
[流程图表示]
\`\`\`

## 步骤说明

### 步骤1：[步骤名称]

- **输入**：[描述]
- **处理**：[描述]
- **输出**：[描述]

### 步骤2：[步骤名称]

[同上]

## 错误处理

- [错误情况1]：[处理方式]
- [错误情况2]：[处理方式]
""",
            ),
            (
                "decision-points.md",
                r"""# 决策点

本文档描述工作流中的决策点。

## 决策树

\`\`\`
[决策树表示]
\`\`\`

## 决策逻辑

### 决策点1：[名称]

- **条件**：[描述]
- **选项A**：[描述]
- **选项B**：[描述]

### 决策点2：[名称]

[同上]

## 默认行为

[描述默认处理逻辑]
""",
            ),
        ],
        "analyzer-based": [
            (
                "analysis-methods.md",
                r"""# 分析方法

本文档描述使用的分析方法。

## 分析维度

1. **[维度1]**：[描述]
2. **[维度2]**：[描述]

## 分析步骤

### 步骤1：数据收集

[描述数据收集方法]

### 步骤2：数据处理

[描述数据处理方法]

### 步骤3：结果解读

[描述结果解读方法]

## 算法说明

\`\`\`python
# 算法伪代码
\`\`\`
""",
            ),
            (
                "metrics.md",
                r"""# 指标

本文档描述分析使用的指标。

## 质量指标

| 指标 | 描述 | 计算方式 |
|------|------|----------|
| [指标1] | [描述] | [计算方式] |
| [指标2] | [描述] | [计算方式] |

## 评分标准

- **优秀**：[标准]
- **良好**：[标准]
- **需改进**：[标准]

## 报告格式

\`\`\`
[报告格式示例]
\`\`\`
""",
            ),
        ],
    }

    return reference_mapping.get(template_type, [])


def get_template_info(template_type: TemplateType) -> dict:
    """获取模板的完整信息.

    Args:
        template_type: 模板类型

    Returns:
        包含模板所有信息的字典
    """
    return {
        "type": template_type,
        "description": TEMPLATE_DESCRIPTIONS.get(template_type, ""),
        "allowed_tools": TEMPLATE_TOOLS.get(template_type, ""),
        "required_references": TEMPLATE_REFERENCES.get(template_type, []),
    }
