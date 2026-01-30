"""缓存机制单元测试."""

import time

from skill_creator_mcp.utils.cache import (
    MemoryCache,
    cache_key,
    cached,
    hash_content,
)


class TestMemoryCache:
    """MemoryCache 测试."""

    def test_cache_set_and_get(self):
        """测试基本的缓存设置和获取."""
        cache = MemoryCache(max_size=10)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None

    def test_cache_ttl(self):
        """测试缓存过期."""
        cache = MemoryCache(max_size=10, default_ttl=1)

        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"

        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_max_size_eviction(self):
        """测试缓存容量限制和 LRU 淘汰."""
        cache = MemoryCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # 缓存已满
        assert cache.get_stats()["size"] == 3

        # 添加第4个项，应该淘汰最旧的
        cache.set("key4", "value4")
        assert cache.get_stats()["size"] == 3
        assert cache.get("key1") is None  # key1 被淘汰
        assert cache.get("key4") == "value4"

    def test_cache_delete(self):
        """测试删除缓存项."""
        cache = MemoryCache()

        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("nonexistent") is False

    def test_cache_clear(self):
        """测试清空缓存."""
        cache = MemoryCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()
        assert cache.get_stats()["size"] == 0

    def test_cache_stats(self):
        """测试缓存统计信息."""
        cache = MemoryCache(max_size=10)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 10
        assert 0 < stats["utilization"] < 100  # utilization 是百分比 0-100


class TestCacheDecorator:
    """缓存装饰器测试."""

    def test_cached_decorator(self):
        """测试缓存装饰器."""
        call_count = 0

        @cached(ttl=10)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # 第一次调用
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # 第二次调用应该从缓存获取
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # 没有增加

    def test_cached_with_different_args(self):
        """测试不同参数使用不同缓存."""
        @cached(ttl=10)
        def compute(x: int) -> int:
            return x * x

        result1 = compute(5)
        result2 = compute(10)

        assert result1 == 25
        assert result2 == 100

    def test_cached_with_prefix(self):
        """测试带前缀的缓存."""
        @cached(ttl=10, key_prefix="test")
        def get_value(x: int) -> int:
            return x + 1

        assert get_value(5) == 6

        # 相同的参数应该命中缓存
        assert get_value(5) == 6


class TestCacheUtilities:
    """缓存工具函数测试."""

    def test_cache_key_generation(self):
        """测试缓存键生成."""
        key1 = cache_key("arg1", "arg2", kwarg1="value1")
        key2 = cache_key("arg1", "arg2", kwarg1="value1")
        key3 = cache_key("arg1", "arg2", kwarg1="value2")

        # 相同参数生成相同的键
        assert key1 == key2
        # 不同参数生成不同的键
        assert key1 != key3

    def test_hash_content(self):
        """测试内容哈希."""
        content1 = "test content"
        content2 = "test content"
        content3 = "different content"

        hash1 = hash_content(content1)
        hash2 = hash_content(content2)
        hash3 = hash_content(content3)

        # 相同内容生成相同哈希
        assert hash1 == hash2
        # 不同内容生成不同哈希
        assert hash1 != hash3

        # 哈希值长度固定（SHA256）
        assert len(hash1) == 64


class TestCacheHitRate:
    """缓存命中率测试."""

    def test_high_hit_rate_scenario(self):
        """测试高命中率场景."""
        cache = MemoryCache(max_size=100)

        # 预填充缓存
        for i in range(50):
            cache.set(f"key{i}", f"value{i}")

        # 重复访问相同的项目
        hits = 0
        for _ in range(100):
            key = f"key{(_ % 50)}"
            if cache.get(key) is not None:
                hits += 1

        # 100% 命中率（因为我们只访问预填充的项目）
        assert hits == 100

    def test_cache_hit_rate_calculation(self):
        """测试缓存命中率计算."""
        cache = MemoryCache(max_size=10)

        # 第一次访问 - 未命中
        cache.get("key1")
        cache.set("key1", "value1")

        # 第二次访问 - 命中
        cache.get("key1")

        stats = cache.get_stats()
        # access_order 应该包含 key1
        assert "key1" in stats["access_order"]
