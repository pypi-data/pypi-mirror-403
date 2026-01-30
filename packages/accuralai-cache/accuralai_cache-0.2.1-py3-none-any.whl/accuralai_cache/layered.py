"""Layered cache combining fast memory and durable disk storage."""

from __future__ import annotations

import asyncio
from typing import Any, Mapping

from pydantic import Field, ValidationError

from accuralai_core.contracts.errors import CacheError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse

from .base import BaseCache, CacheConfig, extract_options
from .disk import build_disk_cache
from .memory import build_memory_cache


class LayeredCacheOptions(CacheConfig):
    """Configuration payload for the layered cache."""

    memory: dict[str, Any] = Field(default_factory=dict)
    disk: dict[str, Any] = Field(default_factory=dict)
    promote_on_hit: bool = True


class LayeredCache(BaseCache):
    """Compose two cache implementations into an L1/L2 hierarchy."""

    def __init__(
        self,
        *,
        memory_cache,
        disk_cache,
        options: LayeredCacheOptions | None = None,
    ) -> None:
        super().__init__(options=options)
        self.options: LayeredCacheOptions = options or LayeredCacheOptions()
        self._memory = memory_cache
        self._disk = disk_cache

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        # First try the in-memory layer.
        result = await self._memory.get(key, request=request)
        if result is not None:
            self._mark_hit()
            return self._clone(result)

        # Fallback to disk. Promote on hit to keep hot items fast.
        disk_result = await self._disk.get(key, request=request)
        if disk_result is None:
            self._mark_miss()
            return None

        if self.options.promote_on_hit:
            await self._memory.set(key, disk_result)

        self._mark_hit()
        return self._clone(disk_result)

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        await asyncio.gather(
            self._memory.set(key, value, ttl_s=ttl_s),
            self._disk.set(key, value, ttl_s=ttl_s),
        )

    async def invalidate(self, key: str) -> None:
        await asyncio.gather(self._memory.invalidate(key), self._disk.invalidate(key))

    async def invalidate_prefix(self, prefix: str) -> None:
        await asyncio.gather(
            self._memory.invalidate_prefix(prefix),
            self._disk.invalidate_prefix(prefix),
        )


async def build_layered_cache(
    *,
    config: Mapping[str, Any] | Any | None = None,
    **_: Any,
) -> LayeredCache:
    """Factory constructing the layered cache."""
    try:
        options, ttl_override = extract_options(config=config, options_model=LayeredCacheOptions)
    except ValidationError as error:
        raise CacheError(f"Invalid layered cache options: {error}") from error

    memory_options = dict(options.memory)
    disk_options = dict(options.disk)

    if ttl_override is not None:
        memory_options.setdefault("default_ttl_s", float(ttl_override))
        disk_options.setdefault("default_ttl_s", float(ttl_override))

    memory_cache = await build_memory_cache(config=memory_options)
    disk_cache = await build_disk_cache(config=disk_options)

    return LayeredCache(memory_cache=memory_cache, disk_cache=disk_cache, options=options)
