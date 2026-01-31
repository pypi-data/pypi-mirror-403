"""缓存机制模块.

提供基于 LRU 算法的内存缓存和可选的磁盘缓存，用于提高重复操作的性能。
"""

import hashlib
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from skill_creator_mcp.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CacheEntry(BaseModel):
    """缓存条目."""

    key: str
    value: Any
    ttl: int | None = None
    created_at: float
    access_count: int = 0
    last_accessed: float


class MemoryCache:
    """内存缓存管理器.

    使用 LRU (Least Recently Used) 策略管理缓存。
    """

    def __init__(self, max_size: int | None = None, default_ttl: int | None = None):
        """初始化内存缓存.

        Args:
            max_size: 最大缓存条目数（None 时从配置获取）
            default_ttl: 默认过期时间（秒）（None 时从配置获取）
        """
        from ..config import get_config
        config = get_config()
        self.max_size = max_size if max_size is not None else config.cache_size
        self.default_ttl = default_ttl if default_ttl is not None else config.cache_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []

    def get(self, key: str, default: T | None = None) -> T | None:
        """获取缓存值.

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存的值，如果不存在或已过期则返回默认值
        """
        if key not in self._cache:
            return default

        entry = self._cache[key]

        # 检查是否过期
        if entry.ttl is not None:
            import time
            if time.time() - entry.created_at > entry.ttl:
                self.delete(key)
                return default

        # 更新访问信息
        entry.access_count += 1
        entry.last_accessed = entry.created_at  # 简化：使用创建时间

        # 更新访问顺序（LRU）
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"Cache hit: {key} (access count: {entry.access_count})")
        result: T | None = entry.value
        return result

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """设置缓存值.

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示使用默认值
        """
        import time

        # 如果缓存已满，删除最久未使用的项
        if len(self._cache) >= self.max_size and key not in self._cache:
            if self._access_order:
                oldest_key = self._access_order.pop(0)
                self.delete(oldest_key)
                logger.debug(f"Cache evicted (LRU): {oldest_key}")

        entry = CacheEntry(
            key=key,
            value=value,
            ttl=ttl or self.default_ttl,
            created_at=time.time(),
            access_count=0,
            last_accessed=time.time(),
        )

        self._cache[key] = entry
        if key not in self._access_order:
            self._access_order.append(key)

        logger.debug(f"Cache set: {key} (TTL: {entry.ttl}s)")

    def delete(self, key: str) -> bool:
        """删除缓存值.

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            logger.debug(f"Cache deleted: {key}")
            return True
        return False

    def clear(self) -> None:
        """清空所有缓存."""
        self._cache.clear()
        self._access_order.clear()
        logger.debug("Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息.

        Returns:
            包含缓存统计的字典
        """
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "utilization": len(self._cache) / self.max_size * 100,  # 百分比 0-100
            "access_order": self._access_order.copy(),
        }


# 全局内存缓存实例
_global_cache = MemoryCache()


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
) -> Callable:
    """缓存装饰器.

    Args:
        ttl: 过期时间（秒）
        key_prefix: 缓存键前缀

    Returns:
        装饰器函数

    Example:
        ```python
        @cached(ttl=600, key_prefix="resource")
        def get_resource(key: str) -> str:
            return fetch_resource(key)
        ```
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # 生成缓存键
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.extend(
                    f"{k}={v}" for k, v in sorted(kwargs.items())
                )
            cache_key = ":".join(key_parts)

            # 尝试从缓存获取
            cached_value = _global_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl=ttl)
            return result

        return wrapper

    return decorator


def cache_key(*args: Any, **kwargs: Any) -> str:
    """生成缓存键.

    Args:
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        缓存键字符串
    """
    key_parts: list[str] = []
    if args:
        key_parts.extend(str(arg) for arg in args)
    if kwargs:
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    # MD5仅用于缓存键生成，非安全场景
    return hashlib.md5(":".join(key_parts).encode(), usedforsecurity=False).hexdigest()


def hash_content(content: str) -> str:
    """计算内容哈希值.

    Args:
        content: 内容字符串

    Returns:
        哈希值（hex 格式）
    """
    return hashlib.sha256(content.encode()).hexdigest()
