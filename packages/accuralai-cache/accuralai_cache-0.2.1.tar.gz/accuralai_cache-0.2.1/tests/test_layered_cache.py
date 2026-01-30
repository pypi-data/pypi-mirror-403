import asyncio
from pathlib import Path

import pytest

from accuralai_core.contracts.models import GenerateRequest, GenerateResponse, Usage

from accuralai_cache.layered import LayeredCache, build_layered_cache


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
async def test_layered_cache_promotes_from_disk(tmp_path: Path):
    cache = await build_layered_cache(
        config={
            "memory": {"max_entries": 1},
            "disk": {"path": str(tmp_path / "layered.sqlite")},
            "promote_on_hit": True,
        }
    )
    assert isinstance(cache, LayeredCache)

    request = GenerateRequest(prompt="layered")
    await cache.set("key", _make_response(request, "value"))

    # Drop from memory layer to force disk lookup.
    await cache._memory.invalidate("key")  # type: ignore[attr-defined]
    assert await cache._memory.get("key", request=request) is None  # type: ignore[attr-defined]

    cached = await cache.get("key", request=request)
    assert cached is not None
    assert cached.output_text == "value"

    # Value should be promoted back into memory.
    assert await cache._memory.get("key", request=request) is not None  # type: ignore[attr-defined]


@pytest.mark.anyio("asyncio")
async def test_layered_cache_ttl_applies_to_layers(tmp_path: Path):
    cache = await build_layered_cache(
        config={
            "ttl_s": 0.2,
            "memory": {"max_entries": 4},
            "disk": {"path": str(tmp_path / "ttl.sqlite")},
        }
    )
    request = GenerateRequest(prompt="ttl")
    await cache.set("key", _make_response(request, "ephemeral"))

    assert await cache.get("key", request=request) is not None
    await asyncio.sleep(0.3)
    assert await cache.get("key", request=request) is None
