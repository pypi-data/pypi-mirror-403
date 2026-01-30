"""健康检查和监控工具.

提供系统健康状态检查、性能监控和指标收集功能.
"""

import platform
import sys
import time
from datetime import datetime
from functools import lru_cache
from typing import Any

import psutil  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from skill_creator_mcp.logging_config import get_logger
from skill_creator_mcp.utils.cache import _global_cache

logger = get_logger(__name__)


class _PerformanceStats:
    """性能统计数据."""

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.response_times: list[float] = []


# 全局性能统计
_performance_stats = _PerformanceStats()


class HealthStatus(BaseModel):
    """健康状态."""

    status: str = Field(description="健康状态: healthy, degraded, unhealthy")
    timestamp: str = Field(description="检查时间")
    uptime_seconds: float = Field(description="运行时间(秒)")
    version: str = Field(description="版本号")


class SystemMetrics(BaseModel):
    """系统指标."""

    cpu_percent: float = Field(description="CPU使用率(%)")
    memory_percent: float = Field(description="内存使用率(%)")
    memory_used_mb: float = Field(description="已使用内存(MB)")
    memory_available_mb: float = Field(description="可用内存(MB)")
    disk_percent: float = Field(description="磁盘使用率(%)")
    disk_used_gb: float = Field(description="已使用磁盘(GB)")
    disk_free_gb: float = Field(description="可用磁盘(GB)")


class CacheMetrics(BaseModel):
    """缓存指标."""

    size: int = Field(description="缓存条目数")
    max_size: int = Field(description="最大缓存条目数")
    utilization_percent: float = Field(description="缓存利用率(%)")


class PerformanceMetrics(BaseModel):
    """性能指标."""

    total_requests: int = Field(description="总请求数")
    successful_requests: int = Field(description="成功请求数")
    failed_requests: int = Field(description="失败请求数")
    avg_response_time_ms: float = Field(description="平均响应时间(毫秒)")


class HealthCheckResult(BaseModel):
    """健康检查结果."""

    health: HealthStatus
    system: SystemMetrics
    cache: CacheMetrics
    performance: PerformanceMetrics
    environment: dict[str, Any] = Field(description="环境信息")


_start_time = time.time()


@lru_cache(maxsize=1)
def get_version() -> str:
    """获取版本号."""
    try:
        from skill_creator_mcp import __version__
        return __version__
    except ImportError:
        return "unknown"


def get_uptime() -> float:
    """获取运行时间."""
    return time.time() - _start_time


def get_system_metrics() -> SystemMetrics:
    """获取系统指标.

    Returns:
        系统指标数据
    """
    # CPU 信息
    cpu_percent = psutil.cpu_percent(interval=0.1)

    # 内存信息
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_used_mb = memory.used / (1024 * 1024)
    memory_available_mb = memory.available / (1024 * 1024)

    # 磁盘信息
    disk = psutil.disk_usage("/")
    disk_percent = disk.percent
    disk_used_gb = disk.used / (1024 * 1024 * 1024)
    disk_free_gb = disk.free / (1024 * 1024 * 1024)

    return SystemMetrics(
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        memory_used_mb=round(memory_used_mb, 2),
        memory_available_mb=round(memory_available_mb, 2),
        disk_percent=disk_percent,
        disk_used_gb=round(disk_used_gb, 2),
        disk_free_gb=round(disk_free_gb, 2),
    )


def get_cache_metrics() -> CacheMetrics:
    """获取缓存指标.

    Returns:
        缓存指标数据
    """
    stats = _global_cache.get_stats()
    return CacheMetrics(
        size=stats["size"],
        max_size=stats["max_size"],
        utilization_percent=round(stats["utilization"], 2),
    )


def get_performance_metrics() -> PerformanceMetrics:
    """获取性能指标.

    Returns:
        性能指标数据
    """
    total = _performance_stats.total_requests
    successful = _performance_stats.successful_requests
    failed = _performance_stats.failed_requests

    # 计算平均响应时间
    response_times = _performance_stats.response_times
    if response_times:
        avg_time = sum(response_times) / len(response_times) * 1000  # 转换为毫秒
    else:
        avg_time = 0.0

    return PerformanceMetrics(
        total_requests=total,
        successful_requests=successful,
        failed_requests=failed,
        avg_response_time_ms=round(avg_time, 2),
    )


def record_request(success: bool, response_time: float) -> None:
    """记录请求性能数据.

    Args:
        success: 请求是否成功
        response_time: 响应时间(秒)
    """
    _performance_stats.total_requests += 1
    if success:
        _performance_stats.successful_requests += 1
    else:
        _performance_stats.failed_requests += 1

    # 只保留最近1000次响应时间
    _performance_stats.response_times.append(response_time)
    if len(_performance_stats.response_times) > 1000:
        _performance_stats.response_times.pop(0)


def get_environment_info() -> dict[str, Any]:
    """获取环境信息.

    Returns:
        环境信息字典
    """
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def determine_health_status(system: SystemMetrics, performance: PerformanceMetrics) -> str:
    """确定健康状态.

    Args:
        system: 系统指标
        performance: 性能指标

    Returns:
        健康状态: healthy, degraded, unhealthy
    """
    # 检查关键资源使用率
    if system.cpu_percent > 90:
        return "unhealthy"
    if system.memory_percent > 90:
        return "unhealthy"
    if system.disk_percent > 95:
        return "unhealthy"

    # 检查失败率
    if performance.total_requests > 0:
        failure_rate = performance.failed_requests / performance.total_requests
        if failure_rate > 0.5:
            return "unhealthy"
        if failure_rate > 0.1:
            return "degraded"

    # 检查资源使用率是否较高
    if system.cpu_percent > 70 or system.memory_percent > 80:
        return "degraded"

    return "healthy"


def health_check() -> HealthCheckResult:
    """执行健康检查.

    Returns:
        健康检查结果
    """
    logger.debug("Executing health check")

    # 获取各项指标
    system = get_system_metrics()
    cache = get_cache_metrics()
    performance = get_performance_metrics()
    environment = get_environment_info()

    # 确定健康状态
    status = determine_health_status(system, performance)

    health = HealthStatus(
        status=status,
        timestamp=datetime.now().isoformat(),
        uptime_seconds=round(get_uptime(), 2),
        version=get_version(),
    )

    result = HealthCheckResult(
        health=health,
        system=system,
        cache=cache,
        performance=performance,
        environment=environment,
    )

    logger.info(f"Health check completed: status={status}")
    return result


def get_quick_status() -> str:
    """获取快速状态摘要.

    Returns:
        状态摘要字符串
    """
    system = get_system_metrics()
    performance = get_performance_metrics()
    status = determine_health_status(system, performance)

    uptime = get_uptime()
    uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m"

    return (
        f"Status: {status.upper()} | "
        f"Uptime: {uptime_str} | "
        f"CPU: {system.cpu_percent:.1f}% | "
        f"Memory: {system.memory_percent:.1f}% | "
        f"Requests: {performance.total_requests}"
    )


def reset_performance_stats() -> None:
    """重置性能统计数据."""
    global _performance_stats
    _performance_stats = _PerformanceStats()
    logger.info("Performance statistics reset")


def is_healthy() -> bool:
    """快速检查系统是否健康.

    Returns:
        是否健康
    """
    system = get_system_metrics()
    performance = get_performance_metrics()
    status = determine_health_status(system, performance)
    return status == "healthy"
