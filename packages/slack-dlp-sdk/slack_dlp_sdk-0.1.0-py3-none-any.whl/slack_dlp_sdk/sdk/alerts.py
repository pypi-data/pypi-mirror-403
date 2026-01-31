"""DLP Alert Management Mixin for Slack DLP SDK.

Provides methods to retrieve, archive, and unarchive DLP alerts from Slack.
"""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from slack_dlp_sdk.constants import DEFAULT_LIMIT
from slack_dlp_sdk.sdk.types import ClientContext

if TYPE_CHECKING:
    Self = ClientContext
else:
    Self = object


class AlertsMixin:
    """Mixin providing DLP alert management functionality."""

    def get_dlp_alerts(
        self: ClientContext,
        latest: Optional[int] = None,
        earliest: Optional[int] = None,
        limit: int = DEFAULT_LIMIT,
        archived_alerts: bool = False,
    ) -> list[dict[str, Any]]:
        """Retrieves DLP alert data from Slack by mimicking a browser request
        to the admin.dlp.violations.list endpoint.
        Args:
            latest: Optional epoch to filter alerts created before this time.
            earliest: Optional epoch to filter alerts created after this time.
            limit: Maximum number of alerts to retrieve per call (default: 100).
            archived_alerts: If True, retrieves archived alerts;
                otherwise, retrieves active alerts.

        Returns:
            A list of dictionaries, each representing a DLP alert.

        Raises:
            SlackHTTPError:
                If there is an HTTP error during the request.
            SlackAuthError:
                If authentication fails or the session is invalid.
            SlackDLPError:
                For any other Slack DLP–related error.
        """
        data: dict[str, Any] = {
            "limit": limit,
            "violation_status": "0" if not archived_alerts else "1",
        }

        def _process_alert(alert: dict[str, Any]) -> Optional[dict[str, Any]]:
            """Processes an alert item, applying earliest/latest filtering"""
            date_create = int(alert.get("date_create", 0) or 0)

            if latest is not None and date_create > latest:
                return None
            if earliest is not None and date_create < earliest:
                return None

            alert_id = str(alert.get("id") or "")
            if "-" in alert_id:
                alert["message_ts"] = alert_id.split("-", 1)[0]

            return alert

        return self._paginate_request(
            "POST",
            "admin.dlp.violations.list",
            data=data,
            reason="native-dlp-violations-table-list",
            items_key="violation_alerts",
            per_item=_process_alert,
        )

    def get_dlp_alert_details(
        self: ClientContext, alert_id: str
    ) -> dict[str, Any]:
        """Retrieves detailed information about a specific DLP alert.

        Args:
            alert_id: The ID of the alert to retrieve details for.

        Returns:
            A dictionary containing the alert details.

        Raises:
            SlackHTTPError:
                If there is an HTTP error during the request.
            SlackAuthError:
                If authentication fails or the session is invalid.
            SlackDLPError:
                For any other Slack DLP–related error.
        """
        return self._make_request(
            method="POST",
            endpoint="admin.dlp.violations.info",
            data={
                "violation_alert_id": alert_id,
            },
            reason="fetch-violation-info",
        ).get("violation_alert", {})

    def archive_dlp_alert(
        self: ClientContext, alert_ids: str | list[str]
    ) -> None:
        """Archives a DLP alert by its ID.

        Args:
            alert_ids: The ID of the violation to archive.
                Multiple IDs can be provided as a comma-separated string or list
                Example:
                    - "1768310000.000000-C02xxxx"
                    - "1768310000.000000-C02xxxx, 1768311475.332639-C02xxxx"
                    - ["1768310000.000000-C02xxxx", "1768311475.332639-C02xxxx"]

        Raises:
            SlackHTTPError:
                If there is an HTTP error during the request.
            SlackAuthError:
                If authentication fails or the session is invalid.
            SlackDLPError:
                For any other Slack DLP–related error.
        """
        if isinstance(alert_ids, list):
            alert_ids = ",".join(alert_ids)

        self._make_request(
            method="POST",
            endpoint="admin.dlp.violations.archive",
            data={
                "alert_ids": alert_ids,
            },
            reason="NativeDLPArchiveViolationModal",
        )

    def unarchive_dlp_alert(
        self: ClientContext, alert_ids: str | list[str]
    ) -> None:
        """Unarchives a DLP violation by its ID.

        Args:
            alert_ids: The ID of the violation to unarchive.
                Multiple IDs can be provided as a comma-separated string or list

                Example:
                    - "1768310000.000000-C02xxxx"
                    - "1768310000.000000-C02xxxx, 1768311475.332639-C02xxxx"
                    - ["1768310000.000000-C02xxxx", "1768311475.332639-C02xxxx"]

        Raises:
            SlackHTTPError:
                If there is an HTTP error during the request.
            SlackAuthError:
                If authentication fails or the session is invalid.
            SlackDLPError:
                For any other Slack DLP–related error.
        """
        if isinstance(alert_ids, list):
            alert_ids = ",".join(alert_ids)

        self._make_request(
            method="POST",
            endpoint="admin.dlp.violations.unarchive",
            data={
                "alert_ids": alert_ids,
            },
            reason="NativeDLPUnarchiveViolationModal",
        )
