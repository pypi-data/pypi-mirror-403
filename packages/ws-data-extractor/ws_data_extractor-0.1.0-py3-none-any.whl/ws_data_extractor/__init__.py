"""Public Python client for the Web Scraper Data Extractor API."""

from .client import AsyncClient, Client
from .errors import ApiError
from .models import (
    ErrorResponse,
    ExtractAsyncResponse,
    ExtractOptions,
    ExtractRequest,
    ExtractResponse,
    RunStatusResponse,
)
from .utils import dedupe_urls, resolve_follow_urls, resolve_urls

__all__ = [
    "ApiError",
    "AsyncClient",
    "Client",
    "ErrorResponse",
    "ExtractAsyncResponse",
    "ExtractOptions",
    "ExtractRequest",
    "ExtractResponse",
    "RunStatusResponse",
    "dedupe_urls",
    "resolve_follow_urls",
    "resolve_urls",
]

__version__ = "0.1.0"
