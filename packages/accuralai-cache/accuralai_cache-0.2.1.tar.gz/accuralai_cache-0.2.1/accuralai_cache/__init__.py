"""Cache implementations for AccuralAI."""

from .base import BaseCache, CacheConfig
from .disk import DiskCache, DiskCacheOptions, build_disk_cache
from .file import FileCache, FileCacheOptions, build_file_cache
from .flexible_layered import (
    FlexibleLayeredCache,
    FlexibleLayeredCacheOptions,
    PromotionStrategy,
    WriteStrategy,
    build_flexible_layered_cache,
)
from .layered import LayeredCache, LayeredCacheOptions, build_layered_cache
from .lfu import LFUCache, LFUCacheOptions, build_lfu_cache
from .memory import (
    AdvancedMemoryCache,
    CacheOptions,
    MemoryCache,
    MemoryCacheOptions,
    build_memory_cache,
)
from .noop import NoOpCache, NoOpCacheOptions, build_noop_cache
from .redis import RedisCache, RedisCacheOptions, build_redis_cache
from .ttl import TTLCache, TTLCacheOptions, build_ttl_cache

__all__ = [
    "BaseCache",
    "CacheConfig",
    # Memory cache
    "AdvancedMemoryCache",
    "CacheOptions",
    "MemoryCache",
    "MemoryCacheOptions",
    "build_memory_cache",
    # Disk cache
    "DiskCache",
    "DiskCacheOptions",
    "build_disk_cache",
    # Layered cache
    "LayeredCache",
    "LayeredCacheOptions",
    "build_layered_cache",
    # Flexible layered cache
    "FlexibleLayeredCache",
    "FlexibleLayeredCacheOptions",
    "PromotionStrategy",
    "WriteStrategy",
    "build_flexible_layered_cache",
    # Redis cache
    "RedisCache",
    "RedisCacheOptions",
    "build_redis_cache",
    # LFU cache
    "LFUCache",
    "LFUCacheOptions",
    "build_lfu_cache",
    # TTL cache
    "TTLCache",
    "TTLCacheOptions",
    "build_ttl_cache",
    # File cache
    "FileCache",
    "FileCacheOptions",
    "build_file_cache",
    # No-op cache
    "NoOpCache",
    "NoOpCacheOptions",
    "build_noop_cache",
]
