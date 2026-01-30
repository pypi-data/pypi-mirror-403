import anyio
import pytest

try:
    from accuralai_cache.memory import MemoryCache
except ImportError:  # pragma: no cover - optional dependency
    MemoryCache = None  # type: ignore[assignment]

from accuralai_core import CoreOrchestrator, GenerateRequest


@pytest.mark.anyio("asyncio")
async def test_generate_with_default_mock_backend():
    orchestrator = CoreOrchestrator()
    try:
        request = GenerateRequest(prompt="  hello   world  ", tags=["Example"])
        response = await orchestrator.generate(request)
    finally:
        await orchestrator.aclose()

    assert response.request_id == request.id
    assert "hello world" in response.output_text
    assert response.finish_reason == "stop"


@pytest.mark.anyio("asyncio")
async def test_cache_hit_latency_uses_retrieval_time(monkeypatch):
    if MemoryCache is None:
        pytest.skip("MemoryCache not available")

    orchestrator = CoreOrchestrator()

    original_get = MemoryCache.get

    async def slow_get(self, key: str, *, request: GenerateRequest):
        await anyio.sleep(0.01)
        return await original_get(self, key, request=request)

    monkeypatch.setattr(MemoryCache, "get", slow_get)

    try:
        request = GenerateRequest(prompt="cache this please")
        first = await orchestrator.generate(request)

        second = await orchestrator.generate(request)
    finally:
        await orchestrator.aclose()

    assert second.finish_reason == "stop"
    assert second.latency_ms >= 10  # slow path from cache retrieval
    assert second.latency_ms != first.latency_ms
