# Skill Creator MCP 故障排除指南

> 版本: 0.3.3
> 更新日期: 2026-01-26

本文档提供常见问题和解决方案。

---

## 常见问题速查表

| 问题 | 类型 | 解决方案 |
|------|------|----------|
| 模块未找到 | 安装问题 | 重新安装依赖 |
| 工具数量不对 | 配置问题 | 重启 IDE，确认版本 |
| 配置无效 | 配置问题 | 检查 JSON 格式 |
| 连接超时 | 运行问题 | 检查网络，增加超时 |
| 权限错误 | 权限问题 | 使用用户安装 |

---

## 安装问题

### 问题：Python 版本不兼容

**错误信息**：
```
Python 3.10 或更高版本 required
```

**解决方案**：
```bash
# 检查 Python 版本
python --version

# 升级 Python（推荐使用 pyenv）
pyenv install 3.11
pyenv global 3.11
```

### 问题：依赖安装失败

**错误信息**：
```
ERROR: Could not find a version that satisfies the requirement
```

**解决方案**：
```bash
# 更新 pip
pip install --upgrade pip

# 清除缓存重试
pip install --no-cache-dir -e ".[dev]"

# 或使用 uv
uv sync --dev
```

### 问题：uv 命令未找到

**解决方案**：
```bash
# 安装 uv
pip install uv

# 或使用官方安装脚本
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 配置问题

### 问题：MCP 服务器未找到

**症状**：`claude mcp list` 中没有显示 skill-creator

**解决方案**：
```bash
# 检查配置
claude mcp list

# 重新添加
claude mcp remove skill-creator
claude mcp add skill-creator stdio python -m skill_creator_mcp

# 确认安装
python -c "import skill_creator_mcp; print('OK')"
```

### 问题：配置文件 JSON 格式错误

**错误信息**：
```
JSON parse error in .mcp.json
```

**解决方案**：
```bash
# 验证 JSON 格式
cat .mcp.json | python -m json.tool

# 或使用 jq
cat .mcp.json | jq .
```

### 问题：环境变量未生效

**症状**：设置的环境变量没有生效

**解决方案**：
```bash
# 确认环境变量设置
claude mcp list

# 查看完整配置
cat .mcp.json

# 删除并重新添加
claude mcp remove skill-creator
claude mcp add skill-creator stdio python -m skill_creator_mcp \
  --env SKILL_CREATOR_LOG_LEVEL=DEBUG
```

---

## 运行时问题

### 问题：工具数量不对（少于16个）

**症状**：IDE 中只显示部分工具

**解决方案**：
```bash
# 1. 确认版本
cd skill-creator-mcp
git log -1 --oneline

# 2. 拉取最新代码
git pull

# 3. 重新安装依赖
uv sync --dev

# 4. 重启 IDE
```

### 问题：权限错误

**错误信息**：
```
Permission denied
```

**解决方案**：
```bash
# 使用用户安装
pip install --user -e ".[dev]"

# 或使用虚拟环境
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 问题：模块导入失败

**错误信息**：
```
ModuleNotFoundError: No module named 'skill_creator_mcp'
```

**解决方案**：
```bash
# 确认安装位置
pip show skill-creator-mcp

# 重新安装
cd skill-creator-mcp
pip install -e .

# 或使用 uv
uv sync --dev
```

### 问题：日志级别设置无效

**症状**：设置 DEBUG 但看不到调试日志

**解决方案**：
```bash
# 确认使用大写
SKILL_CREATOR_LOG_LEVEL=DEBUG  # 正确
SKILL_CREATOR_LOG_LEVEL=debug  # 错误

# 有效值：DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## IDE 集成问题

### Claude Code 问题

**问题：claude mcp 命令未找到**

**解决方案**：
```bash
# 确认 Claude Code 已安装
claude --version

# 更新 Claude Code
# (根据你的安装方式)
```

**问题：配置后工具不显示**

**解决方案**：
```bash
# 1. 检查配置
claude mcp list

# 2. 重启 VSCode
# 3. 检查 Claude Code 日志
```

### Claude Desktop 问题

**问题：配置文件位置不正确**

**macOS 配置位置**：
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows 配置位置**：
```
%APPDATA%/Claude/claude_desktop_config.json
```

**Linux 配置位置**：
```
~/.config/Claude/claude_desktop_config.json
```

**解决方案**：
```bash
# 检查配置文件
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json  # macOS
cat ~/.config/Claude/claude_desktop_config.json  # Linux

# 验证 JSON 格式
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
```

### Cursor 问题

**问题：配置文件路径**

**配置位置**：
```
~/Library/Application Support/Cursor/User/globalStorage/mcp_servers_config.json  # macOS
~/.config/Cursor/User/globalStorage/mcp_servers_config.json  # Linux
%APPDATA%/Cursor/User/globalStorage/mcp_servers_config.json  # Windows
```

---

## 性能问题

### 问题：操作超时

**症状**：长时间运行后超时

**解决方案**：
```bash
# 增加超时时间
claude mcp add skill-creator stdio python -m skill_creator_mcp \
  --env SKILL_CREATOR_TIMEOUT_SECONDS=60
```

---

## 调试技巧

### 启用调试日志

```bash
claude mcp add skill-creator stdio python -m skill_creator_mcp \
  --env SKILL_CREATOR_LOG_LEVEL=DEBUG \
  --env SKILL_CREATOR_LOG_FORMAT=detailed
```

### 检查 MCP 连接

```bash
# 列出所有服务器
claude mcp list

# 查看服务器详情
claude mcp show skill-creator
```

### 手动测试服务器

```bash
# 测试 STDIO 模式
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python -m skill_creator_mcp

# 测试 SSE 模式
curl http://localhost:8000/
```

### 查看日志

**systemd 日志**（如果使用系统服务）：
```bash
sudo journalctl -u skill-creator-mcp -f
```

**Claude Desktop 日志**：
```
~/Library/Logs/Claude/  # macOS
%APPDATA%\Claude\logs\  # Windows
```

---

## 获取帮助

### 文档资源

- [安装指南](./installation.md) - 安装和配置
- [配置参数参考](./configuration.md) - 环境变量配置
- [IDE 集成配置](./ide-config.md) - IDE 配置示例
- [Claude Code 配置指南](./claude-code-config.md) - Claude Code 详细配置

### 报告问题

如果问题无法解决，请：

1. 收集错误信息
2. 记录配置内容
3. 描述复现步骤
4. 提交 Issue 到项目仓库

---

## 常用命令速查

```bash
# 安装依赖
cd skill-creator-mcp
uv sync --dev

# 检查安装
python -c "import skill_creator_mcp; print('OK')"

# 列出 MCP 服务器
claude mcp list

# 添加服务器
claude mcp add skill-creator stdio python -m skill_creator_mcp

# 删除服务器
claude mcp remove skill-creator

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
uv run mypy src/
```
