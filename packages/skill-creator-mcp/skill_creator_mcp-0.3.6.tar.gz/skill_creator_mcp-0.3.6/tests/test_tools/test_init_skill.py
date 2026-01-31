"""测试 init_skill 工具."""

import os
from pathlib import Path

import pytest

from skill_creator_mcp.utils.file_ops import (
    create_directory_structure,
    create_directory_structure_async,
    read_file,
    read_file_async,
    write_file,
    write_file_async,
)
from skill_creator_mcp.utils.validators import (
    validate_skill_directory,
    validate_skill_name,
    validate_template_type,
)


@pytest.fixture(autouse=True)
def clear_env():
    """每个测试前清除环境变量."""
    original_env = os.environ.copy()
    for key in list(os.environ.keys()):
        if key.startswith("SKILL_CREATOR_"):
            del os.environ[key]
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.mark.asyncio
async def test_init_skill_success(temp_dir):
    """测试成功初始化技能."""
    # 验证并创建
    validate_skill_name("test-skill")
    validate_template_type("minimal")

    skill_dir = await create_directory_structure_async(
        name="test-skill",
        template_type="minimal",
        output_dir=temp_dir,
    )

    # 生成 SKILL.md
    skill_md_content = _generate_skill_md_content("test-skill", "minimal")
    await write_file_async(skill_dir / "SKILL.md", skill_md_content)

    assert skill_dir.exists()
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "references").exists()
    assert (skill_dir / "examples").exists()
    assert (skill_dir / "scripts").exists()
    assert (skill_dir / ".claude").exists()


def test_validate_skill_name():
    """测试技能名称验证."""
    # 有效名称
    validate_skill_name("test-skill")
    validate_skill_name("test123")
    validate_skill_name("test-skill-123")

    # 无效名称
    with pytest.raises(ValueError):
        validate_skill_name("Invalid_Name")

    with pytest.raises(ValueError):
        validate_skill_name("-invalid")

    with pytest.raises(ValueError):
        validate_skill_name("invalid-")


def test_validate_template_type():
    """测试模板类型验证."""
    # 有效模板
    assert validate_template_type("minimal") == "minimal"
    assert validate_template_type("tool-based") == "tool-based"
    assert validate_template_type("workflow-based") == "workflow-based"
    assert validate_template_type("analyzer-based") == "analyzer-based"

    # 无效模板
    with pytest.raises(ValueError):
        validate_template_type("invalid")


def test_validate_skill_directory(temp_dir):
    """测试技能目录验证."""
    # 创建有效的技能目录
    skill_dir = temp_dir / "valid-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("test")

    # 应该通过验证
    validate_skill_directory(skill_dir)

    # 测试不存在的目录
    with pytest.raises(ValueError, match="不存在"):
        validate_skill_directory(temp_dir / "non-existent")

    # 测试缺少 SKILL.md 的目录
    invalid_dir = temp_dir / "invalid-skill"
    invalid_dir.mkdir()

    with pytest.raises(ValueError, match="SKILL.md 不存在"):
        validate_skill_directory(invalid_dir)


def test_sync_create_directory_structure(temp_dir):
    """测试同步创建目录结构."""
    skill_dir = create_directory_structure(
        name="test-sync",
        template_type="minimal",
        output_dir=temp_dir,
    )

    assert skill_dir.exists()
    assert (skill_dir / "references").exists()
    assert (skill_dir / "examples").exists()
    assert (skill_dir / "scripts").exists()
    assert (skill_dir / ".claude").exists()


def test_sync_write_file(temp_dir):
    """测试同步写入文件."""
    test_file = temp_dir / "test.txt"
    content = "Hello, World!"

    write_file(test_file, content)

    assert test_file.exists()
    assert test_file.read_text() == content


@pytest.mark.asyncio
async def test_async_read_file(temp_dir):
    """测试异步读取文件."""
    test_file = temp_dir / "test-read.txt"
    content = "Test content for reading"
    test_file.write_text(content)

    result = await read_file_async(test_file)
    assert result == content


def test_sync_read_file(temp_dir):
    """测试同步读取文件."""
    test_file = temp_dir / "test-sync-read.txt"
    content = "Test sync read"
    test_file.write_text(content)

    result = read_file(test_file)
    assert result == content


def _generate_skill_md_content(name: str, template: str) -> str:
    """生成 SKILL.md 内容."""
    skill_title = name.replace("-", " ").replace("_", " ").title()

    descriptions = {
        "minimal": "最小化技能模板，适用于简单功能。",
        "tool-based": "基于工具的技能模板，适用于封装特定工具或 API。",
        "workflow-based": "基于工作流的技能模板，适用于多步骤任务。",
        "analyzer-based": "基于分析的技能模板，适用于数据分析或代码分析。",
    }

    description = descriptions.get(template, descriptions["minimal"])

    allowed_tools = {
        "minimal": "Read, Write, Edit, Bash",
        "tool-based": "Read, Write, Edit, Bash",
        "workflow-based": "Read, Write, Edit, Bash, Glob, Grep",
        "analyzer-based": "Read, Glob, Grep, Bash",
    }

    tools = allowed_tools.get(template, allowed_tools["minimal"])

    return f"""---
name: {name}
description: |
  {description}

allowed-tools: {tools}
mcp_servers: []
---

# {skill_title}

## 技能概述

[简要描述这个技能的功能和用途]
"""


# ==================== 路径验证测试 ====================


def test_output_dir_validation_with_nonexistent_path(temp_dir):
    """测试不存在的路径自动创建."""
    from skill_creator_mcp.models.skill_config import InitSkillInput

    nonexistent = temp_dir / "new" / "nested" / "dir"
    result = InitSkillInput.model_validate({
        "name": "test-skill",
        "output_dir": str(nonexistent),
    })

    assert result.output_dir == str(nonexistent.resolve())
    assert nonexistent.exists()
    assert nonexistent.is_dir()


def test_output_dir_validation_with_file_instead_of_dir(temp_dir):
    """测试路径是文件而非目录时报错."""
    from skill_creator_mcp.models.skill_config import InitSkillInput

    file_path = temp_dir / "not-a-dir"
    file_path.write_text("content")

    with pytest.raises(ValueError, match="不是目录"):
        InitSkillInput.model_validate({
            "name": "test-skill",
            "output_dir": str(file_path),
        })


def test_output_dir_expands_tilde():
    """测试 ~ 展开为用户主目录."""
    from skill_creator_mcp.models.skill_config import InitSkillInput

    input_data = InitSkillInput.model_validate({
        "name": "test-skill",
        "output_dir": "~/test-skill-output",
    })

    home = Path.home()
    expected = str(home / "test-skill-output")
    assert input_data.output_dir == expected


def test_output_dir_validates_read_only_directory(temp_dir):
    """测试只读目录报错."""
    import stat

    from skill_creator_mcp.models.skill_config import InitSkillInput

    readonly_dir = temp_dir / "readonly"
    readonly_dir.mkdir()

    try:
        # 设置只读权限
        readonly_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

        with pytest.raises(ValueError, match="不可写"):
            InitSkillInput.model_validate({
                "name": "test-skill",
                "output_dir": str(readonly_dir),
            })
    finally:
        # 恢复权限以便清理
        readonly_dir.chmod(stat.S_IRWXU)


def test_output_dir_converts_relative_to_absolute(temp_dir):
    """测试相对路径转换为绝对路径."""
    from skill_creator_mcp.models.skill_config import InitSkillInput

    # 保存原始工作目录
    original_cwd = Path.cwd()
    try:
        # 在临时目录中创建相对路径
        os.chdir(temp_dir)

        input_data = InitSkillInput.model_validate({
            "name": "test-skill",
            "output_dir": "./relative/path",
        })

        # 应该是绝对路径
        assert Path(input_data.output_dir).is_absolute()
        # 应该包含 temp_dir
        assert str(temp_dir) in input_data.output_dir
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_init_skill_respects_env_var(monkeypatch, temp_dir):
    """测试工具读取环境变量."""
    from skill_creator_mcp.config import reload_config
    from skill_creator_mcp.models.skill_config import InitSkillInput

    env_dir = temp_dir / "env-output"
    env_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SKILL_CREATOR_OUTPUT_DIR", str(env_dir))

    # 重新加载配置以获取新的环境变量
    reload_config()
    from skill_creator_mcp.config import get_config

    config = get_config()
    assert str(env_dir) in str(config.output_dir) or env_dir == config.output_dir

    # 验证 InitSkillInput 可以使用环境变量值
    input_data = InitSkillInput.model_validate({
        "name": "test-skill",
        "output_dir": str(config.output_dir),
    })

    assert "env-output" in input_data.output_dir
