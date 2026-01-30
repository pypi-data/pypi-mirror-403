#!/bin/bash
# 测试覆盖率检查脚本

set -e

echo "========================================="
echo "  测试覆盖率检查"
echo "========================================="
echo ""

# 运行测试并生成覆盖率报告
echo "运行测试套件..."
PYTHONPATH=/models/claude-glm/Skills-Creator/skill-creator-mcp/src python -m pytest tests/ --cov=src/skill_creator_mcp --cov-report=term-missing --cov-report=html -v

echo ""
echo "========================================="
echo "  覆盖率总结"
echo "========================================="