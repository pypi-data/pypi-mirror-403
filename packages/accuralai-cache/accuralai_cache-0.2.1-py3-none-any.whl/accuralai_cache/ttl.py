"""TTL-only cache with no size limits."""

from __future__ import annotations

import time
from typing import Any, Mapping

from pydantic import Field, ValidationError

from accuralai_core.contracts.errors import CacheError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse

from .base import BaseCache, CacheConfig, CacheEntry, extract_options


class TTLCacheOptions(CacheConfig):
    """Configuration options for TTL-only cache."""

    default_ttl_s: float = Field(default=3600.0, ge=0)
    eager_expiry: bool = True
    cleanup_interval_s: float | None = Field(
        default=None, ge=0, description="Interval for background cleanup (None = no background cleanup)"
    )


class TTLCache(BaseCache):
    """Cache that only uses TTL for eviction, no size limits."""

    def __init__(self, *, options: TTLCacheOptions | None = None) -> None:
        super().__init__(options=options)
        self.options: TTLCacheOptions = options or TTLCacheOptions()
        self._store: dict[str, CacheEntry] = {}

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        async with self._lock:
            if self.options.eager_expiry:
                self._evict_expired_locked()

            entry = self._store.get(key)
            if entry is None:
                self._mark_miss()
                return None

            if entry.expires_at is not None and entry.expires_at <= time.time():
                self._store.pop(key, None)
                self._mark_miss()
                return None

            self._mark_hit()
            return self._clone(entry.response)

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        expiry = self._compute_expiry(ttl_s)
        stored = value.model_copy(deep=True)
        async with self._lock:
            self._store[key] = CacheEntry(response=stored, expires_at=expiry)
            if self.options.eager_expiry:
                self._evict_expired_locked()

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def invalidate_prefix(self, prefix: str) -> None:
        async with self._lock:
            keys = [key for key in self._store.keys() if key.startswith(prefix)]
            for key in keys:
                self._store.pop(key, None)

    def _evict_expired_locked(self) -> None:
        """Remove expired entries."""
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


async def build_ttl_cache(
    *,
    config: Mapping[str, Any] | Any | None = None,
    **_: Any,
) -> TTLCache:
    """Factory for TTL-only cache."""
    try:
        options, _ = extract_options(config=config, options_model=TTLCacheOptions)
    except ValidationError as error:
        raise CacheError(f"Invalid TTL cache options: {error}") from error

    return TTLCache(options=options)

