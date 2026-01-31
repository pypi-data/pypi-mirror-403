"""创建技能 Prompt 模板."""

from typing import Final

# 创建技能的 Prompt 模板
CREATE_SKILL_PROMPT: Final = """你是一个专业的 Agent-Skill 开发助手。

## 任务

创建一个新的 Agent-Skill，名称：{{name}}，模板类型：{{template}}。

## 要求

### 1. 技能命名规范
- 使用小写字母、数字、连字符
- 长度 1-64 字符
- 不以连字符开头或结尾
- 示例：`code-analyzer`, `file-helper`, `api-client`

### 2. SKILL.md 结构

必需的 YAML frontmatter 字段：
```yaml
---
name: skill-name
description: |
  技能描述（1-2 句话）
  何时使用：
  - 场景1
  - 场景2
  触发词：关键词列表
allowed-tools: Read, Write, Edit
mcp_servers: []
---
```

### 3. 目录结构

必需目录：
- `references/` - 参考文档
- `examples/` - 使用示例
- `scripts/` - 辅助脚本
- `.claude/` - Claude 配置

### 4. 内容要求

- SKILL.md 应该 ≤ 150 行
- 详细内容放到 references/ 目录
- 提供 1-3 个核心能力描述
- 包含基本和高级用法示例

### 5. 模板特定要求

{{template_requirements}}

## 输出格式

请按以下步骤创建技能：

1. 确认技能名称符合规范
2. 根据 {{template}} 模板创建目录结构
3. 生成 SKILL.md 内容
4. 创建必需的参考文件

完成时请确认：
- [ ] SKILL.md ≤ 150 行
- [ ] 所有必需目录存在
- [ ] references/ 包含模板必需的文件
"""


def get_create_skill_prompt(name: str, template: str = "minimal") -> str:
    """
    获取创建技能的 Prompt 模板.

    ## 完整模板内容

    这个Prompt模板指导AI创建符合规范的Agent-Skill，包含：

    1. **任务说明**: 创建指定名称和类型的技能
    2. **命名规范**: 小写字母、数字、连字符，1-64字符
    3. **YAML frontmatter**: 必需字段和格式
    4. **目录结构**: references/, examples/, scripts/, .claude/
    5. **内容要求**: SKILL.md ≤150行，详细内容在references/
    6. **模板特定要求**: 根据minimal/tool-based/workflow-based/analyzer-based不同而不同

    ## 参数说明
    - name: 技能名称（必须符合命名规范）
    - template: 模板类型（minimal/tool-based/workflow-based/analyzer-based）

    ## 返回值
    返回完整的Prompt模板字符串，可直接用于LLM生成技能内容

    ## 使用示例
    ```python
    prompt = get_create_skill_prompt("my-skill", "tool-based")
    # 返回包含tool-based模板特定要求的完整Prompt
    ```

    Args:
        name: 技能名称
        template: 模板类型

    Returns:
        Prompt 模板内容
    """
    template_requirements_map = {
        "minimal": """
**minimal 模板**：
- 最简单的技能结构
- 无额外的参考文件要求
- 适用于简单工具封装
""",
        "tool-based": """
**tool-based 模板**：
- 必需参考文件：
  - `references/tool-integration.md` - 工具集成说明
  - `references/usage-examples.md` - 使用示例
- 适用于封装特定工具或 API
""",
        "workflow-based": """
**workflow-based 模板**：
- 必需参考文件：
  - `references/workflow-steps.md` - 工作流步骤
  - `references/decision-points.md` - 决策点说明
- 适用于多步骤任务流程
""",
        "analyzer-based": """
**analyzer-based 模板**：
- 必需参考文件：
  - `references/analysis-methods.md` - 分析方法
  - `references/metrics.md` - 指标说明
- 适用于数据分析或代码分析
""",
    }

    template_requirements = template_requirements_map.get(
        template, "\n**未知模板类型**，请使用：minimal, tool-based, workflow-based, analyzer-based"
    )

    result = CREATE_SKILL_PROMPT.replace("{{name}}", name)
    result = result.replace("{{template}}", template)
    result = result.replace("{{template_requirements}}", template_requirements)
    return result
