from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class ExtractOptions:
    wait_ms: Optional[int] = None
    wait_until: Optional[str] = None
    wait_for_selector: Optional[str] = None
    screenshot: Optional[bool] = None
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[str] = None
    timeout_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if self.wait_ms is not None:
            payload["wait_ms"] = self.wait_ms
        if self.wait_until is not None:
            payload["wait_until"] = self.wait_until
        if self.wait_for_selector is not None:
            payload["wait_for_selector"] = self.wait_for_selector
        if self.screenshot is not None:
            payload["screenshot"] = self.screenshot
        if self.headers is not None:
            payload["headers"] = self.headers
        if self.cookies is not None:
            payload["cookies"] = self.cookies
        if self.timeout_ms is not None:
            payload["timeout_ms"] = self.timeout_ms
        return payload


OptionsType = Union[ExtractOptions, Dict[str, Any]]


def _coerce_options(options: OptionsType) -> Dict[str, Any]:
    if isinstance(options, ExtractOptions):
        return options.to_dict()
    if isinstance(options, dict):
        return options
    raise TypeError("options must be a dict or ExtractOptions")


@dataclass
class ExtractRequest:
    url: str
    prompt: str
    schema: Optional[Dict[str, Any]] = None
    schema_id: Optional[str] = None
    options: Optional[OptionsType] = None
    enforce_schema: Optional[bool] = None
    language: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        if self.schema is not None and self.schema_id is not None:
            raise ValueError("Provide only one of schema_id or schema")
        payload: Dict[str, Any] = {
            "url": self.url,
            "prompt": self.prompt,
        }
        if self.schema is not None:
            payload["schema"] = self.schema
        if self.schema_id is not None:
            payload["schema_id"] = self.schema_id
        if self.options is not None:
            payload["options"] = _coerce_options(self.options)
        if self.enforce_schema is not None:
            payload["enforce_schema"] = self.enforce_schema
        if self.language is not None:
            payload["language"] = self.language
        return payload


@dataclass
class ExtractResponse:
    schema_id: Optional[str]
    data: Any
    schema_hash: Optional[str]
    schema_version: Optional[int]
    validation_errors: Optional[List[Dict[str, Any]]]
    raw: Any = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Any) -> "ExtractResponse":
        if not isinstance(payload, dict):
            return cls(
                schema_id=None,
                data=payload,
                schema_hash=None,
                schema_version=None,
                validation_errors=None,
                raw=payload,
            )
        return cls(
            schema_id=payload.get("schema_id"),
            data=payload.get("data"),
            schema_hash=payload.get("schema_hash"),
            schema_version=payload.get("schema_version"),
            validation_errors=payload.get("validation_errors"),
            raw=payload,
        )


@dataclass
class ExtractAsyncResponse:
    run_id: str
    status_url: Optional[str]
    websocket: Optional[str]
    websocket_token: Optional[str]
    websocket_token_expires_at: Optional[int]
    raw: Any = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ExtractAsyncResponse":
        return cls(
            run_id=payload.get("run_id"),
            status_url=payload.get("status_url"),
            websocket=payload.get("websocket"),
            websocket_token=payload.get("websocket_token"),
            websocket_token_expires_at=payload.get("websocket_token_expires_at"),
            raw=payload,
        )


@dataclass
class RunStatusResponse:
    run_id: str
    status: Optional[str]
    step: Optional[str]
    data: Any
    error: Any
    retryable: Optional[bool]
    started_at: Optional[str]
    finished_at: Optional[str]
    validation_errors: Optional[List[Dict[str, Any]]]
    schema_id: Optional[str]
    schema_hash: Optional[str]
    schema_version: Optional[int]
    raw: Any = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RunStatusResponse":
        return cls(
            run_id=payload.get("run_id"),
            status=payload.get("status"),
            step=payload.get("step"),
            data=payload.get("data"),
            error=payload.get("error"),
            retryable=payload.get("retryable"),
            started_at=payload.get("started_at"),
            finished_at=payload.get("finished_at"),
            validation_errors=payload.get("validation_errors"),
            schema_id=payload.get("schema_id"),
            schema_hash=payload.get("schema_hash"),
            schema_version=payload.get("schema_version"),
            raw=payload,
        )


@dataclass
class ErrorResponse:
    error: str
    message: str
    step: str
    retryable: bool
    request_id: Optional[str]
    run_id: Optional[str]
    validation_errors: Optional[List[Dict[str, Any]]]
    raw: Any = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any], request_id: Optional[str] = None) -> "ErrorResponse":
        return cls(
            error=payload.get("error", "error"),
            message=payload.get("message", ""),
            step=payload.get("step", "unknown"),
            retryable=bool(payload.get("retryable", False)),
            request_id=request_id,
            run_id=payload.get("run_id"),
            validation_errors=payload.get("validation_errors"),
            raw=payload,
        )
