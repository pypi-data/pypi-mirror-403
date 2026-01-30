from __future__ import annotations

from typing import Any, Iterable, List
from urllib.parse import urljoin


def dedupe_urls(urls: Iterable[str]) -> List[str]:
    seen = set()
    output: List[str] = []
    for url in urls:
        if url in seen:
            continue
        output.append(url)
        seen.add(url)
    return output


def _extract_urls(value: Any, base_url: str) -> List[str]:
    urls: List[str] = []
    if isinstance(value, str):
        urls.append(value)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                urls.append(item)
    resolved = [urljoin(base_url, raw) for raw in urls]
    return resolved


def resolve_follow_urls(base_url: str, data: Any) -> List[str]:
    if not base_url or not isinstance(data, dict):
        return []
    urls: List[str] = []
    follow_urls = data.get("_follow_urls")
    next_page = data.get("_next_page_url")
    if follow_urls is not None:
        urls.extend(_extract_urls(follow_urls, base_url))
    if next_page is not None:
        urls.extend(_extract_urls(next_page, base_url))
    return dedupe_urls(urls)


def resolve_urls(base_url: str, data: Any, field: str) -> List[str]:
    if not base_url:
        return []
    urls: List[str] = []
    if isinstance(data, dict):
        if field in data:
            urls.extend(_extract_urls(data[field], base_url))
        else:
            for value in data.values():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and field in item:
                            urls.extend(_extract_urls(item[field], base_url))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and field in item:
                urls.extend(_extract_urls(item[field], base_url))
    return dedupe_urls(urls)
