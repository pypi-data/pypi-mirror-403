from __future__ import annotations

from typing import Any, Dict, List, Optional


class ApiError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        error: str,
        message: str,
        step: str,
        retryable: bool,
        request_id: Optional[str] = None,
        run_id: Optional[str] = None,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message
        self.step = step
        self.retryable = retryable
        self.request_id = request_id
        self.run_id = run_id
        self.validation_errors = validation_errors
        self.payload = payload or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        base = f"{self.error}: {self.message}" if self.message else self.error
        if self.status_code:
            base = f"HTTP {self.status_code} - {base}"
        return base

    def to_error_response(self):
        from .models import ErrorResponse

        return ErrorResponse(
            error=self.error,
            message=self.message,
            step=self.step,
            retryable=self.retryable,
            request_id=self.request_id,
            run_id=self.run_id,
            validation_errors=self.validation_errors,
            raw=self.payload,
        )
