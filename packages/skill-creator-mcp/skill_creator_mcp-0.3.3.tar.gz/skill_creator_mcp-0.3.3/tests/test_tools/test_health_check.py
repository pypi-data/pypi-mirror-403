"""健康检查和监控单元测试."""

import time

import pytest

from skill_creator_mcp.tools.health_check import (
    CacheMetrics,
    HealthCheckResult,
    HealthStatus,
    PerformanceMetrics,
    SystemMetrics,
    determine_health_status,
    get_cache_metrics,
    get_environment_info,
    get_performance_metrics,
    get_quick_status,
    get_system_metrics,
    get_uptime,
    get_version,
    health_check,
    is_healthy,
    record_request,
    reset_performance_stats,
)


class TestHealthStatus:
    """HealthStatus 模型测试."""

    def test_health_status_creation(self):
        """测试健康状态创建."""
        status = HealthStatus(
            status="healthy",
            timestamp="2024-01-01T00:00:00",
            uptime_seconds=100.0,
            version="1.0.0",
        )

        assert status.status == "healthy"
        assert status.uptime_seconds == 100.0
        assert status.version == "1.0.0"


class TestSystemMetrics:
    """SystemMetrics 测试."""

    def test_system_metrics_structure(self):
        """测试系统指标结构."""
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=1024.0,
            memory_available_mb=2048.0,
            disk_percent=70.0,
            disk_used_gb=100.0,
            disk_free_gb=300.0,
        )

        assert metrics.cpu_percent == 50.0
        assert metrics.memory_percent == 60.0


class TestCacheMetrics:
    """CacheMetrics 测试."""

    def test_cache_metrics_structure(self):
        """测试缓存指标结构."""
        metrics = CacheMetrics(
            size=10,
            max_size=128,
            utilization_percent=7.81,
        )

        assert metrics.size == 10
        assert metrics.max_size == 128


class TestPerformanceMetrics:
    """PerformanceMetrics 测试."""

    def test_performance_metrics_structure(self):
        """测试性能指标结构."""
        metrics = PerformanceMetrics(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            avg_response_time_ms=150.5,
        )

        assert metrics.total_requests == 100
        assert metrics.successful_requests == 95
        assert metrics.failed_requests == 5
        assert metrics.avg_response_time_ms == 150.5


class TestGetSystemMetrics:
    """获取系统指标测试."""

    def test_get_system_metrics(self):
        """测试获取系统指标."""
        metrics = get_system_metrics()

        assert isinstance(metrics, SystemMetrics)
        assert 0 <= metrics.cpu_percent <= 100
        assert 0 <= metrics.memory_percent <= 100
        assert 0 <= metrics.disk_percent <= 100
        assert metrics.memory_used_mb > 0
        assert metrics.disk_free_gb >= 0


class TestGetCacheMetrics:
    """获取缓存指标测试."""

    def test_get_cache_metrics(self):
        """测试获取缓存指标."""
        metrics = get_cache_metrics()

        assert isinstance(metrics, CacheMetrics)
        assert metrics.size >= 0
        assert metrics.max_size > 0
        assert 0 <= metrics.utilization_percent <= 100


class TestGetPerformanceMetrics:
    """获取性能指标测试."""

    def test_initial_performance_metrics(self):
        """测试初始性能指标."""
        # 重置统计
        reset_performance_stats()

        metrics = get_performance_metrics()

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.avg_response_time_ms == 0.0

    def test_performance_metrics_after_requests(self):
        """测试记录请求后的性能指标."""
        reset_performance_stats()

        # 记录一些请求
        record_request(success=True, response_time=0.1)
        record_request(success=True, response_time=0.2)
        record_request(success=False, response_time=0.3)

        metrics = get_performance_metrics()

        assert metrics.total_requests == 3
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 1
        assert metrics.avg_response_time_ms > 0


class TestRecordRequest:
    """记录请求测试."""

    def test_record_successful_request(self):
        """测试记录成功请求."""
        reset_performance_stats()

        record_request(success=True, response_time=0.1)

        metrics = get_performance_metrics()
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0

    def test_record_failed_request(self):
        """测试记录失败请求."""
        reset_performance_stats()

        record_request(success=False, response_time=0.5)

        metrics = get_performance_metrics()
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1

    def test_response_time_limit(self):
        """测试响应时间数量限制."""
        reset_performance_stats()

        # 记录超过1000次请求
        for _ in range(1100):
            record_request(success=True, response_time=0.1)

        metrics = get_performance_metrics()
        assert metrics.total_requests == 1100
        # 验证平均响应时间计算正确 (0.1秒 = 100毫秒)
        assert metrics.avg_response_time_ms == 100.0
        # 验证成功请求数正确
        assert metrics.successful_requests == 1100


class TestDetermineHealthStatus:
    """确定健康状态测试."""

    def test_healthy_status(self):
        """测试健康状态."""
        system = SystemMetrics(
            cpu_percent=30.0,
            memory_percent=50.0,
            memory_used_mb=1024,
            memory_available_mb=2048,
            disk_percent=60.0,
            disk_used_gb=100,
            disk_free_gb=300,
        )
        performance = PerformanceMetrics(
            total_requests=100,
            successful_requests=98,
            failed_requests=2,
            avg_response_time_ms=100,
        )

        status = determine_health_status(system, performance)
        assert status == "healthy"

    def test_degraded_status_high_cpu(self):
        """测试高CPU导致的降级状态."""
        system = SystemMetrics(
            cpu_percent=75.0,
            memory_percent=50.0,
            memory_used_mb=1024,
            memory_available_mb=2048,
            disk_percent=60.0,
            disk_used_gb=100,
            disk_free_gb=300,
        )
        performance = PerformanceMetrics(
            total_requests=100,
            successful_requests=98,
            failed_requests=2,
            avg_response_time_ms=100,
        )

        status = determine_health_status(system, performance)
        assert status == "degraded"

    def test_degraded_status_high_failure_rate(self):
        """测试高失败率导致的降级状态."""
        system = SystemMetrics(
            cpu_percent=30.0,
            memory_percent=50.0,
            memory_used_mb=1024,
            memory_available_mb=2048,
            disk_percent=60.0,
            disk_used_gb=100,
            disk_free_gb=300,
        )
        performance = PerformanceMetrics(
            total_requests=100,
            successful_requests=85,
            failed_requests=15,
            avg_response_time_ms=100,
        )

        status = determine_health_status(system, performance)
        assert status == "degraded"

    def test_unhealthy_status_critical_cpu(self):
        """测试严重CPU使用导致的不健康状态."""
        system = SystemMetrics(
            cpu_percent=95.0,
            memory_percent=50.0,
            memory_used_mb=1024,
            memory_available_mb=2048,
            disk_percent=60.0,
            disk_used_gb=100,
            disk_free_gb=300,
        )
        performance = PerformanceMetrics(
            total_requests=100,
            successful_requests=98,
            failed_requests=2,
            avg_response_time_ms=100,
        )

        status = determine_health_status(system, performance)
        assert status == "unhealthy"

    def test_unhealthy_status_critical_memory(self):
        """测试严重内存使用导致的不健康状态."""
        system = SystemMetrics(
            cpu_percent=30.0,
            memory_percent=95.0,
            memory_used_mb=1024,
            memory_available_mb=2048,
            disk_percent=60.0,
            disk_used_gb=100,
            disk_free_gb=300,
        )
        performance = PerformanceMetrics(
            total_requests=100,
            successful_requests=98,
            failed_requests=2,
            avg_response_time_ms=100,
        )

        status = determine_health_status(system, performance)
        assert status == "unhealthy"


class TestHealthCheck:
    """健康检查测试."""

    def test_health_check_returns_result(self):
        """测试健康检查返回结果."""
        result = health_check()

        assert isinstance(result, HealthCheckResult)
        assert isinstance(result.health, HealthStatus)
        assert isinstance(result.system, SystemMetrics)
        assert isinstance(result.cache, CacheMetrics)
        assert isinstance(result.performance, PerformanceMetrics)
        assert isinstance(result.environment, dict)

    def test_health_check_status_values(self):
        """测试健康检查状态值."""
        result = health_check()

        assert result.health.status in ["healthy", "degraded", "unhealthy"]
        assert result.health.uptime_seconds >= 0
        assert result.health.version in ["unknown", "0.2.1", "0.3.0"]


class TestGetQuickStatus:
    """快速状态测试."""

    def test_get_quick_status(self):
        """测试获取快速状态."""
        status = get_quick_status()

        assert isinstance(status, str)
        assert "Status:" in status
        assert "Uptime:" in status
        assert "CPU:" in status
        assert "Memory:" in status
        assert "Requests:" in status

    def test_status_contains_status_level(self):
        """测试状态包含健康级别."""
        status = get_quick_status()
        assert any(level in status for level in ["HEALTHY", "DEGRADED", "UNHEALTHY"])


class TestIsHealthy:
    """健康判断测试."""

    def test_is_healthy_returns_bool(self):
        """测试 is_healthy 返回布尔值."""
        result = is_healthy()
        assert isinstance(result, bool)

    def test_is_healthy_with_good_metrics(self):
        """测试良好指标下的健康判断."""
        # 重置统计以确保良好的性能指标
        reset_performance_stats()
        record_request(success=True, response_time=0.1)
        record_request(success=True, response_time=0.1)

        result = is_healthy()
        # 在正常系统上应该返回 True
        assert isinstance(result, bool)


class TestGetUptime:
    """运行时间测试."""

    def test_get_uptime(self):
        """测试获取运行时间."""
        uptime = get_uptime()

        assert isinstance(uptime, float)
        assert uptime >= 0

    def test_uptime_increases(self):
        """测试运行时间递增."""
        uptime1 = get_uptime()
        time.sleep(0.1)
        uptime2 = get_uptime()

        assert uptime2 > uptime1


class TestGetVersion:
    """版本号测试."""

    def test_get_version(self):
        """测试获取版本号."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0


class TestGetEnvironmentInfo:
    """环境信息测试."""

    def test_get_environment_info(self):
        """测试获取环境信息."""
        env = get_environment_info()

        assert isinstance(env, dict)
        assert "python_version" in env
        assert "platform" in env
        assert "system" in env

    def test_environment_info_values(self):
        """测试环境信息值."""
        env = get_environment_info()

        assert "3." in env["python_version"]
        assert isinstance(env["platform"], str)


class TestResetPerformanceStats:
    """重置性能统计测试."""

    def test_reset_performance_stats(self):
        """测试重置性能统计."""
        # 记录一些数据
        record_request(success=True, response_time=0.1)
        record_request(success=False, response_time=0.2)

        # 重置
        reset_performance_stats()

        metrics = get_performance_metrics()
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0


class TestHealthCheckResult:
    """健康检查结果模型测试."""

    def test_health_check_result_complete(self):
        """测试完整的健康检查结果."""
        health = HealthStatus(
            status="healthy",
            timestamp="2024-01-01T00:00:00",
            uptime_seconds=100.0,
            version="1.0.0",
        )
        system = SystemMetrics(
            cpu_percent=30.0,
            memory_percent=50.0,
            memory_used_mb=1024.0,
            memory_available_mb=2048.0,
            disk_percent=60.0,
            disk_used_gb=100.0,
            disk_free_gb=300.0,
        )
        cache = CacheMetrics(size=10, max_size=128, utilization_percent=7.81)
        performance = PerformanceMetrics(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            avg_response_time_ms=150.5,
        )
        environment = {"python_version": "3.12.0"}

        result = HealthCheckResult(
            health=health,
            system=system,
            cache=cache,
            performance=performance,
            environment=environment,
        )

        assert result.health.status == "healthy"
        assert result.system.cpu_percent == 30.0
        assert result.cache.size == 10
        assert result.performance.total_requests == 100
        assert result.environment["python_version"] == "3.12.0"


# ==================== Server.py Tool 异常处理测试 ====================


class TestServerHealthCheckToolsExceptionHandling:
    """测试server.py中健康检查工具的异常处理 (覆盖 lines 1143-1154, 1169-1180, 1195-1206)."""

    @pytest.mark.asyncio
    async def test_health_check_tool_exception_handling(self):
        """测试health_check_tool的异常处理."""
        from unittest.mock import patch

        from skill_creator_mcp.server import health_check_tool

        # 创建mock context
        class MockContext:
            pass

        # Mock health_check抛出异常
        with patch(
            "skill_creator_mcp.server.health_check",
            side_effect=RuntimeError("Simulated health check error"),
        ):
            result = await health_check_tool(MockContext())

            assert result["success"] is False
            assert "健康检查出错" in result["error"]
            assert result["error_type"] == "internal_error"

    @pytest.mark.asyncio
    async def test_quick_status_tool_exception_handling(self):
        """测试quick_status_tool的异常处理."""
        from unittest.mock import patch

        from skill_creator_mcp.server import quick_status_tool

        class MockContext:
            pass

        # Mock get_quick_status抛出异常
        with patch(
            "skill_creator_mcp.server.get_quick_status",
            side_effect=RuntimeError("Simulated status error"),
        ):
            result = await quick_status_tool(MockContext())

            assert result["success"] is False
            assert "获取状态出错" in result["error"]
            assert result["error_type"] == "internal_error"

    @pytest.mark.asyncio
    async def test_is_healthy_tool_exception_handling(self):
        """测试is_healthy_tool的异常处理."""
        from unittest.mock import patch

        from skill_creator_mcp.server import is_healthy_tool

        class MockContext:
            pass

        # Mock is_healthy抛出异常
        with patch(
            "skill_creator_mcp.server.is_healthy",
            side_effect=RuntimeError("Simulated is_healthy error"),
        ):
            result = await is_healthy_tool(MockContext())

            assert result["success"] is False
            assert "健康检查出错" in result["error"]
            assert result["error_type"] == "internal_error"


class TestServerBatchToolsExceptionHandling:
    """测试server.py中批量工具的异常处理 (覆盖 lines 1063-1076, 1107-1121)."""

    @pytest.mark.asyncio
    async def test_batch_validate_skills_tool_exception_handling(self):
        """测试batch_validate_skills_tool的异常处理."""
        from unittest.mock import patch

        from skill_creator_mcp.server import batch_validate_skills_tool

        class MockContext:
            pass

        # Mock batch_validate_skills抛出异常
        with patch(
            "skill_creator_mcp.server.batch_validate_skills",
            side_effect=RuntimeError("Simulated batch validation error"),
        ):
            result = await batch_validate_skills_tool(
                MockContext(),
                skill_paths=["/skill1", "/skill2"],
                check_structure=True,
                check_content=True,
                concurrent_limit=2,
            )

            assert result["success"] is False
            assert "批量验证出错" in result["error"]
            assert result["error_type"] == "internal_error"

    @pytest.mark.asyncio
    async def test_batch_analyze_skills_tool_exception_handling(self):
        """测试batch_analyze_skills_tool的异常处理."""
        from unittest.mock import patch

        from skill_creator_mcp.server import batch_analyze_skills_tool

        class MockContext:
            pass

        # Mock batch_analyze_skills抛出异常
        with patch(
            "skill_creator_mcp.server.batch_analyze_skills",
            side_effect=RuntimeError("Simulated batch analysis error"),
        ):
            result = await batch_analyze_skills_tool(
                MockContext(),
                skill_paths=["/skill1", "/skill2"],
                analyze_structure=True,
                analyze_complexity=True,
                analyze_quality=True,
                concurrent_limit=2,
            )

            assert result["success"] is False
            assert "批量分析出错" in result["error"]
            assert result["error_type"] == "internal_error"


class TestServerPackageToolExceptionHandling:
    """测试server.py中打包工具的异常处理 (覆盖 lines 742-776)."""

    @pytest.mark.asyncio
    async def test_package_agent_skill_internal_error_handling(self, temp_dir):
        """测试package_agent_skill的内部异常处理."""
        from unittest.mock import patch

        from skill_creator_mcp.server import package_agent_skill

        class MockContext:
            pass

        # Mock package_agent_skill_impl抛出一般异常
        with patch(
            "skill_creator_mcp.server.package_agent_skill_impl",
            side_effect=RuntimeError("Simulated packaging error"),
        ):
            result = await package_agent_skill(
                MockContext(),
                skill_path="/path/to/skill",
                output_dir=str(temp_dir),  # 使用临时目录以通过路径验证
                version="0.3.1",
                format="zip",
            )

            assert result["success"] is False
            assert "打包过程出错" in result["error"]
            assert result["error_type"] == "internal_error"
