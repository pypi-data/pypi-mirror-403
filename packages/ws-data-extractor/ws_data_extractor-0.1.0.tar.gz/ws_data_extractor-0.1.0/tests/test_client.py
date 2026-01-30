import sys
import time
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ws_data_extractor import AsyncClient, Client


class TrackingStream(httpx.SyncByteStream):
    def __init__(self, data: bytes):
        self._data = data
        self.closed = False

    def __iter__(self):
        yield self._data

    def close(self) -> None:
        self.closed = True


def _make_sync_client(handler):
    client = Client(api_key="test", base_url="https://example.com", retries=1)
    client._client.close()
    client._client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://example.com",
        timeout=1.0,
    )
    return client


async def _make_async_client(handler):
    client = AsyncClient(api_key="test", base_url="https://example.com", retries=1)
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.com",
        timeout=1.0,
    )
    return client


def test_sync_extract_allows_list_json():
    def handler(request):
        return httpx.Response(200, request=request, json=[{"item": 1}])

    client = _make_sync_client(handler)
    try:
        result = client.extract(url="https://example.com/page", prompt="Extract")
        assert result.data == [{"item": 1}]
        assert result.raw == [{"item": 1}]
        assert result.schema_id is None
    finally:
        client.close()


def test_sync_retry_closes_response(monkeypatch):
    calls = {"count": 0}
    stream_holder = {}

    def handler(request):
        if calls["count"] == 0:
            calls["count"] += 1
            stream = TrackingStream(b'{"error": "rate_limited"}')
            stream_holder["first"] = stream
            return httpx.Response(
                429,
                request=request,
                headers={"Retry-After": "0"},
                stream=stream,
            )
        return httpx.Response(200, request=request, json={"data": {"ok": True}})

    monkeypatch.setattr(time, "sleep", lambda *_: None)

    client = _make_sync_client(handler)
    try:
        result = client.extract(url="https://example.com/page", prompt="Extract")
        assert result.data == {"ok": True}
        assert stream_holder["first"].closed is True
    finally:
        client.close()


@pytest.mark.asyncio
async def test_async_extract_uses_common_fields():
    async def handler(request):
        if request.url.path == "/v1.0/extract-async":
            return httpx.Response(200, request=request, json={"run_id": "run-1"})
        if request.url.path == "/v1.0/runs/run-1":
            return httpx.Response(
                200,
                request=request,
                json={
                    "run_id": "run-1",
                    "status": "success",
                    "step": "done",
                    "data": {"name": "ok"},
                    "schema_id": "schema-1",
                    "schema_hash": "hash-1",
                    "schema_version": 3,
                    "validation_errors": None,
                },
            )
        return httpx.Response(404, request=request, json={"error": "not_found"})

    client = await _make_async_client(handler)
    try:
        result = await client.extract(url="https://example.com/page", prompt="Extract")
        assert result.data == {"name": "ok"}
        assert result.schema_id == "schema-1"
        assert result.schema_hash == "hash-1"
        assert result.schema_version == 3
        assert result.raw.get("status") == "success"
    finally:
        await client.close()
