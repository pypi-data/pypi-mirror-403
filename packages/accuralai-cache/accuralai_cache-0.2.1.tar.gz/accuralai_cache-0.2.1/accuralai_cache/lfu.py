"""LFU (Least Frequently Used) cache implementation."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Mapping

from pydantic import Field, ValidationError

from accuralai_core.contracts.errors import CacheError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse

from .base import BaseCache, CacheConfig, CacheEntry, extract_options


class LFUCacheOptions(CacheConfig):
    """Configuration options for LFU cache."""

    max_entries: int = Field(default=128, ge=1)
    eager_expiry: bool = True


class LFUCache(BaseCache):
    """LFU (Least Frequently Used) cache with TTL support."""

    def __init__(self, *, options: LFUCacheOptions | None = None) -> None:
        super().__init__(options=options)
        self.options: LFUCacheOptions = options or LFUCacheOptions()
        self._store: dict[str, CacheEntry] = {}
        self._frequencies: dict[str, int] = defaultdict(int)
        self._frequency_groups: dict[int, set[str]] = defaultdict(set)
        self._min_frequency: int = 0

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        async with self._lock:
            if self.options.eager_expiry:
                self._evict_expired_locked()

            entry = self._store.get(key)
            if entry is None:
                self._mark_miss()
                return None

            # Check expiration
            if entry.expires_at is not None and entry.expires_at <= time.time():
                self._remove_key_locked(key)
                self._mark_miss()
                return None

            # Update frequency
            self._increment_frequency_locked(key)
            self._mark_hit()
            return self._clone(entry.response)

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        expiry = self._compute_expiry(ttl_s)
        stored = value.model_copy(deep=True)
        async with self._lock:
            # Remove key if it exists
            if key in self._store:
                self._remove_key_locked(key)

            # Add new entry
            self._store[key] = CacheEntry(response=stored, expires_at=expiry)
            self._frequencies[key] = 1
            self._frequency_groups[1].add(key)
            self._min_frequency = 1

            if self.options.eager_expiry:
                self._evict_expired_locked()
            self._enforce_capacity_locked()

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._remove_key_locked(key)

    async def invalidate_prefix(self, prefix: str) -> None:
        async with self._lock:
            keys = [key for key in self._store.keys() if key.startswith(prefix)]
            for key in keys:
                self._remove_key_locked(key)

    def _remove_key_locked(self, key: str) -> None:
        """Remove key from all data structures."""
        if key not in self._store:
            return

        freq = self._frequencies.pop(key)
        self._frequency_groups[freq].discard(key)

        # Update min frequency if needed
        if freq == self._min_frequency and not self._frequency_groups[freq]:
            self._min_frequency = min(self._frequency_groups.keys()) if self._frequency_groups else 0

        self._store.pop(key, None)

    def _increment_frequency_locked(self, key: str) -> None:
        """Increment frequency for a key."""
        old_freq = self._frequencies[key]
        new_freq = old_freq + 1

        # Move to new frequency group
        self._frequency_groups[old_freq].discard(key)
        self._frequency_groups[new_freq].add(key)
        self._frequencies[key] = new_freq

        # Update min frequency
        if old_freq == self._min_frequency and not self._frequency_groups[old_freq]:
            self._min_frequency = new_freq

    def _evict_lfu_locked(self) -> None:
        """Evict least frequently used item."""
        if not self._store:
            return

        # Find keys with minimum frequency
        lfu_keys = self._frequency_groups[self._min_frequency]
        if not lfu_keys:
            return

        # Remove first key (could be improved with LRU tie-breaker)
        key_to_remove = next(iter(lfu_keys))
        self._remove_key_locked(key_to_remove)

    def _enforce_capacity_locked(self) -> None:
        """Enforce capacity limit by evicting LFU items."""
        while len(self._store) > self.options.max_entries:
            self._evict_lfu_locked()

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
            self._remove_key_locked(key)


async def build_lfu_cache(
    *,
    config: Mapping[str, Any] | Any | None = None,
    **_: Any,
) -> LFUCache:
    """Factory for LFU cache."""
    try:
        options, _ = extract_options(config=config, options_model=LFUCacheOptions)
    except ValidationError as error:
        raise CacheError(f"Invalid LFU cache options: {error}") from error

    return LFUCache(options=options)

