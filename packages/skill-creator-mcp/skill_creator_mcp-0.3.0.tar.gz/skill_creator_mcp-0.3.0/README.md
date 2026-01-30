# Skill Creator MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-563%20passed-success](#)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen](#)

Agent-Skills 开发与质量保证 MCP Server。

## 开发状态

> 🚧 **项目正在开发中**
>
> 当前版本：v0.3.0
>
> 这是 Skill-Creator 项目的 MCP Server 组件，提供创建、验证、分析和重构 Agent-Skills 的工具。

## 特性

- ✅ **collect_requirements** - AI 驱动的需求澄清工具（支持会话恢复）
- ✅ **init_skill** - 初始化新的 Agent-Skill 项目（支持 4 种模板）
- ✅ **validate_skill** - 验证技能结构和内容规范
- ✅ **analyze_skill** - 分析代码质量和复杂度
- ✅ **refactor_skill** - 重构建议生成（P0/P1/P2 优先级）
- ✅ **package_skill** - 打包发布工具（zip/tar.gz/tar.bz2）

### 技能模板

| 模板类型 | 描述 | 适用场景 |
|---------|------|----------|
| `minimal` | 最小化模板 | 简单工具封装 |
| `tool-based` | 工具集成模板 | 封装现有工具 |
| `workflow-based` | 工作流模板 | 多步骤流程 |
| `analyzer-based` | 分析器模板 | 代码分析 |

*注：✅ 已实现 | 🚧 开发中*

## 安装

### 使用 uv（推荐）

```bash
# 克隆仓库
git clone <repository-url>
cd skill-creator-mcp

# 安装依赖
uv sync --dev
```

### 使用 pip

```bash
pip install -e ".[dev]"
```

## 配置

### Claude Code 配置

编辑 `~/.config/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "skill-creator": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/skill-creator-mcp",
        "run",
        "python",
        "-m",
        "skill_creator_mcp"
      ]
    }
  }
}
```

### 环境变量配置（可选）

创建 `.env` 文件来自定义服务器行为：

```bash
# 复制模板
cp .env.example .env

# 编辑配置
vim .env
```

**可用环境变量**：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SKILL_CREATOR_LOG_LEVEL` | INFO | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `SKILL_CREATOR_LOG_FORMAT` | text | 日志格式（text/json） |
| `SKILL_CREATOR_LOG_FILE` | - | 日志文件路径（可选） |
| `SKILL_CREATOR_OUTPUT_DIR` | . | 默认输出目录 |
| `SKILL_CREATOR_MAX_RETRIES` | 3 | 最大重试次数 |
| `SKILL_CREATOR_TIMEOUT_SECONDS` | 30 | 超时时间（秒） |
| `SKILL_CREATOR_DEV_MODE` | false | 开发模式（启用详细调试） |

## 使用

### collect_requirements - 需求澄清

AI 驱动的对话式需求收集工具，支持会话状态管理。

**参数：**
- `action` (str): 执行动作（`start`/`next`/`previous`/`status`/`complete`）
- `mode` (str): 收集模式（`basic`/`complete`/`brainstorm`/`progressive`）
- `session_id` (str, 可选): 会话 ID（自动生成）
- `user_input` (str, 可选): 用户输入（用于 next/complete 动作）

**收集模式：**
- `basic` - 5 步基础收集（技能名称、功能、场景、模板、额外需求）
- `complete` - 10 步完整收集（基础 + 用户、技术栈、依赖、测试、文档）
- `brainstorm` - AI 引导的创意发散
- `progressive` - 快速开始，逐步完善

**返回：**
```json
{
  "success": true,
  "session_id": "req_20250123_abc123",
  "action": "start",
  "mode": "basic",
  "current_step": {
    "key": "skill_name",
    "title": "技能名称",
    "prompt": "请输入技能名称..."
  },
  "step_index": 0,
  "total_steps": 5,
  "progress": 0.0,
  "answers": {},
  "message": "欢迎使用需求澄清工具！当前进度：0% (0/5)",
  "completed": false
}
```

### init_skill - 初始化技能

创建新的 Agent-Skill 项目目录结构。

**参数：**
- `name` (str): 技能名称（小写字母、数字、连字符，1-64字符）
- `template` (str): 模板类型（`minimal`/`tool-based`/`workflow-based`/`analyzer-based`）
- `output_dir` (str): 输出目录路径（默认：`.`）
- `with_scripts` (bool): 是否包含示例脚本（默认：`False`）
- `with_examples` (bool): 是否包含使用示例（默认：`False`）

**返回：**
```json
{
  "success": true,
  "skill_path": "/path/to/skill",
  "skill_name": "my-skill",
  "template_type": "tool-based",
  "message": "技能初始化成功"
}
```

### validate_skill - 验证技能

验证 Agent-Skill 的结构和内容是否符合规范。

**参数：**
- `skill_path` (str): 技能目录路径
- `check_structure` (bool): 是否检查目录结构（默认：`True`）
- `check_content` (bool): 是否检查内容格式（默认：`True`）

**返回：**
```json
{
  "success": true,
  "valid": true,
  "skill_path": "/path/to/skill",
  "skill_name": "my-skill",
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

### analyze_skill - 分析技能

分析 Agent-Skill 的代码质量、复杂度和结构。

**参数：**
- `skill_path` (str): 技能目录路径
- `analyze_structure` (bool): 是否分析代码结构（默认：`True`）
- `analyze_complexity` (bool): 是否分析代码复杂度（默认：`True`）
- `analyze_quality` (bool): 是否分析代码质量（默认：`True`）

**返回：**
```json
{
  "success": true,
  "skill_path": "/path/to/skill",
  "skill_name": "my-skill",
  "structure": {
    "total_files": 10,
    "total_lines": 500,
    "file_breakdown": {
      "server": 1,
      "models": 2,
      "utils": 3,
      "tests": 4
    }
  },
  "complexity": {
    "cyclomatic_complexity": 5,
    "maintainability_index": 85.5
  },
  "quality": {
    "overall_score": 75.0,
    "structure_score": 30.0,
    "documentation_score": 25.0,
    "test_coverage_score": 20.0
  },
  "suggestions": ["建议1", "建议2"],
  "summary": "代码质量良好..."
}
```

## 开发

```bash
# 运行环境检查
./scripts/check-env.sh

# 运行测试
uv run pytest

# 运行 lint
uv run ruff check .

# 运行类型检查
uv run mypy src/

# 启动服务器
uv run python -m skill_creator_mcp
```

## 许可证

MIT License

## 参考资源

- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [需求澄清指南](../skill-creator/references/requirement-collection.md)
