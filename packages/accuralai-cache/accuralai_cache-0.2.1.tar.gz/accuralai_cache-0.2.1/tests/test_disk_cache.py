import asyncio
from pathlib import Path

import pytest

from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage

from accuralai_cache.disk import DiskCache, DiskCacheOptions, build_disk_cache


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
async def test_disk_cache_round_trip(tmp_path: Path):
    cache_file = tmp_path / "cache.sqlite"
    cache = DiskCache(options=DiskCacheOptions(path=str(cache_file)))
    request = GenerateRequest(prompt="hello")
    response = _make_response(request, "stored")

    await cache.set("key", response)
    cached = await cache.get("key", request=request)

    assert cached is not None
    assert cached.output_text == "stored"


@pytest.mark.anyio("asyncio")
async def test_disk_cache_respects_ttl(tmp_path: Path):
    cache_file = tmp_path / "cache.sqlite"
    cache = DiskCache(options=DiskCacheOptions(path=str(cache_file), default_ttl_s=0.2))
    request = GenerateRequest(prompt="hello")
    await cache.set("key", _make_response(request, "value"))

    assert await cache.get("key", request=request) is not None
    await asyncio.sleep(0.3)
    assert await cache.get("key", request=request) is None


@pytest.mark.anyio("asyncio")
async def test_build_disk_cache_from_mapping(tmp_path: Path):
    cache_file = tmp_path / "custom.sqlite"
    cache = await build_disk_cache(
        config={
            "path": str(cache_file),
            "size_limit_mb": 1,
            "ttl_s": 1,
        }
    )
    request = GenerateRequest(prompt="hello")
    await cache.set("key", _make_response(request, "v"))
    assert await cache.get("key", request=request) is not None
