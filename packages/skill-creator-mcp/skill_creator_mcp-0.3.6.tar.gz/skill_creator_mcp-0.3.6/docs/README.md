# Skill Creator MCP 文档索引

> Skill Creator MCP - Agent-Skills 开发与质量保证工具

欢迎来到 Skill Creator MCP 文档中心！本文档提供完整的文档导航和快速开始指南。

---

## 🚀 快速开始

### 5分钟快速安装

**方式1：使用 uv 安装**（推荐）

```bash
cd skill-creator-mcp
uv sync --dev
```

**方式2：使用 pip 安装**

```bash
cd skill-creator-mcp
pip install -e ".[dev]"
```

详细安装指南请参考：[安装指南](./installation.md)

### 快速配置

**1. 配置 Claude Code**

```bash
cd /path/to/Skills-Creator
claude mcp add skill-creator stdio python -m skill_creator_mcp
```

**2. 验证配置**

```bash
claude mcp list
```

详细配置请参考：
- [Claude Code 配置指南](./claude-code-config.md)
- [IDE 集成配置](./ide-config.md)

---

## 📚 完整文档导航

### 安装与配置

| 文档 | 描述 | 适合人群 |
|------|------|---------|
| [快速开始](./quick-start.md) | MCP Server 快速配置指南 | 新用户 |
| [安装指南](./installation.md) | 详细的安装和配置说明 | 新用户 |
| [配置参数参考](./configuration.md) | 所有环境变量的完整参考 | 高级用户 |
| [MCP 配置说明](./mcp-config-guide.md) | uv/venv/全局安装配置方案与最佳实践 | 所有用户 |
| [IDE集成配置](./ide-config.md) | Claude Desktop/Cursor/Continue.dev 等配置 | IDE用户 |
| [Claude Code 配置指南](./claude-code-config.md) | Claude Code CLI 完整配置 | Claude Code 用户 |
| [SSE配置指南](./sse-guide.md) | SSE 模式远程部署指南 | 运维人员 |
| [客户端兼容性说明](./client-compatibility.md) | 客户端限制与自动降级策略 | 所有用户 |

### 使用指南

| 文档 | 描述 | 适合人群 |
|------|------|---------|
| [MCP 工具列表](./api/) | 所有 MCP 工具的完整文档 | 所有用户 |

### 技术文档

| 文档 | 描述 | 适合人群 |
|------|------|---------|
| [API 参考](./api/) | 所有 MCP 工具的完整 API 文档 | 开发者 |

---

## 🎯 按场景查找

### 我想快速安装和开始使用

**推荐路径**：
1. [安装指南](./installation.md) - 选择安装方式
2. [Claude Code 配置指南](./claude-code-config.md) - 快速配置
3. [MCP 工具列表](./api/) - 学习使用

### 我想了解所有配置选项

**推荐路径**：
1. [配置参数参考](./configuration.md) - 完整的参数列表
- 日志配置（LOG_LEVEL, LOG_FORMAT, LOG_FILE）
- 输出配置（OUTPUT_DIR）
- 操作配置（MAX_RETRIES, TIMEOUT_SECONDS）

### 我想在 IDE 中使用

**推荐路径**：
1. [IDE 集成配置](./ide-config.md) - 选择你的 IDE
- Claude Desktop
- Claude Code (VSCode)
- Cursor
- Continue.dev
2. [配置参数参考](./configuration.md) - 环境变量配置

### 我想部署到远程服务器

**推荐路径**：
1. [SSE 配置指南](./sse-guide.md) - 远程部署配置
2. [配置参数参考](./configuration.md) - 认证和端口配置

---

## 🔍 可用工具列表

### 需求收集原子工具（7个）

| 工具 | 描述 |
|------|------|
| `create_requirement_session` | 创建需求收集会话 |
| `get_requirement_session` | 获取会话状态 |
| `update_requirement_answer` | 更新答案 |
| `get_static_question` | 获取静态问题 |
| `generate_dynamic_question` | 生成动态问题 |
| `validate_answer_format` | 验证答案格式 |
| `check_requirement_completeness` | 检查需求完整性 |

### 技能工具（4个）

| 工具 | 描述 |
|------|------|
| `init_skill` | 初始化新的 Agent-Skill |
| `validate_skill` | 验证技能结构和内容 |
| `analyze_skill` | 分析代码质量和复杂度 |
| `refactor_skill` | 生成重构建议 |

### 打包工具（1个）

| 工具 | 描述 |
|------|------|
| `package_skill` | 打包发布工具（支持strict模式进行Agent-Skill标准打包） |

### 开发工具（不作为MCP工具暴露）

| 工具 | 描述 |
|------|------|
| `check_client_capabilities` | 检测客户端能力支持 |
| `test_llm_sampling` | 测试 LLM Sampling 能力 |
| `test_user_elicitation` | 测试用户征询能力 |
| `test_conversation_loop` | 测试对话循环能力 |
| `test_requirement_completeness` | 测试需求完整性判断 |

> 注意：这些工具仅在开发环境有用，已迁移到 `scripts/dev-tools.py`。
> 开发者可通过 `python -m scripts.dev-tools <command>` 使用。
> 相关测试保留在 `tests/test_utils/test_testing.py`。

---

## 📊 项目统计

| 指标 | 数值 |
|------|------|
| 当前版本 | v0.3.6 |
| MCP 工具数量 | 12 个核心工具（不含开发工具） |
| 测试覆盖率 | 97% (553 个测试用例) |
| 支持的模板 | 4 种（minimal/tool-based/workflow-based/analyzer-based） |

---

## 🔗 相关链接

- [主项目 README](../README.md)
- [项目架构审计报告](../../ARCHITECTURE_AUDIT_REPORT_v2.md)
- [FastMCP 文档](https://jlowin.github.io/fastmcp/)

---

## 📝 文档更新记录

- **2026-01-28**: 添加快速开始指南和客户端兼容性说明，更新工具列表（需求收集拆分为7个原子工具）
- **2026-01-26**: v0.3.3 版本文档更新，完善安装配置说明
- **2026-01-29**: v0.3.4 版本，移除 package_agent_tool（已弃用），统一使用 package_skill

---

> **提示**：这是 Skill Creator MCP 的文档索引页面。如果你不知道从哪里开始，建议先阅读 [安装指南](./installation.md) 和 [Claude Code 配置指南](./claude-code-config.md)。
