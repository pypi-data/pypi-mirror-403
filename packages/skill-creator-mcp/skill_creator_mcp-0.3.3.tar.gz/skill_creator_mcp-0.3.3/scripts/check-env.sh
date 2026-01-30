#!/bin/bash
# 开发环境检查脚本

set -e

echo "========================================="
echo "  Skill Creator MCP - 环境检查"
echo "========================================="
echo ""

# 1. 检查 Python 版本
echo "1. 检查 Python 版本..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "  ❌ 错误: Python 版本 $PYTHON_VERSION 低于要求 (>= 3.10)"
    exit 1
fi
echo "  ✓ Python 版本: $PYTHON_VERSION"
echo ""

# 2. 检查 uv
echo "2. 检查 uv..."
if ! command -v uv &> /dev/null; then
    echo "  ❌ 错误: uv 未安装"
    echo "  请运行: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
UV_VERSION=$(uv --version)
echo "  ✓ uv 版本: $UV_VERSION"
echo ""

# 3. 检查项目目录
echo "3. 检查项目结构..."
if [ ! -f "pyproject.toml" ]; then
    echo "  ❌ 错误: pyproject.toml 不存在"
    exit 1
fi
echo "  ✓ pyproject.toml 存在"

if [ ! -d "src/skill_creator_mcp" ]; then
    echo "  ❌ 错误: src/skill_creator_mcp 目录不存在"
    exit 1
fi
echo "  ✓ 源代码目录存在"
echo ""

# 4. 检查依赖安装
echo "4. 检查依赖安装..."
if ! uv run python -c "import fastmcp" 2>/dev/null; then
    echo "  ⚠ 警告: fastmcp 未安装，运行 'uv sync' 安装依赖"
else
    echo "  ✓ fastmcp 已安装"
fi
echo ""

echo "========================================="
echo "  环境检查完成！"
echo "========================================="
echo ""
echo "下一步："
echo "  1. 安装依赖: uv sync --dev"
echo "  2. 运行测试: uv run pytest"
echo "  3. 启动服务器: uv run python -m skill_creator_mcp"
echo ""
