"""Shared HTTP helpers for Slack internal admin endpoints.

Provides methods for making requests and handling pagination.

Assumes the concrete client provides:
- self.session
- self.base_url
- self.user_token
- self.timeout
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING, TypeVar
from collections.abc import Callable

import requests

from slack_dlp_sdk.exceptions import (
    SlackAPIError,
    SlackAuthError,
    SlackHTTPError,
    SlackRateLimitedError,
)
from slack_dlp_sdk.sdk.types import ClientContext

if TYPE_CHECKING:
    Self = ClientContext
else:
    Self = object

T = TypeVar("T")


class SlackHTTPMixin:
    """
    Shared HTTP helpers for Slack internal admin endpoints.

    Assumes the concrete client provides:
      - self.session
      - self.base_url
      - self.user_token
      - self.timeout
    """

    def _make_request(
        self: ClientContext,
        method: str,
        endpoint: str,
        *,
        data: Optional[dict[str, Any]] = None,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Makes an HTTP request to a Slack internal endpoint.

        Args:
            method: HTTP method (e.g., "POST").
            endpoint: Slack endpoint path appended to base_url.
            data: Form fields to include in the request.
            reason: _x_reason value.

        Returns:
            The parsed JSON response as a dictionary.

        Raises:
            SlackAPIError: If the API response indicates an error.
            SlackAuthError: If authentication fails.
            SlackHTTPError: For other HTTP errors.
        """
        url = f"{self.base_url}{endpoint}"

        # Set auth token if not already provided in data
        if data is None:
            data = {}

        if "token" not in data:
            data["token"] = self.user_token

        if reason is not None:
            data.setdefault("_x_reason", reason)
        data.setdefault("_x_mode", "online")
        data.setdefault("_x_app_name", "manage")

        # Remove any None values to avoid sending them as 'null' strings
        compact_form: dict[str, str] = {
            k: str(v) for k, v in data.items() if v is not None
        }

        try:
            response = self.session.request(
                method,
                url,
                data=compact_form,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise SlackHTTPError(
                status_code=e.response.status_code,
                endpoint=endpoint,
                body_snippet=str(e)[:500],
            ) from e

        if response.status_code == 429:
            raise SlackRateLimitedError(
                retry_after=int(response.headers.get("Retry-After", "0")),
                endpoint=endpoint,
            )
        elif response.status_code == 401:
            raise SlackAuthError(
                error="invalid_auth",
                messages=["Authentication failed"],
                warnings=[],
                status_code=response.status_code,
                endpoint=endpoint,
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise SlackHTTPError(
                status_code=response.status_code,
                endpoint=endpoint,
                body_snippet=response.text[:500],
            ) from e

        payload = response.json()
        if not payload.get("ok", False):
            raise SlackAPIError(
                error=payload.get("error", "unknown_error"),
                messages=payload.get("messages", []),
                warnings=payload.get("warnings", []),
                status_code=response.status_code,
                endpoint=endpoint,
            )

        return payload

    # pylint: disable=line-too-long
    def _paginate_request(
        self: ClientContext,
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
    ) -> list[T] | list[dict[str, Any]]:
        """
        Generic cursor-based paginator for Slack internal endpoints.

        Args:
            method: HTTP method (usually "POST").
            endpoint: Slack endpoint path appended to base_url.
            data: Base form fields (token and _x_* are injected by _make_request).
            reason: _x_reason value.
            items_key: Key in the payload containing the list of items for the page.
            cursor_key: Form field name used to send the cursor (usually "cursor").
            next_cursor_path: Where to find next cursor in payload.
            max_pages: Optional hard limit (safety valve).
            per_item: Optional hook called with each item dict; return transformed item or None to skip.
            per_page: Optional hook called with each raw payload (e.g. metrics/logging).

        Returns:
            A list of items (raw dicts) or transformed items if per_item is provided.
        Raises:
            SlackAPIError: If any API request fails.
            SlackHTTPError: For HTTP errors.
            SlackAuthError: If authentication fails.
        """
        if data is None:
            data = {}

        results: list[Any] = []
        cursor: str | None = None
        pages = 0

        while True:
            if cursor:
                data[cursor_key] = cursor
            else:
                data.pop(cursor_key, None)

            payload = self._make_request(
                method, endpoint, data=data, reason=reason
            )

            if per_page is not None:
                per_page(payload)

            page_items = payload.get(items_key) or []
            if not isinstance(page_items, list):
                raise SlackAPIError(
                    error="invalid_response",
                    messages=[f"Expected '{items_key}' to be a list"],
                    warnings=[],
                    status_code=None,
                    endpoint=endpoint,
                )

            if per_item is None:
                results.extend(page_items)
            else:
                for item in page_items:
                    if not isinstance(item, dict):
                        continue
                    mapped = per_item(item)
                    if mapped is not None:
                        results.append(mapped)

            md = payload
            for key in next_cursor_path:
                if not isinstance(md, dict):
                    md = {}
                    break
                md = md.get(key)
            cursor = md or None

            if not cursor:
                break

            pages += 1
            if max_pages is not None and pages >= max_pages:
                break

        return results
