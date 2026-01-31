# MCP 配置参数说明与最佳实践

> **版本**: v0.3.3
> **更新日期**: 2026-01-26
> **审核状态**: ✅ 已修正 - 区分安装方式

---

## 重要说明：根据安装方式选择配置

⚠️ **关键**：配置方式取决于您如何安装 `skill-creator-mcp`

| 安装方式 | 推荐配置 | 是否需要 --directory |
|---------|----------|---------------------|
| **PyPI / pip / uv pip** | 直接运行 | ❌ 不需要 |
| **源码开发（克隆仓库）** | 使用 --directory | ✅ 需要 |

---

## 场景一：全局安装（推荐用于大多数用户）

### 安装方式

```bash
# 方式1：使用 uv pip 安装（推荐）
uv pip install skill-creator-mcp

# 方式2：使用 pip 安装
pip install skill-creator-mcp

# 方式3：从 PyPI 安装
pip install skill-creator-mcp
```

### Claude Code 配置

**方式1：使用 claude mcp add（简单）**
```bash
claude mcp add skill-creator stdio python -m skill_creator_mcp --scope user
```

**方式2：使用 claude mcp add-json（推荐）**
```bash
claude mcp add-json "skill-creator" '{
  "command": "python",
  "args": ["-m", "skill_creator_mcp"]
}' --scope user
```

### Claude Desktop 配置

**配置文件**：`~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "skill-creator": {
      "command": "python",
      "args": ["-m", "skill_creator_mcp"],
      "env": {
        "SKILL_CREATOR_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**优点**：
- ✅ 配置简单，无需指定路径
- ✅ 可以从任何位置运行
- ✅ 自动使用已安装的版本

**工作目录**：
- MCP Server 在 Python 环境目录启动
- 技能默认创建在 Claude Code 启动目录
- 可通过 `SKILL_CREATOR_OUTPUT_DIR` 环境变量自定义

**验证安装**：
```bash
# 检查是否已安装
python -c "import skill_creator_mcp; print('OK')"

# 测试运行
python -m skill_creator_mcp --help
```

---

## 场景二：源码开发（仅限贡献者/开发者）

### 安装方式

```bash
# 1. 克隆仓库
git clone https://github.com/GeerMrc/Skills-Creator.git
cd Skills-Creator/skill-creator-mcp

# 2. 安装依赖
uv sync --dev
```

### Claude Code 配置

**方式1：使用 claude mcp add**
```bash
claude mcp add skill-creator stdio uv run python -m skill_creator_mcp --scope user
```

**方式2：使用 claude mcp add-json（推荐）**
```bash
claude mcp add-json "skill-creator" '{
  "command": "uv",
  "args": [
    "--directory",
    "/absolute/path/to/Skills-Creator/skill-creator-mcp",
    "run",
    "python",
    "-m",
    "skill_creator_mcp"
  ]
}' --scope user
```

### Claude Desktop 配置

**使用 uv --directory**（推荐）：

```json
{
  "mcpServers": {
    "skill-creator": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/Skills-Creator/skill-creator-mcp",
        "run",
        "python",
        "-m",
        "skill_creator_mcp"
      ],
      "env": {
        "SKILL_CREATOR_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**使用 cwd**（替代方案）：

```json
{
  "mcpServers": {
    "skill-creator": {
      "command": "python",
      "args": ["-m", "skill_creator_mcp"],
      "cwd": "/absolute/path/to/Skills-Creator/skill-creator-mcp"
    }
  }
}
```

**优点**：
- ✅ 使用最新源码
- ✅ 可以直接修改代码
- ✅ 适合调试和开发

**注意事项**：
- 路径必须是绝对路径
- 需要安装 uv >= 0.5.0
- 必须先运行 `uv sync`

---

## 配置对比表

### 全局安装 vs 源码开发

| 维度 | 全局安装 | 源码开发 |
|------|----------|----------|
| **安装复杂度** | ⭐ 简单 | ⭐⭐ 中等 |
| **配置复杂度** | ⭐ 简单 | ⭐⭐⭐ 复杂 |
| **更新方式** | `pip install -U` | `git pull` |
| **适用场景** | 使用工具 | 开发/贡献 |
| **路径依赖** | ❌ 无 | ✅ 有 |
| **需要 --directory** | ❌ 否 | ✅ 是 |

---

## 工作目录机制

### 关键概念

MCP 配置中有**两个不同的目录概念**：

| 配置项 | 作用范围 | 说明 |
|--------|----------|------|
| `--directory` / `cwd` | MCP Server | 控制 MCP Server 启动位置 |
| `output_dir` | 工具参数 | 控制技能创建位置 |

### 工作流程图

```
全局安装场景：
┌─────────────────────────────────────┐
│     Claude Code 启动目录             │
│     (如 /home/user/projects)        │
├─────────────────────────────────────┤
│  MCP Server (系统 Python)           │
│  ✓ 已安装到 site-packages           │
│  ✓ 无需指定目录                      │
├─────────────────────────────────────┤
│  技能创建目录 (output_dir=".")       │
│  /home/user/projects/my-skill/      │
└─────────────────────────────────────┘

源码开发场景：
┌─────────────────────────────────────┐
│     Claude Code 启动目录             │
│     (如 /home/user/Skills-Creator)   │
├─────────────────────────────────────┤
│  MCP Server (--directory 指定)      │
│  /home/user/Skills-Creator/         │
│  skill-creator-mcp/                 │
├─────────────────────────────────────┤
│  技能创建目录 (output_dir=".")       │
│  /home/user/Skills-Creator/         │
│  my-skill/                          │
└─────────────────────────────────────┘
```

---

## 常见问题排查

### 问题1：模块找不到

**错误信息**：`ModuleNotFoundError: No module named 'skill_creator_mcp'`

**原因**：
- 使用了源码开发配置，但包未安装
- 或者使用了全局安装配置，但包未正确安装

**解决方案**：

**方案A**：安装到系统（推荐）
```bash
pip install skill-creator-mcp
# 或
uv pip install skill-creator-mcp
```

**方案B**：使用源码开发配置
```json
{
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
```

### 问题2：已全局安装，但配置了 --directory

**症状**：配置复杂，但没必要

**解决方案**：简化配置
```json
{
  "command": "python",
  "args": ["-m", "skill_creator_mcp"]
}
```

### 问题3：技能创建位置不对

**原因**：`output_dir` 默认为 `"."`（Claude Code 启动目录）

**解决方案**：设置环境变量
```json
{
  "env": {
    "SKILL_CREATOR_OUTPUT_DIR": "/path/to/skills"
  }
}
```

---

## 快速决策树

```
您是如何安装的？
│
├─ 通过 pip / uv pip / PyPI 安装？
│  └─→ 使用全局安装配置（简单）
│      {
│        "command": "python",
│        "args": ["-m", "skill_creator_mcp"]
│      }
│
└─ 克隆了源码仓库进行开发？
   └─→ 使用源码开发配置（复杂）
      {
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
```

---

## 推荐项目结构

### 标准布局（全局安装）

```
/home/user/development/
├── my-project-1/         ← 技能1
├── my-project-2/         ← 技能2
└── shared-skills/        ← 共享技能
    ├── utils/
    └── templates/
```

**配置**：
```json
{
  "env": {
    "SKILL_CREATOR_OUTPUT_DIR": "/home/user/development/shared-skills"
  }
}
```

---

## 参考资源

- [PyPI 页面](https://pypi.org/project/skill-creator-mcp/)
- [GitHub 仓库](https://github.com/GeerMrc/Skills-Creator)
- [uv 官方文档](https://github.com/astral-sh/uv)
