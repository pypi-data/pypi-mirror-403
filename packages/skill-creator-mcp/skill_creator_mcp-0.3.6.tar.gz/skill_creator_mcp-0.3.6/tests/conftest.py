"""pytest 配置."""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """临时目录 fixture."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def sample_skill_dir(temp_dir):
    """示例技能目录 fixture."""
    skill_dir = temp_dir / "sample-skill"
    skill_dir.mkdir()

    # 创建 SKILL.md
    (skill_dir / "SKILL.md").write_text("""---
name: sample-skill
description: |
  示例技能。用于测试。

  何时使用：测试
  触发词：测试
---

# Sample Skill

示例技能内容。
""")

    # 创建 references 目录
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    (refs_dir / "advanced.md").write_text("# 高级用法\n\n详细内容...")

    return skill_dir
