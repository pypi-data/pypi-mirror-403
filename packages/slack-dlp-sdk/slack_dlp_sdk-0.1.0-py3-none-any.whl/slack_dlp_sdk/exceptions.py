"""Exceptions for slack-dlp-sdk."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class SlackDLPError(Exception):
    """Base exception for slack-dlp-sdk."""


@dataclass
class SlackAPIError(SlackDLPError):
    """Raised when Slack returns ok=false."""

    error: str
    messages: list[str]
    warnings: list[str]
    status_code: Optional[int] = None
    endpoint: Optional[str] = None

    def __str__(self) -> str:
        bits: list[str] = [self.error]
        if self.endpoint:
            bits.append(f"endpoint={self.endpoint}")
        if self.status_code:
            bits.append(f"status={self.status_code}")
        if self.messages:
            bits.append("; ".join(self.messages))
        return " | ".join(bits)


class SlackInvalidArgumentsError(SlackAPIError):
    """Slack rejected the request arguments."""


class SlackAuthError(SlackAPIError):
    """Authentication error."""


@dataclass
class SlackRateLimitedError(SlackDLPError):
    """Raised on HTTP 429."""

    retry_after: Optional[int] = None
    endpoint: Optional[str] = None

    def __str__(self) -> str:
        if self.retry_after is None:
            return "rate_limited"
        return f"rate_limited | retry_after={self.retry_after}s"


@dataclass
class SlackHTTPError(SlackDLPError):
    """Raised when HTTP request fails without a usable Slack JSON payload."""

    status_code: int
    endpoint: Optional[str] = None
    body_snippet: Optional[str] = None

    def __str__(self) -> str:
        bits = [f"http_error status={self.status_code}"]
        if self.endpoint:
            bits.append(f"endpoint={self.endpoint}")
        if self.body_snippet:
            bits.append(self.body_snippet)
        return " | ".join(bits)


class SlackDecodeError(SlackDLPError):
    """Raised when response cannot be decoded as JSON."""
