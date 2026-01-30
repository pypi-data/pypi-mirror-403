"""GitHub MCP 集成测试.

测试 GitHub MCP 集成功能，验证：
1. SKILL.md 中的 mcp_servers 配置
2. GitHub 示例文档的存在性和有效性
3. 交叉引用链接的有效性
"""

from pathlib import Path

import pytest
import yaml

from skill_creator_mcp.utils.validators import _validate_skill_md

# 项目根目录
PROJECT_ROOT = Path("/models/claude-glm/Skills-Creator")
SKILL_CREATOR_DIR = PROJECT_ROOT / "skill-creator"
EXAMPLES_DIR = SKILL_CREATOR_DIR / "examples"
SKILL_MD = SKILL_CREATOR_DIR / "SKILL.md"


@pytest.mark.asyncio
async def test_github_mcp_servers_config():
    """测试 SKILL.md 中的 GitHub MCP 配置."""
    if not SKILL_MD.exists():
        pytest.skip(f"SKILL.md 不存在于 {SKILL_MD}")

    content = SKILL_MD.read_text(encoding="utf-8")

    # 解析 YAML frontmatter
    if not content.startswith("---"):
        pytest.fail("SKILL.md 缺少 YAML frontmatter")

    # 提取 YAML 内容
    yaml_end = content.find("---", 3)
    if yaml_end == -1:
        pytest.fail("SKILL.md YAML frontmatter 格式错误")

    yaml_content = content[3:yaml_end].strip()
    frontmatter = yaml.safe_load(yaml_content)

    # 验证 mcp_servers 字段存在
    assert "mcp_servers" in frontmatter, "SKILL.md 缺少 mcp_servers 字段"

    # 验证 GitHub 在 mcp_servers 列表中
    mcp_servers = frontmatter["mcp_servers"]
    assert isinstance(mcp_servers, list), "mcp_servers 应该是列表类型"
    assert "GitHub" in mcp_servers, "GitHub 应该在 mcp_servers 列表中"


@pytest.mark.asyncio
async def test_github_requirement_tracking_example_exists():
    """测试 github-requirement-tracking.md 示例文档存在."""
    example_file = EXAMPLES_DIR / "github-requirement-tracking.md"

    if not EXAMPLES_DIR.exists():
        pytest.skip(f"examples 目录不存在: {EXAMPLES_DIR}")

    assert example_file.exists(), f"GitHub 需求追踪示例不存在: {example_file}"

    # 验证文件内容非空
    content = example_file.read_text(encoding="utf-8")
    assert len(content) > 100, "示例文档内容过少"


@pytest.mark.asyncio
async def test_github_automation_example_exists():
    """测试 github-automation.md 示例文档存在."""
    example_file = EXAMPLES_DIR / "github-automation.md"

    if not EXAMPLES_DIR.exists():
        pytest.skip(f"examples 目录不存在: {EXAMPLES_DIR}")

    assert example_file.exists(), f"GitHub 自动化示例不存在: {example_file}"

    # 验证文件内容非空
    content = example_file.read_text(encoding="utf-8")
    assert len(content) > 100, "示例文档内容过少"


@pytest.mark.asyncio
async def test_github_example_content_validity():
    """测试 GitHub 示例文档内容有效性."""
    if not EXAMPLES_DIR.exists():
        pytest.skip(f"examples 目录不存在: {EXAMPLES_DIR}")

    github_files = [
        EXAMPLES_DIR / "github-requirement-tracking.md",
        EXAMPLES_DIR / "github-automation.md",
    ]

    for example_file in github_files:
        if not example_file.exists():
            pytest.fail(f"示例文件不存在: {example_file}")

        content = example_file.read_text(encoding="utf-8")

        # 验证基本的 Markdown 结构
        assert "#" in content, f"{example_file.name} 缺少标题"

        # 验证包含 GitHub 相关关键词
        github_keywords = ["GitHub", "issue", "MCP"]
        found_keywords = [kw for kw in github_keywords if kw.lower() in content.lower()]
        assert len(found_keywords) >= 2, f"{example_file.name} 应该包含 GitHub 相关关键词"


@pytest.mark.asyncio
async def test_github_cross_references():
    """测试 GitHub 示例中的交叉引用链接."""
    if not EXAMPLES_DIR.exists():
        pytest.skip(f"examples 目录不存在: {EXAMPLES_DIR}")

    github_files = [
        EXAMPLES_DIR / "github-requirement-tracking.md",
        EXAMPLES_DIR / "github-automation.md",
    ]

    for example_file in github_files:
        if not example_file.exists():
            continue

        content = example_file.read_text(encoding="utf-8")

        # 检查是否有引用链接
        if "](references/" in content or "](../references/" in content:
            # 提取引用路径
            import re

            pattern = r'\]\((?:\.\./)?references/([^)]+)\)'
            matches = re.findall(pattern, content)

            for ref_path in matches:
                ref_file = SKILL_CREATOR_DIR / "references" / ref_path
                assert ref_file.exists(), f"{example_file.name} 引用的文档不存在: {ref_path}"


@pytest.mark.asyncio
async def test_github_examples_in_readme():
    """测试 GitHub 示例在 README 中的引用."""
    readme_file = EXAMPLES_DIR / "README.md"

    if not readme_file.exists():
        pytest.skip("examples/README.md 不存在")

    content = readme_file.read_text(encoding="utf-8")

    # 验证 GitHub 示例被提及或索引
    github_examples = ["github-requirement-tracking", "github-automation"]
    found_examples = [ex for ex in github_examples if ex in content]

    # 至少应该有一个 GitHub 示例被提及
    assert len(found_examples) > 0, "README 应该提及至少一个 GitHub 示例"


@pytest.mark.asyncio
async def test_skill_creator_valid_with_github_mcp():
    """测试 skill-creator 技能在添加 GitHub MCP 后仍然有效."""
    if not SKILL_CREATOR_DIR.exists():
        pytest.skip(f"skill-creator 目录不存在: {SKILL_CREATOR_DIR}")

    # 使用现有的验证器验证技能
    structure_errors = []
    content_errors = []
    content_warnings = []

    # 检查基本结构
    required_dirs = ["references", "examples"]
    for dir_name in required_dirs:
        dir_path = SKILL_CREATOR_DIR / dir_name
        if not dir_path.exists():
            structure_errors.append(f"缺少必需目录: {dir_name}")

    # 检查 SKILL.md
    if SKILL_MD.exists():
        content_errors, content_warnings, _ = _validate_skill_md(SKILL_CREATOR_DIR)
    else:
        content_errors.append("缺少 SKILL.md 文件")

    # 验证结果
    assert len(structure_errors) == 0, f"结构错误: {structure_errors}"
    assert len(content_errors) == 0, f"内容错误: {content_errors}"
