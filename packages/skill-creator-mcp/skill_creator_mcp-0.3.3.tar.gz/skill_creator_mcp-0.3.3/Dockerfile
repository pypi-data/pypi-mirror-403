# Skill Creator MCP Server - Dockerfile
# 多阶段构建，优化镜像大小

FROM python:3.12-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装 uv 包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY src ./src

# 安装依赖并构建
RUN uv sync --frozen --no-dev
RUN uv build

# 最终运行时镜像
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 创建非 root 用户
RUN useradd -m -u 1000 mcpuser

WORKDIR /app

# 从 builder 复制构建产物和依赖
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/dist /app/dist
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/pyproject.toml

# 设置所有权
RUN chown -R mcpuser:mcpuser /app

# 切换到非 root 用户
USER mcpuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 默认使用 STDIO 模式
CMD ["python", "-m", "skill_creator_mcp"]

# 暴露端口（SSE 模式）
EXPOSE 8000

# 使用说明：
# STDIO 模式（默认）:
#   docker run -it --rm skill-creator-mcp
#
# SSE HTTP 模式:
#   docker run -it --rm -p 8000:8000 skill-creator-mcp python -m skill_creator_mcp.http
