"""验证规则资源.

提供 Agent-Skills 的验证规则和标准。
"""

from typing import Final

# 验证规则内容
VALIDATION_RULES_CONTENT: Final = """# Agent-Skills 验证规则

## 1. 命名验证规则

### 1.1 技能名称格式
- **正则表达式**: `^[a-z][a-z0-9-]*[a-z0-9]$`
- **长度限制**: 1-64 字符
- **允许字符**: 小写字母、数字、连字符
- **禁止模式**:
  - 不能以连字符开头或结尾
  - 不能有连续的连字符
  - 不能使用大写字母
  - 不能使用下划线

**有效示例**:
- `code-analyzer`
- `file-helper`
- `api-client-v2`

**无效示例**:
- `CodeAnalyzer` (大写字母)
- `_helper` (以下划线开头)
- `test--name` (连续连字符)
- `-prefix` (以连字符开头)

### 1.2 目录名称一致性
- 目录名必须与 SKILL.md 中的 `name` 字段完全一致
- 验证函数会检查此匹配

## 2. 结构验证规则

### 2.1 必需文件
| 文件 | 必需 | 描述 |
|------|------|------|
| `SKILL.md` | ✅ | 技能主文档 |

### 2.2 必需目录
| 目录 | 必需 | 描述 |
|------|------|------|
| `references/` | ✅ | 参考文档 |
| `examples/` | ✅ | 使用示例 |
| `scripts/` | ✅ | 辅助脚本 |
| `.claude/` | ✅ | Claude 配置 |

### 2.3 可选目录
| 目录 | 描述 |
|------|------|
| `src/` | 源代码（如果需要） |
| `tests/` | 测试代码 |

## 3. 内容验证规则

### 3.1 SKILL.md YAML Frontmatter
必需字段：
```yaml
---
name: skill-name              # 必需，符合命名规范
description: |               # 必需，多行描述
  技能描述内容
allowed-tools: Read, Write    # 必需，逗号分隔的列表
mcp_servers: []              # 可选，MCP 服务器列表
template: minimal            # 可选，模板类型
---
```

### 3.2 描述字段要求
- 至少包含：功能描述、使用场景、触发词
- 推荐格式：
  ```yaml
  description: |
    [一句话功能描述]

    何时使用：
    - [场景1]
    - [场景2]

    触发词：[关键词1, 关键词2]
  ```

### 3.3 allowed-tools 验证
有效工具列表：
- `Read` - 读取文件
- `Write` - 写入文件
- `Edit` - 编辑文件
- `Bash` - 执行命令
- `Glob` - 文件匹配
- `Grep` - 内容搜索
- `GlobDirectoryTree` - 目录遍历

## 4. 模板特定验证规则

### 4.1 minimal 模板
- 无额外要求
- 适用于简单技能

### 4.2 tool-based 模板
必需引用文件：
- `references/tool-integration.md` - 工具集成说明
- `references/usage-examples.md` - 使用示例

### 4.3 workflow-based 模板
必需引用文件：
- `references/workflow-steps.md` - 工作流步骤
- `references/decision-points.md` - 决策点说明

### 4.4 analyzer-based 模板
必需引用文件：
- `references/analysis-methods.md` - 分析方法
- `references/metrics.md` - 指标说明

## 5. 质量验证规则

### 5.1 文档长度
- SKILL.md 应该 ≤ 150 行
- 超过时应考虑拆分到 references/

### 5.2 文档完整性
检查项：
- [ ] 技能概述清晰
- [ ] 核心能力列表完整
- [ ] 使用方法有示例
- [ ] 注意事项已列出
- [ ] 参考资源有效

### 5.3 示例可运行性
- examples/ 中的示例应该可以实际运行
- 包含预期输出

## 6. 验证优先级

| 优先级 | 检查项 | 描述 |
|--------|--------|------|
| P0 | 必需文件/目录存在 | 基础结构检查 |
| P0 | 命名规范 | 名称格式正确 |
| P0 | YAML frontmatter 有效性 | 可解析且包含必需字段 |
| P1 | 模板特定要求 | 根据模板类型检查 |
| P2 | 内容质量 | 描述完整性、示例可运行性 |

## 7. 验证命令

### 7.1 使用 validate_skill 工具
```python
await validate_skill(
    skill_path="/path/to/skill",
    check_structure=True,
    check_content=True,
)
```

### 7.2 验证输出格式
```json
{
  "success": true,
  "valid": true,
  "skill_path": "/path/to/skill",
  "skill_name": "skill-name",
  "template_type": "tool-based",
  "errors": [],
  "warnings": [],
  "checks": {
    "structure": true,
    "naming": true,
    "content": true,
    "template_requirements": true
  },
  "message": "验证通过"
}
```

## 8. 常见验证错误

### 8.1 结构错误
- `缺少必需文件: SKILL.md`
- `缺少必需目录: references`
- `目录不存在: /path/to/skill`

### 8.2 命名错误
- `目录名不符合规范: Test_Skill`
- `name 字段与目录名不一致`

### 8.3 内容错误
- `SKILL.md 文件不存在`
- `缺少 YAML frontmatter`
- `缺少必需字段: description`
- `缺少必需字段: allowed-tools`

### 8.4 模板特定错误
- `缺少必需文件: references/tool-integration.md`
- `缺少必需文件: references/workflow-steps.md`
"""


def get_validation_rules() -> str:
    """获取验证规则文档内容.

    Returns:
        验证规则 Markdown 内容
    """
    return VALIDATION_RULES_CONTENT


def get_validation_rules_summary() -> dict:
    """获取验证规则摘要.

    Returns:
        包含关键规则的字典
    """
    return {
        "naming": {
            "pattern": r"^[a-z][a-z0-9-]*[a-z0-9]$",
            "min_length": 1,
            "max_length": 64,
            "allowed_chars": "a-z, 0-9, -",
        },
        "required_files": ["SKILL.md"],
        "required_directories": ["references", "examples", "scripts", ".claude"],
        "required_fields": ["name", "description", "allowed-tools"],
        "template_requirements": {
            "minimal": [],
            "tool-based": ["tool-integration.md", "usage-examples.md"],
            "workflow-based": ["workflow-steps.md", "decision-points.md"],
            "analyzer-based": ["analysis-methods.md", "metrics.md"],
        },
    }
