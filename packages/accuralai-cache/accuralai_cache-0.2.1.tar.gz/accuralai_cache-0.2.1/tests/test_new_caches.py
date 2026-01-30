"""Tests for new cache implementations."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from accuralai_core.contracts.models import GenerateResponse, Usage
from accuralai_cache.lfu import LFUCache, LFUCacheOptions
from accuralai_cache.ttl import TTLCache, TTLCacheOptions
from accuralai_cache.file import FileCache, FileCacheOptions
from accuralai_cache.noop import NoOpCache, NoOpCacheOptions
from accuralai_cache.flexible_layered import (
    FlexibleLayeredCache,
    FlexibleLayeredCacheOptions,
    PromotionStrategy,
    WriteStrategy,
)


@pytest.fixture
def sample_response() -> GenerateResponse:
    """Create a sample response for testing."""
    return GenerateResponse(
        id=uuid4(),
        request_id=uuid4(),
        output_text="test response",
        finish_reason="stop",
        usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        latency_ms=100,
        metadata={},
        validator_events=[],
    )


@pytest.mark.anyio
async def test_lfu_cache_eviction(sample_response: GenerateResponse) -> None:
    """Test LFU cache evicts least frequently used items."""
    cache = LFUCache(options=LFUCacheOptions(max_entries=2))

    # Add two items
    await cache.set("key1", sample_response)
    await cache.set("key2", sample_response)

    # Access key1 multiple times
    await cache.get("key1", request=MagicMock())
    await cache.get("key1", request=MagicMock())
    await cache.get("key1", request=MagicMock())

    # Add third item - should evict key2 (less frequently used)
    await cache.set("key3", sample_response)

    # key2 should be evicted
    result = await cache.get("key2", request=MagicMock())
    assert result is None

    # key1 and key3 should still be present
    assert await cache.get("key1", request=MagicMock()) is not None
    assert await cache.get("key3", request=MagicMock()) is not None


@pytest.mark.anyio
async def test_ttl_cache_no_size_limit(sample_response: GenerateResponse) -> None:
    """Test TTL cache has no size limits."""
    cache = TTLCache(options=TTLCacheOptions(default_ttl_s=3600.0))

    # Add many items (should not evict based on size)
    for i in range(1000):
        await cache.set(f"key{i}", sample_response)

    # All should still be present
    for i in range(1000):
        result = await cache.get(f"key{i}", request=MagicMock())
        assert result is not None


@pytest.mark.anyio
async def test_file_cache_persistence(tmp_path, sample_response: GenerateResponse) -> None:
    """Test file cache persists to disk."""
    cache_dir = tmp_path / "cache"
    cache = FileCache(options=FileCacheOptions(directory=str(cache_dir)))

    await cache.set("test_key", sample_response)
    result = await cache.get("test_key", request=MagicMock())

    assert result is not None
    assert result.output_text == sample_response.output_text

    # Verify file exists
    cache_files = list(cache_dir.glob("*.json"))
    assert len(cache_files) == 1


@pytest.mark.anyio
async def test_noop_cache_always_misses(sample_response: GenerateResponse) -> None:
    """Test no-op cache never stores anything."""
    cache = NoOpCache(options=NoOpCacheOptions())

    await cache.set("key", sample_response)
    result = await cache.get("key", request=MagicMock())

    assert result is None
    assert cache.stats["misses"] >= 1


@pytest.mark.anyio
async def test_flexible_layered_cache_multiple_layers(
    sample_response: GenerateResponse,
) -> None:
    """Test flexible layered cache with multiple layers."""
    from accuralai_cache.memory import MemoryCache, MemoryCacheOptions
    from accuralai_cache.ttl import TTLCache, TTLCacheOptions

    memory_cache = MemoryCache(options=MemoryCacheOptions(max_entries=10))
    ttl_cache = TTLCache(options=TTLCacheOptions(default_ttl_s=3600.0))

    # Create layer wrappers
    layer1 = type("Layer", (), {"name": "memory", "priority": 0, "cache": memory_cache})()
    layer2 = type("Layer", (), {"name": "ttl", "priority": 1, "cache": ttl_cache})()

    cache = FlexibleLayeredCache(
        layers=[layer1, layer2],
        options=FlexibleLayeredCacheOptions(),
    )

    # Set in cache
    await cache.set("test_key", sample_response)

    # Should be retrievable
    result = await cache.get("test_key", request=MagicMock())
    assert result is not None


@pytest.mark.anyio
async def test_flexible_layered_promotion_strategy(
    sample_response: GenerateResponse,
) -> None:
    """Test flexible layered cache promotion strategies."""
    from accuralai_cache.memory import MemoryCache, MemoryCacheOptions
    from accuralai_cache.ttl import TTLCache, TTLCacheOptions

    memory_cache = MemoryCache(options=MemoryCacheOptions(max_entries=10))
    ttl_cache = TTLCache(options=TTLCacheOptions(default_ttl_s=3600.0))

    layer1 = type("Layer", (), {"name": "memory", "priority": 0, "cache": memory_cache})()
    layer2 = type("Layer", (), {"name": "ttl", "priority": 1, "cache": ttl_cache})()

    # Test NEVER strategy
    cache = FlexibleLayeredCache(
        layers=[layer1, layer2],
        options=FlexibleLayeredCacheOptions(promotion_strategy=PromotionStrategy.NEVER),
    )

    # Set in ttl cache (layer2)
    await ttl_cache.set("test_key", sample_response)

    # Get from cache (should hit layer2)
    result = await cache.get("test_key", request=MagicMock())
    assert result is not None

    # Should NOT be promoted to memory cache
    memory_result = await memory_cache.get("test_key", request=MagicMock())
    assert memory_result is None


@pytest.mark.anyio
async def test_flexible_layered_write_strategies(
    sample_response: GenerateResponse,
) -> None:
    """Test flexible layered cache write strategies."""
    from accuralai_cache.memory import MemoryCache, MemoryCacheOptions
    from accuralai_cache.ttl import TTLCache, TTLCacheOptions

    memory_cache = MemoryCache(options=MemoryCacheOptions(max_entries=10))
    ttl_cache = TTLCache(options=TTLCacheOptions(default_ttl_s=3600.0))

    layer1 = type("Layer", (), {"name": "memory", "priority": 0, "cache": memory_cache})()
    layer2 = type("Layer", (), {"name": "ttl", "priority": 1, "cache": ttl_cache})()

    # Test WRITE_AROUND strategy (skip fast layer)
    cache = FlexibleLayeredCache(
        layers=[layer1, layer2],
        options=FlexibleLayeredCacheOptions(write_strategy=WriteStrategy.WRITE_AROUND),
    )

    await cache.set("test_key", sample_response)

    # Should be in ttl cache but not memory cache
    ttl_result = await ttl_cache.get("test_key", request=MagicMock())
    assert ttl_result is not None

    memory_result = await memory_cache.get("test_key", request=MagicMock())
    assert memory_result is None

