import asyncio

import pytest

from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage

from accuralai_cache.memory import MemoryCache, MemoryCacheOptions, build_memory_cache


def _make_response(request: GenerateRequest, text: str) -> GenerateResponse:
    return GenerateResponse(
        id=request.id,
        request_id=request.id,
        output_text=text,
        finish_reason="stop",
        usage=Usage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        latency_ms=0,
    )


@pytest.mark.anyio("asyncio")
async def test_memory_cache_get_set():
    cache = MemoryCache(options=MemoryCacheOptions(copy_on_get=True))
    request = GenerateRequest(prompt="hello")
    response = _make_response(request, "result")

    await cache.set("key", response)
    cached = await cache.get("key", request=request)

    assert cached is not None
    assert cached.output_text == "result"
    assert cached is not response  # copy_on_get should clone


@pytest.mark.anyio("asyncio")
async def test_memory_cache_ttl_expires():
    cache = MemoryCache(options=MemoryCacheOptions(default_ttl_s=0.2))
    request = GenerateRequest(prompt="hello")
    await cache.set("key", _make_response(request, "value"))

    assert await cache.get("key", request=request) is not None
    await asyncio.sleep(0.3)
    assert await cache.get("key", request=request) is None


@pytest.mark.anyio("asyncio")
async def test_memory_cache_enforces_capacity():
    cache = MemoryCache(options=MemoryCacheOptions(max_entries=2))
    request = GenerateRequest(prompt="hello")

    await cache.set("k1", _make_response(request, "v1"))
    await cache.set("k2", _make_response(request, "v2"))
    await cache.set("k3", _make_response(request, "v3"))  # should evict k1

    assert await cache.get("k1", request=request) is None
    assert await cache.get("k2", request=request) is not None
    assert await cache.get("k3", request=request) is not None


@pytest.mark.anyio("asyncio")
async def test_build_memory_cache_from_settings():
    cache = await build_memory_cache(config={"default_ttl_s": 0.5, "max_entries": 5})
    request = GenerateRequest(prompt="hello")
    await cache.set("test", _make_response(request, "value"))
    assert await cache.get("test", request=request) is not None


@pytest.mark.anyio("asyncio")
async def test_memory_cache_invalidate_prefix():
    cache = MemoryCache(options=MemoryCacheOptions())
    request = GenerateRequest(prompt="hello")
    await cache.set("user:1", _make_response(request, "v1"))
    await cache.set("user:2", _make_response(request, "v2"))
    await cache.invalidate_prefix("user:")
    assert await cache.get("user:1", request=request) is None
    assert await cache.get("user:2", request=request) is None
