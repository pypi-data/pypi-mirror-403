"""Flexible layered cache supporting multiple layers and configurable strategies."""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import Any, Callable, Literal, Mapping

from pydantic import Field, ValidationError

from accuralai_core.contracts.errors import CacheError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse

from .base import BaseCache, CacheConfig, extract_options


class PromotionStrategy(str, Enum):
    """Strategies for promoting cache hits to faster layers."""

    ALWAYS = "always"  # Always promote on hit
    NEVER = "never"  # Never promote
    FREQUENCY_BASED = "frequency_based"  # Promote based on access frequency


class WriteStrategy(str, Enum):
    """Strategies for writing to cache layers."""

    WRITE_THROUGH = "write_through"  # Write to all layers synchronously
    WRITE_BACK = "write_back"  # Write to fast layer, async write to slow layers
    WRITE_AROUND = "write_around"  # Write only to slow layer, skip fast layer


class LayerConfig:
    """Configuration for a single cache layer."""

    def __init__(self, name: str, cache: Any, priority: int = 0) -> None:
        self.name = name
        self.cache = cache
        self.priority = priority


class FlexibleLayeredCacheOptions(CacheConfig):
    """Configuration for flexible layered cache."""

    layers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of layer configurations",
    )
    promotion_strategy: PromotionStrategy = Field(
        default=PromotionStrategy.ALWAYS,
        description="Strategy for promoting hits to faster layers",
    )
    write_strategy: WriteStrategy = Field(
        default=WriteStrategy.WRITE_THROUGH,
        description="Strategy for writing to layers",
    )
    promotion_threshold: int = Field(
        default=2,
        ge=1,
        description="Access count threshold for frequency-based promotion",
    )


class FlexibleLayeredCache(BaseCache):
    """Flexible layered cache supporting multiple layers and strategies."""

    def __init__(
        self,
        *,
        layers: list[Any] | None = None,
        options: FlexibleLayeredCacheOptions | None = None,
    ) -> None:
        super().__init__(options=options)
        self.options: FlexibleLayeredCacheOptions = options or FlexibleLayeredCacheOptions()
        self._layers: list[Any] = layers or []
        self._access_counts: dict[str, dict[str, int]] = {}  # key -> {layer_name: count}

        # Sort layers by priority (lower priority number = checked first)
        if layers:
            self._layers = sorted(layers, key=lambda l: getattr(l, "priority", 0))

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        """Get from layers in priority order."""
        # Try layers in priority order
        for layer in self._layers:
            cache = getattr(layer, "cache", layer) if hasattr(layer, "cache") else layer
            result = await cache.get(key, request=request)
            if result is not None:
                self._mark_hit()
                self._record_access(key, getattr(layer, "name", "unknown"))
                await self._maybe_promote(key, result, layer)
                return self._clone(result)

        self._mark_miss()
        return None

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        """Set in layers according to write strategy."""
        if self.options.write_strategy == WriteStrategy.WRITE_THROUGH:
            # Write to all layers synchronously
            await asyncio.gather(
                *[
                    self._write_to_layer(layer, key, value, ttl_s)
                    for layer in self._layers
                ]
            )
        elif self.options.write_strategy == WriteStrategy.WRITE_BACK:
            # Write to fast layer, async write to slow layers
            if self._layers:
                fast_layer = self._layers[0]
                await self._write_to_layer(fast_layer, key, value, ttl_s)
                # Write to remaining layers in background
                if len(self._layers) > 1:
                    asyncio.create_task(
                        asyncio.gather(
                            *[
                                self._write_to_layer(layer, key, value, ttl_s)
                                for layer in self._layers[1:]
                            ]
                        )
                    )
        elif self.options.write_strategy == WriteStrategy.WRITE_AROUND:
            # Write only to slow layer (skip fast layer)
            if len(self._layers) > 1:
                await asyncio.gather(
                    *[
                        self._write_to_layer(layer, key, value, ttl_s)
                        for layer in self._layers[1:]
                    ]
                )
            elif self._layers:
                # Only one layer, write to it
                await self._write_to_layer(self._layers[0], key, value, ttl_s)

    async def invalidate(self, key: str) -> None:
        """Invalidate key in all layers."""
        await asyncio.gather(*[self._invalidate_layer(layer, key) for layer in self._layers])
        self._access_counts.pop(key, None)

    async def invalidate_prefix(self, prefix: str) -> None:
        """Invalidate prefix in all layers."""
        await asyncio.gather(
            *[self._invalidate_prefix_layer(layer, prefix) for layer in self._layers]
        )

    async def _write_to_layer(
        self,
        layer: Any,
        key: str,
        value: GenerateResponse,
        ttl_s: int | None,
    ) -> None:
        """Write to a specific layer."""
        cache = getattr(layer, "cache", layer) if hasattr(layer, "cache") else layer
        await cache.set(key, value, ttl_s=ttl_s)

    async def _invalidate_layer(self, layer: Any, key: str) -> None:
        """Invalidate key in a specific layer."""
        cache = getattr(layer, "cache", layer) if hasattr(layer, "cache") else layer
        await cache.invalidate(key)

    async def _invalidate_prefix_layer(self, layer: Any, prefix: str) -> None:
        """Invalidate prefix in a specific layer."""
        cache = getattr(layer, "cache", layer) if hasattr(layer, "cache") else layer
        if hasattr(cache, "invalidate_prefix"):
            await cache.invalidate_prefix(prefix)

    async def _maybe_promote(
        self,
        key: str,
        value: GenerateResponse,
        hit_layer: Any,
    ) -> None:
        """Promote value to faster layers if strategy allows."""
        if self.options.promotion_strategy == PromotionStrategy.NEVER:
            return

        hit_layer_name = getattr(hit_layer, "name", "unknown")
        hit_layer_index = next(
            (i for i, l in enumerate(self._layers) if getattr(l, "name", None) == hit_layer_name),
            None,
        )

        if hit_layer_index is None or hit_layer_index == 0:
            # Already in fastest layer or couldn't find layer
            return

        # Check if should promote
        should_promote = False
        if self.options.promotion_strategy == PromotionStrategy.ALWAYS:
            should_promote = True
        elif self.options.promotion_strategy == PromotionStrategy.FREQUENCY_BASED:
            counts = self._access_counts.get(key, {})
            total_accesses = sum(counts.values())
            if total_accesses >= self.options.promotion_threshold:
                should_promote = True

        if should_promote:
            # Promote to faster layers
            for i in range(hit_layer_index):
                faster_layer = self._layers[i]
                await self._write_to_layer(faster_layer, key, value, ttl_s=None)

    def _record_access(self, key: str, layer_name: str) -> None:
        """Record access to a key in a layer."""
        if key not in self._access_counts:
            self._access_counts[key] = {}
        self._access_counts[key][layer_name] = self._access_counts[key].get(layer_name, 0) + 1


async def build_flexible_layered_cache(
    *,
    config: Mapping[str, Any] | Any | None = None,
    **_: Any,
) -> FlexibleLayeredCache:
    """Factory for flexible layered cache."""
    try:
        options, _ = extract_options(config=config, options_model=FlexibleLayeredCacheOptions)
    except ValidationError as error:
        raise CacheError(f"Invalid flexible layered cache options: {error}") from error

    # Build layers from config
    layers = []
    for layer_config in options.layers:
        layer_type = layer_config.get("type", "memory")
        layer_options = layer_config.get("options", {})
        layer_name = layer_config.get("name", layer_type)
        layer_priority = layer_config.get("priority", len(layers))

        # Build cache based on type
        if layer_type == "memory":
            from .memory import build_memory_cache

            cache = await build_memory_cache(config=layer_options)
        elif layer_type == "disk":
            from .disk import build_disk_cache

            cache = await build_disk_cache(config=layer_options)
        elif layer_type == "redis":
            from .redis import build_redis_cache

            cache = await build_redis_cache(config=layer_options)
        elif layer_type == "file":
            from .file import build_file_cache

            cache = await build_file_cache(config=layer_options)
        elif layer_type == "lfu":
            from .lfu import build_lfu_cache

            cache = await build_lfu_cache(config=layer_options)
        elif layer_type == "ttl":
            from .ttl import build_ttl_cache

            cache = await build_ttl_cache(config=layer_options)
        else:
            raise CacheError(f"Unknown layer type: {layer_type}")

        # Create layer wrapper
        layer = type("Layer", (), {"name": layer_name, "priority": layer_priority, "cache": cache})()
        layers.append(layer)

    return FlexibleLayeredCache(layers=layers, options=options)

