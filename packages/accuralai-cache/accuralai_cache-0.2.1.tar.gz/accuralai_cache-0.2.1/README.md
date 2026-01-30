# AccuralAI Cache Package

Caching providers for the AccuralAI LLM pipeline.

## Available Cache Types

### Memory Cache (LRU)
In-memory cache with LRU eviction policy.

```python
from accuralai_cache import MemoryCache, MemoryCacheOptions

cache = MemoryCache(options=MemoryCacheOptions(
    max_entries=512,
    eager_expiry=True
))
```

### Disk Cache (SQLite)
Persistent cache using SQLite database.

```python
from accuralai_cache import DiskCache, DiskCacheOptions

cache = DiskCache(options=DiskCacheOptions(
    path=".cache/accuralai.sqlite",
    size_limit_mb=256
))
```

### Redis Cache
Distributed cache using Redis (requires `redis` package).

```bash
pip install accuralai-cache[redis]
```

```python
from accuralai_cache import RedisCache, RedisCacheOptions

cache = RedisCache(options=RedisCacheOptions(
    host="localhost",
    port=6379,
    key_prefix="accuralai:cache:"
))
```

### LFU Cache
Least Frequently Used cache with configurable eviction.

```python
from accuralai_cache import LFUCache, LFUCacheOptions

cache = LFUCache(options=LFUCacheOptions(
    max_entries=128,
    eager_expiry=True
))
```

### TTL Cache
Cache that only uses TTL for eviction (no size limits).

```python
from accuralai_cache import TTLCache, TTLCacheOptions

cache = TTLCache(options=TTLCacheOptions(
    default_ttl_s=3600.0,
    eager_expiry=True
))
```

### File Cache
Human-readable JSON file-based cache.

```python
from accuralai_cache import FileCache, FileCacheOptions

cache = FileCache(options=FileCacheOptions(
    directory=".cache/accuralai-file",
    max_files=1000
))
```

### No-Op Cache
Cache that doesn't store anything (for testing/development).

```python
from accuralai_cache import NoOpCache

cache = NoOpCache()
```

### Layered Cache
Combines memory and disk caches.

```python
from accuralai_cache import build_layered_cache

cache = await build_layered_cache(config={
    "memory": {"max_entries": 512},
    "disk": {"path": ".cache/accuralai.sqlite"},
    "promote_on_hit": True
})
```

### Flexible Layered Cache
Advanced layered cache supporting multiple layers and configurable strategies.

```python
from accuralai_cache import build_flexible_layered_cache, PromotionStrategy, WriteStrategy

cache = await build_flexible_layered_cache(config={
    "layers": [
        {"type": "memory", "name": "l1", "priority": 0, "options": {"max_entries": 128}},
        {"type": "redis", "name": "l2", "priority": 1, "options": {"host": "localhost"}},
        {"type": "disk", "name": "l3", "priority": 2, "options": {"path": ".cache/db.sqlite"}},
    ],
    "promotion_strategy": "always",  # or "never", "frequency_based"
    "write_strategy": "write_through",  # or "write_back", "write_around"
    "promotion_threshold": 2
})
```

## Configuration

All caches support common configuration options:

- `default_ttl_s`: Default TTL in seconds
- `copy_on_get`: Whether to clone responses on get
- `stats_enabled`: Enable hit/miss statistics

## Usage

```python
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse
from accuralai_cache import MemoryCache, MemoryCacheOptions

cache = MemoryCache(options=MemoryCacheOptions(max_entries=100))

# Store a response
response = GenerateResponse(...)
await cache.set("cache_key", response, ttl_s=300)

# Retrieve
request = GenerateRequest(prompt="test")
cached = await cache.get("cache_key", request=request)

# Invalidate
await cache.invalidate("cache_key")
await cache.invalidate_prefix("prefix:")
```
