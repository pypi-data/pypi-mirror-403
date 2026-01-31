# MCP Server 配置指南

> **本文档提供 MCP Server 快速配置指南**
> **完整文档**: [Skill Creator MCP 文档](https://github.com/your-repo/blob/main/skill-creator-mcp/docs/README.md)

---

## 快速安装

### 方式1：使用 uv 安装（推荐）

```bash
cd skill-creator-mcp
uv sync --dev
```

### 方式2：使用 pip 安装

```bash
cd skill-creator-mcp
pip install -e ".[dev]"
```

---

## Claude Code Desktop 配置

### 1. 配置 MCP Server

```bash
cd /path/to/Skills-Creator
claude mcp add skill-creator stdio python -m skill_creator_mcp
```

### 2. 验证配置

```bash
claude mcp list
```

### 3. 测试连接

```bash
uv run python -m skill_creator_mcp
```

---

## Claude Desktop 配置

### 配置文件位置

| 操作系统 | 配置文件路径 |
|---------|-------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

### 配置示例

```json
{
  "mcpServers": {
    "skill-creator": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/Skills-Creator/skill-creator-mcp",
        "run",
        "python",
        "-m",
        "skill_creator_mcp"
      ]
    }
  }
}
```

### Python 环境配置

如果使用虚拟环境：

```json
{
  "mcpServers": {
    "skill-creator": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "skill_creator_mcp"]
    }
  }
}
```

---

## IDE 集成配置

### VSCode + Claude Code

1. 安装 Claude Code 扩展
2. 在项目根目录运行：
   ```bash
   claude mcp add skill-creator stdio python -m skill_creator_mcp
   ```
3. 重启 VSCode

### Cursor

1. 打开 Settings (Cmd/Ctrl + ,)
2. 搜索 "MCP Servers"
3. 添加配置：
   ```json
   {
     "skill-creator": {
       "command": "uv",
       "args": ["--directory", "/path/to/skill-creator-mcp", "run", "python", "-m", "skill_creator_mcp"]
     }
   }
   ```

### Continue.dev

1. 打开 Continue 配置文件
2. 添加 MCP 服务器：
   ```json
   {
     "mcpServers": {
       "skill-creator": {
         "command": "uv",
         "args": ["--directory", "/path/to/skill-creator-mcp", "run", "python", "-m", "skill_creator_mcp"]
       }
     }
   }
   ```

---

## 环境变量配置

### 日志配置

```bash
# 设置日志级别 (DEBUG, INFO, WARNING, ERROR)
export LOG_LEVEL=INFO

# 设置日志格式 (text, json)
export LOG_FORMAT=text

# 设置日志文件路径（可选）
export LOG_FILE=/path/to/mcp.log
```

### 输出配置

```bash
# 设置默认输出目录
export OUTPUT_DIR=/path/to/output
```

### 性能配置

```bash
# 最大重试次数（默认：3）
export MAX_RETRIES=3

# 超时时间（秒，默认：30）
export TIMEOUT_SECONDS=30
```

---

## 常见配置问题

### 问题1：ModuleNotFoundError

**症状**: 启动时报错 `ModuleNotFoundError: No module named 'skill_creator_mcp'`

**解决方案**:
```bash
# 确保在正确的目录
cd skill-creator-mcp

# 重新安装依赖
uv sync --dev

# 或使用 pip
pip install -e .
```

### 问题2：Python 版本不兼容

**症状**: 导入错误或语法错误

**解决方案**:
```bash
# 检查 Python 版本（需要 >=3.10）
python --version

# 使用正确的 Python 版本
python3.10 -m pip install -e .
```

### 问题3：MCP Server 无法连接

**症状**: Claude Desktop 显示"无法连接到 MCP Server"

**解决方案**:
1. 检查配置文件路径是否正确
2. 验证 Python 环境路径
3. 手动测试 MCP Server：
   ```bash
   uv run python -m skill_creator_mcp
   ```
4. 查看 Claude Desktop 日志

### 问题4：权限问题（Linux/macOS）

**症状**: 启动时报错 "Permission denied"

**解决方案**:
```bash
# 给予执行权限
chmod +x skill-creator-mcp/.venv/bin/python

# 或使用绝对路径
which python3
```

---

## 验证安装

运行测试验证安装：

```bash
cd skill-creator-mcp
uv run pytest --collect-only -q
```

预期输出应该显示测试收集成功。

---

## 可用工具列表

### 核心工具（12个）

| 类别 | 工具数量 | 工具列表 |
|------|----------|----------|
| **技能工具** | 4个 | init_skill, validate_skill, analyze_skill, refactor_skill |
| **打包工具** | 1个 | package_skill |
| **需求收集原子工具** | 7个 | create_requirement_session, get_requirement_session, update_requirement_answer, get_static_question, generate_dynamic_question, validate_answer_format, check_requirement_completeness |

---

## 远程部署（SSE 模式）

如需部署到远程服务器，请参考：
- [SSE 配置指南](https://github.com/your-repo/blob/main/skill-creator-mcp/docs/sse-guide.md)

快速启动：
```bash
uv run python -m skill_creator_mcp.http
# 访问: http://localhost:8000
```

---

## 相关文档

- [MCP 集成指南](mcp-integration.md) - MCP 工具使用和资源访问
- [架构设计](architecture.md) - 混合架构设计原则
- [故障排除](troubleshooting.md) - 常见问题解决

---

**最后更新**: 2026-01-28
**版本**: v0.3.3
