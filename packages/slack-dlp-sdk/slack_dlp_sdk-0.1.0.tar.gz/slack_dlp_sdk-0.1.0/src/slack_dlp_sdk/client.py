# pylint: disable=line-too-long

"""slack_dlp_sdk.client

High-level client for Slack's Enterprise DLP admin endpoints.

This project interacts with Slack's internal/admin HTTP endpoints (e.g.
`admin.dlp.*`) used by the Slack web UI. These endpoints are not part of the
publicly documented Slack Web API and may change without notice.

Architecture:

`SlackDLPClient` provides shared HTTP/session setup and authentication, then
exposes feature-specific operations via mixins:
    - `SlackHTTPMixin`: request/response helpers, retries, timeouts, and error
      handling.
    - `AlertsMixin`: DLP violation (alert) listing and basic lifecycle operations.
    - `RulesMixin`: DLP rule listing and management operations.

Authentication model:

The client authenticates using the Slack `d` cookie value from an authenticated
browser session for the enterprise domain. On initialisation, it requests the
enterprise homepage and scrapes an `xoxc-...` token ("enterprise_api_token")
used by the Slack UI. That token is then sent as the `token` parameter to the
admin endpoints.

Caveats:
    - Requires appropriate Slack Enterprise Grid admin permissions.
    - Because token retrieval relies on HTML content, Slack UI/auth changes can
      break authentication.
    - Treat the `d` cookie and scraped token as secrets; do not log or commit them.

Basic usage:

    from slack_dlp_sdk.client import SlackDLPClient

    with SlackDLPClient(d_cookie="...", enterprise_domain="example.slack.com") as client:
        alerts = client.get_dlp_alerts()
        rules = client.get_dlp_rules()
"""

from __future__ import annotations

import re

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from slack_dlp_sdk.constants import DEFAULT_TIMEOUT, USER_AGENT
from slack_dlp_sdk.exceptions import SlackDLPError

from slack_dlp_sdk.sdk.http import SlackHTTPMixin
from slack_dlp_sdk.sdk.alerts import AlertsMixin
from slack_dlp_sdk.sdk.rules import RulesMixin


class SlackDLPClient(SlackHTTPMixin, AlertsMixin, RulesMixin):
    """Client for interacting with Slack's DLP API endpoints.

    Args:
        d_cookie: The 'd' cookie value from Slack authentication.
        enterprise_domain: The Slack enterprise domain
            Example: "your-enterprise.slack.com"
        timeout: Optional timeout for HTTP requests
            (default: 30 seconds).
    """

    def __init__(
        self,
        d_cookie: str,
        enterprise_domain: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        if not d_cookie:
            raise SlackDLPError("d_cookie is required (set D_COOKIE).")
        if not enterprise_domain:
            raise SlackDLPError(
                "enterprise_domain is required (set ENTERPRISE_DOMAIN)."
            )

        self.enterprise_domain = enterprise_domain.strip()
        self.base_url = f"https://{self.enterprise_domain}/api/"
        self.timeout = timeout

        self.session = requests.Session()
        self.session.cookies.set("d", d_cookie)
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            }
        )

        self._configure_retries()
        self.user_token = self._get_user_token()

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "SlackDLPClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _configure_retries(self) -> None:
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST"}),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)

    def _get_user_token(self) -> str:
        response = self.session.get(
            f"https://{self.enterprise_domain}",
            timeout=self.timeout,
        )
        response.raise_for_status()

        # Find the user token with enterprise wide scope
        # `"enterprise_api_token": "xoxc-..."` in the response
        match = re.search(
            r'enterprise_api_token"\s*:\s*"(xoxc-[^"]+)"', response.text
        )
        if not match:
            # Fallback: Try to find any `xoxc-` token in the response
            match = re.search(r"(xoxc-[A-Za-z0-9-]+)", response.text)

        if not match:
            raise SlackDLPError(
                "Could not find enterprise_api_token"
                " (xoxc-...) in the response."
            )
        return match.group(1)
