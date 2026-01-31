"""配置集成测试.

测试配置系统的端到端行为，包括环境变量优先级、
Pydantic 模型与配置的集成、以及跨平台兼容性。
"""

import os
from pathlib import Path

from skill_creator_mcp.config import Config, get_config, reload_config
from skill_creator_mcp.models.skill_config import InitSkillInput
from skill_creator_mcp.utils.cache import MemoryCache
from skill_creator_mcp.utils.path_helpers import (
    normalize_path,
    split_path_parts,
)


class TestConfigIntegration:
    """配置集成测试."""

    def test_env_var_priority(self, tmp_path):
        """测试环境变量优先级."""
        env_dir = tmp_path / "env-output"
        env_dir.mkdir()

        # 设置环境变量
        os.environ["SKILL_CREATOR_OUTPUT_DIR"] = str(env_dir)
        try:
            reload_config()
            config = get_config()

            # 验证配置正确读取环境变量
            assert env_dir in config.output_dir.parents or config.output_dir == env_dir
        finally:
            del os.environ["SKILL_CREATOR_OUTPUT_DIR"]
            reload_config()

    def test_pydantic_model_respects_config(self, tmp_path):
        """测试 Pydantic 模型正确读取配置."""
        env_dir = tmp_path / "pydantic-test"
        env_dir.mkdir()

        os.environ["SKILL_CREATOR_OUTPUT_DIR"] = str(env_dir)
        try:
            reload_config()

            # 不传递 output_dir，应使用环境变量
            input_data = InitSkillInput.model_validate({
                "name": "test-skill",
                # output_dir=None（使用默认）
            })

            # 验证模型正确应用了默认值
            assert str(env_dir) in input_data.output_dir or input_data.output_dir == str(env_dir)
        finally:
            del os.environ["SKILL_CREATOR_OUTPUT_DIR"]
            reload_config()

    def test_path_helpers_cross_platform(self, tmp_path):
        """测试路径工具跨平台兼容性."""
        # 测试路径规范化
        path = normalize_path(tmp_path / "test" / "path")
        assert path.is_absolute()

        # 测试路径拼接（使用 pathlib 而非字符串拼接）
        joined = tmp_path / "subdir" / "file.txt"
        assert "subdir" in str(joined)
        assert "file.txt" in str(joined)

        # 测试路径分割
        parts = split_path_parts(joined)
        assert len(parts) >= 2
        assert "file.txt" in parts[-1] or parts[-1].endswith("file.txt")

    def test_cache_respects_config(self):
        """测试缓存正确读取配置."""
        # 重新加载配置以确保使用默认值
        reload_config()

        # 创建缓存（不传递参数，应使用配置默认值）
        cache = MemoryCache()

        # 验证缓存使用配置默认值
        config = get_config()
        assert cache.max_size == config.cache_size
        assert cache.default_ttl == config.cache_ttl

    def test_cache_custom_values(self):
        """测试缓存自定义值."""
        # 创建自定义缓存
        custom_size = 256
        custom_ttl = 7200
        cache = MemoryCache(max_size=custom_size, default_ttl=custom_ttl)

        # 验证自定义值生效
        assert cache.max_size == custom_size
        assert cache.default_ttl == custom_ttl

    def test_config_new_properties(self):
        """测试新增的配置属性."""
        config = Config()

        # 验证新增的属性（不包含已删除的 default_output_dir）
        assert hasattr(config, "cache_size")
        assert hasattr(config, "cache_ttl")
        assert hasattr(config, "plan_archive_dir")

        # 验证默认值
        assert config.cache_size == 128
        assert config.cache_ttl == 3600
        # 默认输出目录是 ~/skills（使用 output_dir 属性）
        assert "skills" in str(config.output_dir).lower()
        assert str(Path.home()) in str(config.output_dir)

    def test_plan_archive_dir_configurable(self, tmp_path):
        """测试计划归档目录可配置."""
        custom_archive = tmp_path / "custom-archive"

        os.environ["SKILL_CREATOR_PLAN_ARCHIVE_DIR"] = str(custom_archive)
        try:
            reload_config()
            config = get_config()

            # 验证自定义归档目录生效
            assert str(custom_archive) in str(config.plan_archive_dir)
        finally:
            del os.environ["SKILL_CREATOR_PLAN_ARCHIVE_DIR"]
            reload_config()

    def test_output_dir_parameter_overrides_config(self, tmp_path):
        """测试参数可以覆盖配置."""
        config_dir = tmp_path / "config-dir"
        config_dir.mkdir()

        param_dir = tmp_path / "param-dir"
        param_dir.mkdir()

        # 设置环境变量
        os.environ["SKILL_CREATOR_OUTPUT_DIR"] = str(config_dir)
        try:
            reload_config()

            # 传递显式参数，应覆盖环境变量
            input_data = InitSkillInput.model_validate({
                "name": "test-skill",
                "output_dir": str(param_dir),
            })

            # 验证参数优先级高于配置
            assert str(param_dir) in input_data.output_dir
        finally:
            del os.environ["SKILL_CREATOR_OUTPUT_DIR"]
            reload_config()

    def test_config_validation_with_new_defaults(self):
        """测试配置验证使用新的默认值."""
        config = Config()
        errors = config.validate()

        # 新的默认值应该通过验证
        assert len(errors) == 0 or all("output_dir" not in e for e in errors)
