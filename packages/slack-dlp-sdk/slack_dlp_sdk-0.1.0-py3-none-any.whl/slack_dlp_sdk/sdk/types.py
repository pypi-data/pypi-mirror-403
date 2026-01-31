"""Type definitions for Slack DLP SDK."""

from __future__ import annotations

from typing import Protocol, Any, Optional, TypeVar
from collections.abc import Callable

import requests

T = TypeVar("T")


class ClientContext(Protocol):
    """Protocol defining the expected attributes and methods
    for a Slack DLP SDK client context."""

    base_url: str
    user_token: str
    timeout: int
    session: requests.Session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        *,
        data: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
    ) -> dict[str, Any]: ...

    def _paginate_request(
        self,
        method: str,
        endpoint: str,
        *,
        data: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
        items_key: str,
        cursor_key: str = "cursor",
        next_cursor_path: tuple[str, str] = (
            "response_metadata",
            "next_cursor",
        ),
        max_pages: Optional[int] = None,
        per_item: Optional[Callable[[dict[str, Any]], Optional[T]]] = None,
        per_page: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> list[dict[str, Any]]: ...
