"""最佳实践资源.

提供 Agent-Skills 开发的最佳实践指南。
"""

from typing import Final

# 最佳实践内容
BEST_PRACTICES_CONTENT: Final = """# Agent-Skills 开发最佳实践

## 1. 技能设计原则

### 1.1 单一职责
- 每个技能应该专注于一个明确的任务或功能域
- 避免创建过于复杂的多功能技能

### 1.2 渐进式披露
- 基础用法应该简单直接
- 高级功能可以逐步揭示
- 提供清晰的示例文档

### 1.3 上下文感知
- 技能应该理解调用上下文
- 适应不同的使用场景

## 2. SKILL.md 结构规范

### 2.1 必需字段
- `name`: 技能名称（小写字母、数字、连字符）
- `description`: 清晰描述技能功能
- `allowed-tools`: 明确列出需要的工具

### 2.2 内容组织
```markdown
## 技能概述
[1-2 句话描述]

## 核心能力
[列出 3-5 个核心能力]

## 使用方法
[提供基本和高级用法示例]
```

### 2.3 长度限制
- SKILL.md 应该 ≤150 行
- 保持简洁，将详细内容放到 references/

## 3. 目录结构规范

### 3.1 必需目录
```
skill-name/
├── SKILL.md              # 主文档
├── references/           # 参考文档
├── examples/             # 使用示例
├── scripts/              # 辅助脚本
└── .claude/              # Claude 配置
```

### 3.2 可选目录
```
├── src/                  # 源代码（如果需要）
│   └── skill_name/
│       ├── __init__.py
│       ├── server.py     # MCP Server（如果需要）
│       ├── models/       # 数据模型
│       └── utils/        # 工具函数
└── tests/                # 测试
```

## 4. MCP 工具使用规范

### 4.1 工具选择
- 只在 `allowed-tools` 中声明实际需要的工具
- 优先使用 Read/Write/Edit 而不是 Bash

### 4.2 错误处理
- 始终检查工具调用的返回值
- 提供清晰的错误信息

### 4.3 性能优化
- 避免不必要的文件读取
- 使用 Glob/Grep 进行批量操作

## 5. 命名规范

### 5.1 技能名称
- 格式：`{功能}-{修饰符}`
- 示例：`code-analyzer`, `file-organizer`, `api-helper`

### 5.2 目录名称
- 必须与 SKILL.md 中的 name 字段一致
- 使用小写字母和连字符

### 5.3 文件命名
- Python 模块：使用下划线 `my_helper.py`
- Markdown 文档：使用连字符 `usage-guide.md`

## 6. 文档编写规范

### 6.1 参考文档 (references/)
- 每个主题一个文件
- 使用清晰的标题层级
- 包含代码示例

### 6.2 使用示例 (examples/)
- 提供真实可运行的示例
- 包含预期输出
- 标注复杂度级别

## 7. 测试规范

### 7.1 测试覆盖
- 核心逻辑必须有单元测试
- 目标覆盖率 ≥ 80%

### 7.2 测试类型
- 单元测试：测试独立函数
- 集成测试：测试完整流程
- 示例测试：验证文档中的示例

## 8. 质量检查清单

在提交技能前，请确认：

- [ ] SKILL.md ≤ 150 行
- [ ] name 字段与目录名一致
- [ ] 所有必需目录存在
- [ ] references/ 包含所有必需文件
- [ ] allowed-tools 只包含实际使用的工具
- [ ] 文档中的示例可以运行
- [ ] 没有硬编码的路径
- [ ] 错误处理完善

## 9. 常见反模式

### 9.1 避免过度复杂
- ❌ 创建"全能"技能
- ✅ 拆分为多个专注的技能

### 9.2 避免重复造轮
- ❌ 重新实现现有工具的功能
- ✅ 直接声明使用现有工具

### 9.3 避免模糊描述
- ❌ "这个技能做很多事情"
- ✅ "这个技能分析 Python 代码的复杂度"
"""


def get_best_practices() -> str:
    """获取最佳实践文档内容.

    Returns:
        最佳实践 Markdown 内容
    """
    return BEST_PRACTICES_CONTENT


def get_best_practices_summary() -> dict:
    """获取最佳实践摘要.

    Returns:
        包含关键要点的字典
    """
    return {
        "design_principles": [
            "单一职责",
            "渐进式披露",
            "上下文感知",
        ],
        "structure_rules": [
            "SKILL.md ≤ 150 行",
            "必需目录：references/, examples/, scripts/, .claude/",
            "name 字段与目录名一致",
        ],
        "naming_conventions": {
            "skill_name": "小写字母、数字、连字符",
            "python_modules": "下划线分隔",
            "markdown_files": "连字符分隔",
        },
        "quality_checks": [
            "文档示例可运行",
            "无硬编码路径",
            "错误处理完善",
            "测试覆盖率 ≥ 80%",
        ],
    }
