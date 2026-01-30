"""In-memory cache implementations."""


from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Mapping

from pydantic import Field, ValidationError

from accuralai_core.contracts.errors import CacheError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse

from .base import BaseCache, CacheConfig, CacheEntry, extract_options


class MemoryCacheOptions(CacheConfig):
    """Configuration options for in-memory cache behaviour."""

    max_entries: int | None = Field(default=None, ge=1)
    eager_expiry: bool = True


class MemoryCache(BaseCache):
    """LRU-style cache with TTL support."""

    def __init__(self, *, options: MemoryCacheOptions | None = None) -> None:
        super().__init__(options=options)
        self.options: MemoryCacheOptions = options or MemoryCacheOptions()
        self._store: "OrderedDict[str, CacheEntry]" = OrderedDict()

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        async with self._lock:
            if self.options.eager_expiry:
                self._evict_expired_locked()

            item = self._store.get(key)
            if item is None:
                self._mark_miss()
                return None

            entry = item
            if entry.expires_at is not None and entry.expires_at <= time.time():
                self._store.pop(key, None)
                self._mark_miss()
                return None

            self._store.move_to_end(key)
            self._mark_hit()
            return self._clone(entry.response)

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        expiry = self._compute_expiry(ttl_s)
        stored = value.model_copy(deep=True)
        async with self._lock:
            self._store[key] = CacheEntry(response=stored, expires_at=expiry)
            self._store.move_to_end(key)
            if self.options.eager_expiry:
                self._evict_expired_locked()
            self._enforce_capacity_locked()

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def invalidate_prefix(self, prefix: str) -> None:
        async with self._lock:
            keys = [key for key in self._store.keys() if key.startswith(prefix)]
            for key in keys:
                self._store.pop(key, None)

    def _enforce_capacity_locked(self) -> None:
        max_entries = self.options.max_entries
        if max_entries is None:
            return
        while len(self._store) > max_entries:
            self._store.popitem(last=False)

    def _evict_expired_locked(self) -> None:
        if not self._store:
            return
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self._store.items()
            if entry.expires_at is not None and entry.expires_at <= current_time
        ]
        for key in expired_keys:
            self._store.pop(key, None)


async def build_memory_cache(
    *,
    config: Mapping[str, Any] | Any | None = None,
    **_: Any,
) -> MemoryCache:
    """Factory for registering the advanced memory cache."""
    try:
        options, _ = extract_options(config=config, options_model=MemoryCacheOptions)
    except ValidationError as error:
        raise CacheError(f"Invalid cache options: {error}") from error

    return MemoryCache(options=options)


# Backwards compatibility re-export for older imports.
AdvancedMemoryCache = MemoryCache
CacheOptions = MemoryCacheOptions
