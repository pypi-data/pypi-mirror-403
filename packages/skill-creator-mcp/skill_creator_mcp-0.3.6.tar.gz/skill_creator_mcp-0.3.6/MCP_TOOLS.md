# MCP Server 工具清单

> **版本**: v0.3.6
> **更新日期**: 2026-01-29
> **项目**: skill-creator-mcp

---

## 概述

skill-creator-mcp 提供 **12个工具**，按3类功能分组，用于 Agent-Skills 的开发、验证、分析和打包。

---

## 工具分类

### 1. 技能工具（4个）

用于 Agent-Skill 的核心生命周期操作。

| 工具名称 | 功能 | 类别 |
|---------|------|------|
| `init_skill` | 初始化新的 Agent-Skill 项目结构 | 创建 |
| `validate_skill` | 验证 Agent-Skill 的结构和内容 | 验证 |
| `analyze_skill` | 分析代码质量、复杂度和结构 | 分析 |
| `refactor_skill` | 生成重构建议 | 优化 |

---

### 2. 需求收集原子工具（7个）

用于收集技能创建需求的原子化工具，符合ADR 001架构原则。

| 工具名称 | 功能 | 类别 |
|---------|------|------|
| `create_requirement_session_tool` | 创建需求收集会话 | 会话管理 |
| `get_requirement_session_tool` | 获取会话状态 | 会话管理 |
| `update_requirement_answer_tool` | 更新答案 | 会话管理 |
| `get_static_question_tool` | 获取预定义问题（basic/complete模式） | 问题获取 |
| `generate_dynamic_question_tool` | 生成动态问题（brainstorm/progressive模式） | 问题获取 |
| `validate_answer_format_tool` | 验证答案格式 | 验证工具 |
| `check_requirement_completeness_tool` | 检查需求完整性 | 验证工具 |

**说明**: 这些工具替代了旧的 `collect_requirements` 单一工具（已弃用），提供更灵活的工作流编排能力。

---

### 3. 打包工具（1个）

用于 Agent-Skill 的打包和分发。

| 工具名称 | 功能 | 模式 |
|---------|------|------|
| `package_skill` | 统一打包工具 | 支持 strict 模式生成标准化包名 |

**package_skill 参数**:
- `strict=False` (默认): 通用打包模式
- `strict=True`: Agent-Skill 标准打包模式，需要 `version` 参数

---

## 工具总数统计

```
技能工具:      4
需求收集工具:  7
打包工具:      1
───────────────────
总计:         12
```

---

## 使用指南

### 快速开始

1. **创建技能**: 使用 `init_skill` 初始化项目
2. **收集需求**: 使用7个需求收集工具收集用户需求
3. **验证技能**: 使用 `validate_skill` 检查质量
4. **分析质量**: 使用 `analyze_skill` 获取详细分析
5. **打包分发**: 使用 `package_skill` 生成发布包

### 工作流示例

```python
# 1. 收集需求
session = await create_requirement_session_tool(mode="basic")
# ... 使用其他需求收集工具

# 2. 初始化技能
await init_skill(name="my-skill", template="tool-based")

# 3. 验证技能
validation = await validate_skill(skill_path="...")

# 4. 分析质量
analysis = await analyze_skill(skill_path="...")

# 5. 打包（标准模式，带版本号）
await package_skill(skill_path="...", version="0.1.0", strict=True)
```

---

## 相关文档

- [README.md](README.md) - MCP Server 完整文档
- [CHANGELOG.md](CHANGELOG.md) - 版本变更记录
- [需求收集 API 核心](../skill-creator/references/requirement-collection-api-core.md) - 7个需求收集工具详细文档

---

**文档维护**: 随工具变更更新
**最后更新**: 2026-01-29
