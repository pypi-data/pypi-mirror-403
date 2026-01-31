# 配置参数参考

> 版本: 0.3.3
> 更新日期: 2026-01-26

本文档提供所有环境变量的完整参考，确保配置参数与代码实现100%一致。

## 环境变量完整参考

### 日志配置

| 环境变量 | 默认值 | 有效值 | 描述 |
|---------|--------|--------|------|
| `SKILL_CREATOR_LOG_LEVEL` | INFO | DEBUG, INFO, WARNING, ERROR, CRITICAL | 日志级别 |
| `SKILL_CREATOR_LOG_FORMAT` | default | default, simple, detailed | 日志格式 |
| `SKILL_CREATOR_LOG_FILE` | 无（输出到stderr） | 文件路径 | 日志文件路径（可选） |

### 输出配置

| 环境变量 | 默认值 | 有效值 | 描述 |
|---------|--------|--------|------|
| `SKILL_CREATOR_OUTPUT_DIR` | ~/skills | 目录路径 | 默认输出目录（自动创建） |

### 操作配置

| 环境变量 | 默认值 | 有效值 | 描述 |
|---------|--------|--------|------|
| `SKILL_CREATOR_MAX_RETRIES` | 3 | ≥0 的整数 | 最大重试次数 |
| `SKILL_CREATOR_TIMEOUT_SECONDS` | 30 | >0 的整数 | 操作超时时间（秒） |

---

## 配置文件位置

### 默认配置文件

**.env.example** - 示例配置文件：
```
skill-creator-mcp/.env.example
```

**.env** - 实际配置文件（需创建）：
```
skill-creator-mcp/.env
```

### 环境变量配置方式

**方式1：使用 .env 文件**（推荐）

在项目根目录创建 `.env` 文件：
```bash
# 复制示例配置
cp .env.example .env

# 编辑配置
nano .env
```

**方式2：使用系统环境变量**

在 `~/.bashrc` 或 `~/.zshrc` 中添加：
```bash
export SKILL_CREATOR_LOG_LEVEL=DEBUG
export SKILL_CREATOR_OUTPUT_DIR=~/skills-output
```

**方式3：使用 IDE 配置**

在 IDE 的 MCP 服务器配置中通过 `env` 字段传递：
```json
{
  "env": {
    "SKILL_CREATOR_LOG_LEVEL": "DEBUG",
    "SKILL_CREATOR_OUTPUT_DIR": "~/skills-output"
  }
}
```

---

## 日志配置详解

### 日志级别 (SKILL_CREATOR_LOG_LEVEL)

控制日志输出的详细程度：

| 级别 | 输出内容 | 使用场景 |
|------|---------|----------|
| `DEBUG` | 所有调试信息 | 开发调试、问题排查 |
| `INFO` | 一般信息（默认） | 正常运行 |
| `WARNING` | 警告信息 | 关注潜在问题 |
| `ERROR` | 仅错误信息 | 生产环境、错误追踪 |
| `CRITICAL` | 严重错误 | 系统级别问题 |

**配置示例**：
```bash
# 开发环境
SKILL_CREATOR_LOG_LEVEL=DEBUG

# 生产环境
SKILL_CREATOR_LOG_LEVEL=INFO
```

### 日志格式 (SKILL_CREATOR_LOG_FORMAT)

控制日志输出的格式：

| 格式 | 描述 | 使用场景 |
|------|------|----------|
| `default` | 默认格式，包含时间、级别、消息 | 正常使用 |
| `simple` | 简化格式，仅消息 | 简洁输出 |
| `detailed` | 详细格式，包含更多上下文 | 调试分析 |

### 日志文件 (SKILL_CREATOR_LOG_FILE)

指定日志输出文件（可选）：

```bash
# 输出到文件
SKILL_CREATOR_LOG_FILE=/var/log/skill-creator-mcp.log

# 输出到 stderr（默认）
SKILL_CREATOR_LOG_FILE=
```

---

## 输出配置详解

### 输出目录 (SKILL_CREATOR_OUTPUT_DIR)

指定技能创建的默认输出目录，支持自动目录管理。

```bash
# 默认值（自动创建）
SKILL_CREATOR_OUTPUT_DIR=~/skills

# 自定义路径
SKILL_CREATOR_OUTPUT_DIR=~/.claude/skills

# 绝对路径
SKILL_CREATOR_OUTPUT_DIR=/opt/skills-output
```

### 目录自动管理功能

**v0.3.3+ 新增功能**：

1. **自动创建目录**：目录不存在时自动创建（包括父目录）
2. **自动验证**：验证路径存在且为目录
3. **权限检查**：验证目录可写性
4. **路径展开**：自动展开 `~` 为用户主目录

**优先级**：
```
工具参数 > SKILL_CREATOR_OUTPUT_DIR > 默认值 (~/skills)
```

**推荐配置**：

1. **使用默认值**（推荐）：
   ```bash
   # 无需配置，自动使用 ~/skills
   # 首次使用时自动创建
   ```

2. **自定义路径**：
   ```bash
   export SKILL_CREATOR_OUTPUT_DIR=~/.claude/skills
   ```

3. **Claude Code 配置**：
   ```json
   {
     "env": {
       "SKILL_CREATOR_OUTPUT_DIR": "~/.claude/skills"
     }
   }
   ```

---

## 操作配置详解

### 最大重试次数 (SKILL_CREATOR_MAX_RETRIES)

失败操作的最大重试次数：

```bash
# 默认值
SKILL_CREATOR_MAX_RETRIES=3

# 不重试
SKILL_CREATOR_MAX_RETRIES=0

# 增加重试次数
SKILL_CREATOR_MAX_RETRIES=5
```

### 超时时间 (SKILL_CREATOR_TIMEOUT_SECONDS)

单个操作的超时时间（秒）：

```bash
# 默认值（30秒）
SKILL_CREATOR_TIMEOUT_SECONDS=30

# 增加超时时间
SKILL_CREATOR_TIMEOUT_SECONDS=60

# 减少超时时间
SKILL_CREATOR_TIMEOUT_SECONDS=15
```

---

## 完整配置示例

### 开发环境配置

```bash
# .env 文件
SKILL_CREATOR_LOG_LEVEL=DEBUG
SKILL_CREATOR_LOG_FORMAT=detailed
SKILL_CREATOR_OUTPUT_DIR=~/dev-skills
SKILL_CREATOR_MAX_RETRIES=5
SKILL_CREATOR_TIMEOUT_SECONDS=60
```

### 生产环境配置

```bash
# .env 文件
SKILL_CREATOR_LOG_LEVEL=INFO
SKILL_CREATOR_LOG_FORMAT=default
SKILL_CREATOR_LOG_FILE=/var/log/skill-creator-mcp.log
SKILL_CREATOR_OUTPUT_DIR=/opt/skills
SKILL_CREATOR_MAX_RETRIES=3
SKILL_CREATOR_TIMEOUT_SECONDS=30
```

---

## 配置验证

### 检查配置有效性

```python
from skill_creator_mcp.config import get_config

config = get_config()
# 验证配置
errors = config.validate()

if errors:
    print(f"配置错误: {errors}")
else:
    print("配置有效")
```

### 常见配置错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 无效的 LOG_LEVEL | 值不在有效范围内 | 使用 DEBUG/INFO/WARNING/ERROR/CRITICAL |
| 无效的 LOG_FORMAT | 值不在有效范围内 | 使用 default/simple/detailed |
| OUTPUT_DIR 不是目录 | 路径存在但不是目录 | 使用有效的目录路径 |
| MAX_RETRIES < 0 | 负数 | 使用 ≥0 的整数 |
| TIMEOUT_SECONDS <= 0 | 非正数 | 使用 >0 的整数 |

---

## 配置优先级

```
IDE 配置环境变量 > .env 文件 > 系统环境变量 > 默认值
```

---

## 相关文档

- [安装指南](./installation.md) - 安装和基础配置
- [IDE 集成配置](./ide-config.md) - 各种 IDE 的配置示例
- [Claude Code 配置指南](./claude-code-config.md) - Claude Code 详细配置
