"""Shared cache abstractions and helpers."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, Field

from accuralai_core.contracts.models import GenerateResponse
from accuralai_core.contracts.protocols import Cache


class CacheConfig(BaseModel):
    """Base configuration shared across cache implementations."""

    default_ttl_s: float | None = Field(default=None, ge=0)
    copy_on_get: bool = True
    stats_enabled: bool = False


@dataclass(slots=True)
class CacheEntry:
    """Internal representation of a cached response."""

    response: GenerateResponse
    expires_at: float | None = None


class BaseCache(Cache):
    """Helper base class that offers TTL resolution and cloning behaviour."""

    def __init__(self, *, options: CacheConfig | None = None) -> None:
        self.options = options or CacheConfig()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict[str, int]:
        """Return cache hit/miss counters."""
        return {"hits": self._hits, "misses": self._misses}

    def _resolve_ttl(self, ttl_s: Optional[int]) -> Optional[float]:
        if ttl_s is not None:
            return float(ttl_s)
        return self.options.default_ttl_s

    def _compute_expiry(self, ttl_s: Optional[int]) -> Optional[float]:
        resolved = self._resolve_ttl(ttl_s)
        if resolved is None:
            return None
        return time.time() + resolved

    def _clone(self, response: GenerateResponse) -> GenerateResponse:
        if self.options.copy_on_get:
            return response.model_copy(deep=True)
        return response

    def _mark_hit(self) -> None:
        if self.options.stats_enabled:
            self._hits += 1

    def _mark_miss(self) -> None:
        if self.options.stats_enabled:
            self._misses += 1

    async def invalidate_prefix(self, prefix: str) -> None:
        """Optional hook for derived caches; default routes to individual invalidation."""
        raise NotImplementedError("invalidate_prefix is not implemented for this cache")


def extract_options(
    *,
    config: Any,
    options_model: type[CacheConfig],
) -> tuple[CacheConfig, Optional[int]]:
    """Normalize configuration payloads from core settings or dicts."""
    options_payload: dict[str, Any] = {}
    ttl_override: int | None = None

    if config is None:
        pass
    elif hasattr(config, "options"):
        # CacheSettings from accuralai-core
        options_payload = dict(getattr(config, "options") or {})
        ttl_override = getattr(config, "ttl_s", None)
    elif isinstance(config, dict):
        options_payload = dict(config)
        ttl_override = options_payload.pop("ttl_s", None)
    else:
        raise TypeError(f"Unsupported cache configuration type: {type(config)!r}")

    options = options_model.model_validate(options_payload)

    if ttl_override is not None and options.default_ttl_s is None:
        options.default_ttl_s = float(ttl_override)

    return options, ttl_override
