"""Redis-backed cache for distributed caching."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Mapping

from pydantic import Field, ValidationError

from accuralai_core.contracts.errors import CacheError
from accuralai_core.contracts.models import GenerateRequest, GenerateResponse

from .base import BaseCache, CacheConfig, extract_options


class RedisCacheOptions(CacheConfig):
    """Configuration settings for Redis cache."""

    host: str = Field(default="localhost")
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0)
    password: str | None = Field(default=None)
    socket_timeout: float = Field(default=5.0, ge=0)
    socket_connect_timeout: float = Field(default=5.0, ge=0)
    max_connections: int = Field(default=50, ge=1)
    key_prefix: str = Field(default="accuralai:cache:")
    decode_responses: bool = False  # Must be False for binary data


class RedisCache(BaseCache):
    """Redis-backed cache for distributed caching."""

    def __init__(self, *, options: RedisCacheOptions | None = None) -> None:
        super().__init__(options=options)
        self.options: RedisCacheOptions = options or RedisCacheOptions()
        self._client: Any = None  # aioredis.Redis
        self._connection_pool: Any = None  # aioredis.ConnectionPool

    async def _ensure_client(self) -> Any:
        """Ensure Redis client is initialized."""
        if self._client is None:
            try:
                import redis.asyncio as aioredis
            except ImportError as e:
                raise CacheError(
                    "redis package is required for Redis cache. Install with: pip install redis"
                ) from e

            self._connection_pool = aioredis.ConnectionPool(
                host=self.options.host,
                port=self.options.port,
                db=self.options.db,
                password=self.options.password,
                socket_timeout=self.options.socket_timeout,
                socket_connect_timeout=self.options.socket_connect_timeout,
                max_connections=self.options.max_connections,
                decode_responses=self.options.decode_responses,
            )
            self._client = aioredis.Redis(connection_pool=self._connection_pool)
        return self._client

    def _make_key(self, key: str) -> str:
        """Add prefix to cache key."""
        return f"{self.options.key_prefix}{key}"

    async def get(self, key: str, *, request: GenerateRequest) -> GenerateResponse | None:
        client = await self._ensure_client()
        cache_key = self._make_key(key)

        try:
            data = await client.get(cache_key)
            if data is None:
                self._mark_miss()
                return None

            # Deserialize JSON
            if isinstance(data, bytes):
                payload = json.loads(data.decode("utf-8"))
            else:
                payload = json.loads(data)

            response = GenerateResponse.model_validate(payload)
            self._mark_hit()
            return self._clone(response)
        except Exception as e:
            # Log error but don't fail - cache miss is acceptable
            self._mark_miss()
            return None

    async def set(self, key: str, value: GenerateResponse, *, ttl_s: int | None = None) -> None:
        client = await self._ensure_client()
        cache_key = self._make_key(key)

        # Serialize to JSON
        payload = value.model_dump()
        json_data = json.dumps(payload).encode("utf-8")

        # Resolve TTL
        ttl = self._resolve_ttl(ttl_s)
        ttl_int = int(ttl) if ttl is not None else None

        try:
            await client.set(cache_key, json_data, ex=ttl_int)
        except Exception as e:
            # Log error but don't fail - cache write failures are acceptable
            pass

    async def invalidate(self, key: str) -> None:
        client = await self._ensure_client()
        cache_key = self._make_key(key)
        try:
            await client.delete(cache_key)
        except Exception:
            pass

    async def invalidate_prefix(self, prefix: str) -> None:
        client = await self._ensure_client()
        pattern = self._make_key(f"{prefix}*")

        try:
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await client.delete(*keys)
        except Exception:
            pass

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()


async def build_redis_cache(
    *,
    config: Mapping[str, Any] | Any | None = None,
    **_: Any,
) -> RedisCache:
    """Factory for Redis cache."""
    try:
        options, _ = extract_options(config=config, options_model=RedisCacheOptions)
    except ValidationError as error:
        raise CacheError(f"Invalid Redis cache options: {error}") from error

    return RedisCache(options=options)

