"""验证技能 Prompt 模板."""

from typing import Final

# 验证技能的 Prompt 模板
VALIDATE_SKILL_PROMPT: Final = """你是一个专业的 Agent-Skill 质量审核专家。

## 任务

验证 Agent-Skill：{{skill_path}} 的结构和内容是否符合规范。

## 验证清单

### 1. 命名验证
- [ ] 技能名称符合规范（小写字母、数字、连字符）
- [ ] 目录名与 SKILL.md 中的 name 字段一致

### 2. 结构验证
- [ ] 必需文件存在：SKILL.md
- [ ] 必需目录存在：references/, examples/, scripts/, .claude/

### 3. 内容验证
- [ ] SKILL.md 包含有效的 YAML frontmatter
- [ ] 必需字段存在：name, description, allowed-tools
- [ ] description 包含：功能描述、使用场景、触发词

### 4. 模板特定验证
{{template_requirements}}

### 5. 质量验证
- [ ] SKILL.md 行数 ≤ 150
- [ ] 核心能力描述清晰
- [ ] 使用方法有示例
- [ ] 注意事项已列出

## 验证标准

**通过标准**：
- 所有 P0 检查项通过
- P1 检查项最多 1 个警告
- P2 检查项可忽略

**失败标准**：
- 任何 P0 检查项失败
- 超过 3 个 P1 检查项失败

## 输出格式

请按以下格式输出验证结果：

```markdown
# 验证结果

## 总体评估
[通过 / 失败]

## 检查结果

### 命名验证
- [x] 技能名称符合规范
- [ ] 目录名与 name 字段一致

### 结构验证
- [x] 必需文件存在
- [ ] 必需目录存在

### 内容验证
- [x] YAML frontmatter 有效
- [x] 必需字段存在

## 发现的问题

### 错误 (Errors)
[列出所有必须修复的问题]

### 警告 (Warnings)
[列出建议修复的问题]

## 改进建议
[提供具体的改进建议]
```
"""


def get_validate_skill_prompt(skill_path: str, template_type: str | None = None) -> str:
    """
    获取验证技能的 Prompt 模板.

    ## 完整模板内容

    这个Prompt模板指导AI全面验证Agent-Skill的合规性，包含：

    1. **命名验证**: 检查技能名称规范和一致性
    2. **结构验证**: 验证必需文件和目录存在
    3. **内容验证**: 检查YAML frontmatter和必需字段
    4. **模板特定验证**: 根据模板类型检查特定要求
    5. **质量验证**: 评估SKILL.md长度、清晰度、示例完整性
    6. **验证标准**: 明确的通过/失败标准
    7. **输出格式**: 结构化的验证结果报告

    ## 参数说明
    - skill_path: 要验证的技能目录路径
    - template_type: 模板类型（可选），用于模板特定验证

    ## 返回值
    返回完整的验证Prompt，指导AI生成详细的验证报告

    ## 验证标准
    - **通过**: 所有P0项通过，P1项最多1个警告
    - **失败**: 任何P0项失败，或超过3个P1项失败

    ## 使用示例
    ```python
    prompt = get_validate_skill_prompt("/path/to/skill", "tool-based")
    # 返回包含tool-based模板特定验证要求的Prompt
    ```

    Args:
        skill_path: 技能目录路径
        template_type: 模板类型（可选）

    Returns:
        Prompt 模板内容
    """
    template_requirements = ""

    if template_type:
        template_req_map = {
            "minimal": "**minimal 模板**：无额外要求",
            "tool-based": """
**tool-based 模板**：
- 必需文件：tool-integration.md, usage-examples.md
""",
            "workflow-based": """
**workflow-based 模板**：
- 必需文件：workflow-steps.md, decision-points.md
""",
            "analyzer-based": """
**analyzer-based 模板**：
- 必需文件：analysis-methods.md, metrics.md
""",
        }
        template_requirements = template_req_map.get(
            template_type, f"\n**{template_type} 模板**：使用标准模板要求"
        )

    result = VALIDATE_SKILL_PROMPT.replace("{{skill_path}}", skill_path)
    result = result.replace("{{template_requirements}}", template_requirements)
    return result
