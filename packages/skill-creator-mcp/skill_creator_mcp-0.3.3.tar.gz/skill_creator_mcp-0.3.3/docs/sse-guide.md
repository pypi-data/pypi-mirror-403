# Skill Creator MCP SSE 配置指南

> 版本: 0.3.3
> 更新日期: 2026-01-26
> 适用场景: 远程部署、Web应用集成、多客户端访问

---

## 概述

SSE（Server-Sent Events）是 Skill Creator MCP 的远程传输模式，适用于需要通过网络访问的场景。

### SSE vs STDIO

| 特性 | SSE 模式 | STDIO 模式 |
|------|----------|------------|
| **适用场景** | 远程服务器、Web应用 | 本地开发、Claude Desktop |
| **通信方式** | HTTP Server-Sent Events | 标准输入/输出 |
| **网络访问** | 支持远程访问 | 仅本地进程 |
| **部署方式** | 独立服务器 | 子进程 |

---

## 快速开始

### 1. 启动 SSE 服务器

```bash
# 进入 MCP Server 目录
cd skill-creator-mcp

# 启动 SSE 服务器
uv run python -m skill_creator_mcp.http

# 或使用已安装的包
python -m skill_creator_mcp.http
```

服务器将在 `http://localhost:8000` 启动。

### 2. 验证服务运行

```bash
# 健康检查
curl http://localhost:8000/

# 或使用浏览器访问
# http://localhost:8000/
```

### 3. 在 Claude Code 中配置

```bash
# 添加 SSE 服务器
claude mcp add skill-creator-remote sse http://localhost:8000/sse
```

---

## 服务器启动方式

### 方式1：使用 uv（推荐）

```bash
cd skill-creator-mcp
uv run python -m skill_creator_mcp.http
```

### 方式2：使用已安装的包

```bash
python -m skill_creator_mcp.http
```

### 方式3：使用 uvicorn（生产环境）

```bash
# 安装 uvicorn
pip install uvicorn

# 启动服务器
uvicorn skill_creator_mcp.http:app --host 0.0.0.0 --port 8000
```

---

## 环境变量配置

### 使用 .env 文件

**创建 `.env` 文件**：
```ini
# 日志配置
SKILL_CREATOR_LOG_LEVEL=INFO
SKILL_CREATOR_LOG_FORMAT=default

# 输出配置
SKILL_CREATOR_OUTPUT_DIR=.

# 操作配置
SKILL_CREATOR_MAX_RETRIES=3
SKILL_CREATOR_TIMEOUT_SECONDS=30
```

**加载环境变量**：
```bash
# 使用 python-dotenv
pip install python-dotenv

# 启动时加载
python -m dotenv run python -m skill_creator_mcp.http
```

---

## 远程部署配置

### 监听所有网络接口

```bash
# 允许远程访问
uv run python -m skill_creator_mcp.http --host 0.0.0.0 --port 8000
```

### 使用 uvicorn 部署

```bash
# 基础部署
uvicorn skill_creator_mcp.http:app --host 0.0.0.0 --port 8000

# 带工作进程
uvicorn skill_creator_mcp.http:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 安全配置

### 反向代理配置（Nginx）

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /sse {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 专用配置
        proxy_buffering off;
        proxy_cache off;
    }
}
```

### 防火墙配置

```bash
# Linux (ufw)
sudo ufw allow 8000/tcp
sudo ufw reload

# Linux (firewalld)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

---

## 系统服务配置

### systemd 服务配置

**创建服务文件** `/etc/systemd/system/skill-creator-mcp.service`：
```ini
[Unit]
Description=Skill Creator MCP Server (SSE)
After=network.target

[Service]
Type=simple
User=skill-creator
Group=skill-creator
WorkingDirectory=/opt/Skills-Creator/skill-creator-mcp
Environment="PATH=/opt/Skills-Creator/skill-creator-mcp/.venv/bin"
Environment="SKILL_CREATOR_LOG_LEVEL=INFO"
Environment="SKILL_CREATOR_OUTPUT_DIR=/var/lib/skill-creator"
ExecStart=/usr/bin/python3 -m skill_creator_mcp.http
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启动服务**：
```bash
# 安装服务
sudo cp skill-creator-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable skill-creator-mcp
sudo systemctl start skill-creator-mcp
sudo systemctl status skill-creator-mcp
```

---

## Docker 部署

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY skill-creator-mcp/ ./skill-creator-mcp/
WORKDIR /app/skill-creator-mcp

# 安装依赖
RUN uv sync --frozen

# 暴露端口
EXPOSE 8000

# 启动服务器
CMD ["uv", "run", "python", "-m", "skill_creator_mcp.http"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  skill-creator-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SKILL_CREATOR_LOG_LEVEL=INFO
      - SKILL_CREATOR_OUTPUT_DIR=/data
    volumes:
      - ./data:/data
    restart: unless-stopped
```

---

## 故障排除

### 问题1: 端口被占用

**错误信息**：
```
OSError: [Errno 48] Address already in use
```

**解决方案**：
```bash
# 查找占用进程
lsof -i :8000

# 终止进程或更换端口
uv run python -m skill_creator_mcp.http --port 8001
```

### 问题2: 无法远程访问

**症状**：本地可以访问，远程无法访问

**解决方案**：
```bash
# 1. 确认监听地址为 0.0.0.0（而非 localhost）
uv run python -m skill_creator_mcp.http --host 0.0.0.0

# 2. 检查防火墙
sudo ufw status
sudo ufw allow 8000/tcp

# 3. 检查云服务器安全组
# 确保入站规则允许 8000 端口
```

### 问题3: SSE 连接断开

**症状**：连接建立后很快断开

**解决方案**：
```nginx
# Nginx 配置增加超时
location /sse {
    proxy_pass http://localhost:8000;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
    proxy_buffering off;
    proxy_cache off;
}
```

---

## 监控与日志

### 查看日志

**systemd 日志**：
```bash
# 实时查看
sudo journalctl -u skill-creator-mcp -f

# 查看最近100行
sudo journalctl -u skill-creator-mcp -n 100
```

### 日志级别说明

| 级别 | 用途 | 适用场景 |
|------|------|----------|
| DEBUG | 开发调试 | 开发环境、问题排查 |
| INFO | 正常运行 | 生产环境默认 |
| WARNING | 警告信息 | 关注潜在问题 |
| ERROR | 错误信息 | 生产环境、错误追踪 |

---

## 相关资源

- [配置参数参考](./configuration.md) - 完整的环境变量配置
- [安装指南](./installation.md) - 安装步骤和配置
- [IDE 集成配置](./ide-config.md) - 各种 IDE 的配置示例
- [Claude Code 配置指南](./claude-code-config.md) - Claude Code 详细配置
