from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Optional
import httpx

from .errors import ApiError
from .models import (
    ExtractAsyncResponse,
    ExtractRequest,
    ExtractResponse,
    RunStatusResponse,
    OptionsType,
)
from .utils import resolve_follow_urls as _resolve_follow_urls
from .utils import resolve_urls as _resolve_urls

DEFAULT_BASE_URL = "https://api.data-extractor.com"
DEFAULT_TIMEOUT_MS = 30000
DEFAULT_RETRIES = 2
RETRY_STATUS = {429, 502, 503}
INITIAL_BACKOFF_SECONDS = 0.5
BACKOFF_MULTIPLIER = 2.0

logger = logging.getLogger("ws_data_extractor")


def _env_int(name: str) -> Optional[int]:
    value = os.getenv(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    now = time.time()
    return max(0.0, dt.timestamp() - now)


def _coerce_payload(
    url: str,
    prompt: str,
    schema: Optional[Dict[str, Any]],
    schema_id: Optional[str],
    options: Optional[OptionsType],
    enforce_schema: Optional[bool],
    language: Optional[str],
) -> Dict[str, Any]:
    request = ExtractRequest(
        url=url,
        prompt=prompt,
        schema=schema,
        schema_id=schema_id,
        options=options,
        enforce_schema=enforce_schema,
        language=language,
    )
    return request.to_dict()


def _read_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


def _ensure_error_payload(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    return {
        "error": "http_error",
        "message": str(payload),
        "step": "parse",
        "retryable": False,
        "raw": payload,
    }


def _invalid_response_payload(payload: Any) -> Dict[str, Any]:
    return {
        "error": "invalid_response",
        "message": "Response was not a JSON object",
        "step": "parse",
        "retryable": False,
        "raw": payload,
    }


def _make_api_error(
    response: Optional[httpx.Response],
    *,
    status_code: int,
    request_id: Optional[str],
    payload: Optional[Dict[str, Any]] = None,
    message_override: Optional[str] = None,
    step_override: Optional[str] = None,
    retryable_override: Optional[bool] = None,
) -> ApiError:
    body = payload or {}
    error = body.get("error") or "http_error"
    message = message_override or body.get("message") or ""
    step = step_override or body.get("step") or "unknown"
    retryable = bool(body.get("retryable", False))
    if retryable_override is not None:
        retryable = retryable_override
    if response is not None and status_code in RETRY_STATUS:
        retryable = True
    return ApiError(
        status_code=status_code,
        error=error,
        message=message,
        step=step,
        retryable=retryable,
        request_id=request_id,
        run_id=body.get("run_id"),
        validation_errors=body.get("validation_errors"),
        payload=body,
    )


class Client:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        retries: int = DEFAULT_RETRIES,
        user_agent: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        idempotency: bool = True,
    ) -> None:
        resolved_key = api_key or os.getenv("WS_API_KEY")
        if not resolved_key:
            raise ValueError("API key is required. Set api_key or WS_API_KEY.")

        resolved_base = (base_url or os.getenv("WS_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        resolved_timeout = timeout_ms if timeout_ms is not None else _env_int("WS_TIMEOUT_MS")
        if resolved_timeout is None:
            resolved_timeout = DEFAULT_TIMEOUT_MS

        self.api_key = resolved_key
        self.base_url = resolved_base
        self.timeout_ms = resolved_timeout
        self.retries = max(0, retries)
        self.user_agent = user_agent
        self.headers = headers or {}
        self.idempotency = idempotency

        timeout_seconds = self.timeout_ms / 1000.0
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def resolve_urls(self, base_url: str, data: Any, field: str) -> list[str]:
        return _resolve_urls(base_url, data, field)

    def resolve_follow_urls(self, base_url: str, data: Any) -> list[str]:
        return _resolve_follow_urls(base_url, data)

    def extract(
        self,
        *,
        url: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        schema_id: Optional[str] = None,
        options: Optional[OptionsType] = None,
        enforce_schema: Optional[bool] = None,
        language: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> ExtractResponse:
        payload = _coerce_payload(url, prompt, schema, schema_id, options, enforce_schema, language)
        body = self._request_json(
            method="POST",
            path="/v1.0/extract",
            json_body=payload,
            idempotency_key=idempotency_key,
        )
        return ExtractResponse.from_dict(body)

    def get_schema(self, schema_id: str) -> Dict[str, Any]:
        body = self._request_json(method="GET", path=f"/v1.0/schemas/{schema_id}")
        if not isinstance(body, dict):
            raise _make_api_error(
                None,
                status_code=0,
                request_id=None,
                payload=_invalid_response_payload(body),
            )
        return body

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        attempt = 0
        backoff = INITIAL_BACKOFF_SECONDS
        auto_key = idempotency_key
        if method.upper() not in {"GET", "HEAD"} and self.idempotency and not auto_key:
            auto_key = str(uuid.uuid4())

        while True:
            headers = self._build_headers(auto_key)
            start = time.time()
            try:
                sleep_for: Optional[float] = None
                response = self._client.request(method, path, json=json_body, headers=headers)
                try:
                    duration_ms = int((time.time() - start) * 1000)
                    request_id = response.headers.get("x-request-id")
                    logger.debug(
                        "request completed",
                        extra={"request_id": request_id, "duration_ms": duration_ms, "endpoint": path},
                    )
                    payload = _read_json(response)

                    if response.status_code in RETRY_STATUS and attempt < self.retries:
                        retry_after = _parse_retry_after(response.headers.get("Retry-After"))
                        sleep_for = retry_after if retry_after is not None else backoff
                    elif response.status_code >= 400:
                        error_payload = _ensure_error_payload(payload)
                        raise _make_api_error(
                            response,
                            status_code=response.status_code,
                            request_id=request_id,
                            payload=error_payload,
                        )
                    else:
                        return payload
                finally:
                    response.close()
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                if attempt < self.retries:
                    time.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                    attempt += 1
                    continue
                raise _make_api_error(
                    None,
                    status_code=0,
                    request_id=None,
                    payload={"error": "transport_error", "message": str(exc)},
                    message_override=str(exc),
                    step_override="transport",
                    retryable_override=True,
                )

            if sleep_for is not None:
                time.sleep(sleep_for)
                backoff *= BACKOFF_MULTIPLIER
                attempt += 1
                continue

    def _build_headers(self, idempotency_key: Optional[str]) -> Dict[str, str]:
        headers: Dict[str, str] = {"Authorization": f"Bearer {self.api_key}"}
        if self.user_agent:
            headers["User-Agent"] = self.user_agent
        if self.headers:
            headers.update(self.headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers


class AsyncClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        retries: int = DEFAULT_RETRIES,
        user_agent: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        idempotency: bool = True,
    ) -> None:
        resolved_key = api_key or os.getenv("WS_API_KEY")
        if not resolved_key:
            raise ValueError("API key is required. Set api_key or WS_API_KEY.")

        resolved_base = (base_url or os.getenv("WS_API_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        resolved_timeout = timeout_ms if timeout_ms is not None else _env_int("WS_TIMEOUT_MS")
        if resolved_timeout is None:
            resolved_timeout = DEFAULT_TIMEOUT_MS

        self.api_key = resolved_key
        self.base_url = resolved_base
        self.timeout_ms = resolved_timeout
        self.retries = max(0, retries)
        self.user_agent = user_agent
        self.headers = headers or {}
        self.idempotency = idempotency

        timeout_seconds = self.timeout_ms / 1000.0
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    def resolve_urls(self, base_url: str, data: Any, field: str) -> list[str]:
        return _resolve_urls(base_url, data, field)

    def resolve_follow_urls(self, base_url: str, data: Any) -> list[str]:
        return _resolve_follow_urls(base_url, data)

    async def extract(
        self,
        *,
        url: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        schema_id: Optional[str] = None,
        options: Optional[OptionsType] = None,
        enforce_schema: Optional[bool] = None,
        language: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        poll_interval_ms: int = 1000,
    ) -> ExtractResponse:
        async_response = await self.extract_async(
            url=url,
            prompt=prompt,
            schema=schema,
            schema_id=schema_id,
            options=options,
            enforce_schema=enforce_schema,
            language=language,
            idempotency_key=idempotency_key,
        )
        run = await self.wait_run(
            async_response.run_id,
            timeout_ms=timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )
        if run.status != "success":
            payload = run.error if isinstance(run.error, dict) else None
            raise _make_api_error(
                None,
                status_code=0,
                request_id=None,
                payload=payload
                or {
                    "error": "run_failed",
                    "message": f"Run finished with status={run.status}",
                    "step": run.step or "unknown",
                    "retryable": run.retryable or False,
                    "run_id": run.run_id,
                    "validation_errors": run.validation_errors,
                },
            )
        if isinstance(run.raw, dict):
            return ExtractResponse.from_dict(run.raw)
        return ExtractResponse.from_dict({"data": run.data, "raw": run.raw})

    async def extract_async(
        self,
        *,
        url: str,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        schema_id: Optional[str] = None,
        options: Optional[OptionsType] = None,
        enforce_schema: Optional[bool] = None,
        language: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> ExtractAsyncResponse:
        payload = _coerce_payload(url, prompt, schema, schema_id, options, enforce_schema, language)
        body = await self._request_json(
            method="POST",
            path="/v1.0/extract-async",
            json_body=payload,
            idempotency_key=idempotency_key,
        )
        if not isinstance(body, dict):
            raise _make_api_error(
                None,
                status_code=0,
                request_id=None,
                payload=_invalid_response_payload(body),
            )
        return ExtractAsyncResponse.from_dict(body)

    async def get_run(self, run_id: str) -> RunStatusResponse:
        body = await self._request_json(method="GET", path=f"/v1.0/runs/{run_id}")
        if not isinstance(body, dict):
            raise _make_api_error(
                None,
                status_code=0,
                request_id=None,
                payload=_invalid_response_payload(body),
            )
        return RunStatusResponse.from_dict(body)

    async def wait_run(
        self,
        run_id: str,
        *,
        timeout_ms: Optional[int] = None,
        poll_interval_ms: int = 1000,
    ) -> RunStatusResponse:
        start = time.time()
        timeout_seconds = (timeout_ms / 1000.0) if timeout_ms is not None else None
        while True:
            status = await self.get_run(run_id)
            if status.status in {"success", "failed"}:
                return status
            if timeout_seconds is not None and (time.time() - start) > timeout_seconds:
                raise TimeoutError(f"Timed out waiting for run {run_id}")
            await asyncio.sleep(max(poll_interval_ms, 50) / 1000.0)

    async def get_schema(self, schema_id: str) -> Dict[str, Any]:
        body = await self._request_json(method="GET", path=f"/v1.0/schemas/{schema_id}")
        if not isinstance(body, dict):
            raise _make_api_error(
                None,
                status_code=0,
                request_id=None,
                payload=_invalid_response_payload(body),
            )
        return body

    async def _request_json(
        self,
        *,
        method: str,
        path: str,
        json_body: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        attempt = 0
        backoff = INITIAL_BACKOFF_SECONDS
        auto_key = idempotency_key
        if method.upper() not in {"GET", "HEAD"} and self.idempotency and not auto_key:
            auto_key = str(uuid.uuid4())

        while True:
            headers = self._build_headers(auto_key)
            start = time.time()
            try:
                sleep_for: Optional[float] = None
                response = await self._client.request(method, path, json=json_body, headers=headers)
                try:
                    duration_ms = int((time.time() - start) * 1000)
                    request_id = response.headers.get("x-request-id")
                    logger.debug(
                        "request completed",
                        extra={"request_id": request_id, "duration_ms": duration_ms, "endpoint": path},
                    )
                    payload = _read_json(response)

                    if response.status_code in RETRY_STATUS and attempt < self.retries:
                        retry_after = _parse_retry_after(response.headers.get("Retry-After"))
                        sleep_for = retry_after if retry_after is not None else backoff
                    elif response.status_code >= 400:
                        error_payload = _ensure_error_payload(payload)
                        raise _make_api_error(
                            response,
                            status_code=response.status_code,
                            request_id=request_id,
                            payload=error_payload,
                        )
                    else:
                        return payload
                finally:
                    await response.aclose()
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                if attempt < self.retries:
                    await asyncio.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                    attempt += 1
                    continue
                raise _make_api_error(
                    None,
                    status_code=0,
                    request_id=None,
                    payload={"error": "transport_error", "message": str(exc)},
                    message_override=str(exc),
                    step_override="transport",
                    retryable_override=True,
                )

            if sleep_for is not None:
                await asyncio.sleep(sleep_for)
                backoff *= BACKOFF_MULTIPLIER
                attempt += 1
                continue

    def _build_headers(self, idempotency_key: Optional[str]) -> Dict[str, str]:
        headers: Dict[str, str] = {"Authorization": f"Bearer {self.api_key}"}
        if self.user_agent:
            headers["User-Agent"] = self.user_agent
        if self.headers:
            headers.update(self.headers)
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers
