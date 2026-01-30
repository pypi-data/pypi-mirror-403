"""No-op cache implementation for testing and development."""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import ValidationError

from accuralai_core.contracts.errors import CacheError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse

from .base import BaseCache, CacheConfig, extract_options


class NoOpCacheOptions(CacheConfig):
    """Configuration options for no-op cache (all options ignored)."""

    pass


class NoOpCache(BaseCache):
    """No-op cache that doesn't store anything (for testing/development)."""

    def __init__(self, *, options: NoOpCacheOptions | None = None) -> None:
        super().__init__(options=options or NoOpCacheOptions())

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        self._mark_miss()
        return None

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        # Do nothing
        pass

    async def invalidate(self, key: str) -> None:
        # Do nothing
        pass

    async def invalidate_prefix(self, prefix: str) -> None:
        # Do nothing
        pass


async def build_noop_cache(
    *,
    config: Mapping[str, Any] | Any | None = None,
    **_: Any,
) -> NoOpCache:
    """Factory for no-op cache."""
    try:
        options, _ = extract_options(config=config, options_model=NoOpCacheOptions)
    except ValidationError as error:
        raise CacheError(f"Invalid no-op cache options: {error}") from error

    return NoOpCache(options=options)

