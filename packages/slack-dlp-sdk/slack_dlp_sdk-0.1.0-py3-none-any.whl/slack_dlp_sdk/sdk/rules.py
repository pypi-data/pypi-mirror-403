"""DLP rule management Mixin for Slack DLP SDK.

Provides methods to create, retrieve, update, deactivate,
and reactivate DLP rules.
"""

from __future__ import annotations

import json
from typing import Any, Optional, TYPE_CHECKING

from slack_dlp_sdk.constants import DEFAULT_LIMIT
from slack_dlp_sdk.sdk.types import ClientContext
from slack_dlp_sdk.sdk.models import (
    SystemDetector,
    RuleAction,
    ChannelShareTargetType,
    ChannelType,
)

if TYPE_CHECKING:
    Self = ClientContext
else:
    Self = object


# pylint: disable=line-too-long
class RulesMixin:
    """Mixin providing DLP rule management functionality."""

    @staticmethod
    def _normalise_detectors(
        detectors: list[dict[str, str]] | list[SystemDetector],
    ) -> list[dict[str, str]]:
        """Convert detector inputs into Slack's expected shape."""
        normalised: list[dict[str, str]] = []

        for d in detectors:
            if isinstance(d, SystemDetector):
                normalised.append({"type": d.value})
            else:
                # already a dict
                normalised.append(d)

        return normalised

    def get_dlp_rules(
        self: ClientContext,
        limit: int = DEFAULT_LIMIT,
        latest: Optional[int] = None,
        earliest: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Retrieves the DLP rules configured in the Slack workspace.

        Returns:
            A list of dictionaries, each representing a DLP rule.

        Raises:
            SlackAPIError: If the API request fails.
        """
        return self._paginate_request(
            method="POST",
            endpoint="admin.dlp.rules.list",
            reason="native-dlp-rules-table-list-refetch",
            items_key="rules",
            data={
                "limit": limit,
                "latest": latest,
                "earliest": earliest,
            },
        )

    def deactivate_dlp_rule(self: ClientContext, rule_id: str) -> None:
        """Deactivates a DLP rule by its ID.

        Args:
            rule_id: The ID of the rule to deactivate.

        Raises:
            SlackAPIError: If the API request fails.
        """
        self._make_request(
            method="POST",
            endpoint="admin.dlp.rules.deactivate",
            data={
                "rule_id": rule_id,
            },
            reason="NativeDLPDeactivateRuleModal",
        )

    def reactivate_dlp_rule(self: ClientContext, rule_id: str) -> None:
        """Reactivates a DLP rule by its ID.

        Args:
            rule_id: The ID of the rule to reactivate.

        Raises:
            SlackAPIError: If the API request fails.
        """
        self._make_request(
            method="POST",
            endpoint="admin.dlp.rules.reactivate",
            data={
                "rule_id": rule_id,
            },
            reason="NativeDLPReactivateRuleModal",
        )

    def get_dlp_rule_details(
        self: ClientContext, rule_id: str
    ) -> dict[str, Any]:
        """Retrieves detailed information about a specific DLP rule.

        Args:
            rule_id: The ID of the rule to retrieve details for.

        Returns:
            A dictionary containing the rule details.

        Raises:
            SlackAPIError: If the API request fails.
        """
        return self._make_request(
            method="POST",
            endpoint="admin.dlp.rules.info",
            data={
                "rule_id": rule_id,
            },
            reason="NativeDLPRuleDetails",
        ).get("rule", {})

    def update_dlp_rule(
        self: ClientContext,
        rule_id: str,
        name: str,
        detectors: list[SystemDetector | dict[str, str]],
        action: RuleAction,
        channel_share_target: Optional[ChannelShareTargetType] = None,
        channel_type: Optional[list[ChannelType]] = None,
        custom_message: Optional[str] = None,
        workspace_targets: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Update an existing Slack DLP rule.

        Wraps the Slack `admin.dlp.rules.edit` endpoint and mirrors the
        behaviour of editing a rule via the Slack Admin UI.

        Args:
            rule_id:
                The unique ID of the DLP rule to update.
            name:
                Updated human-readable name for the rule.
            detectors:
                One or more detectors to apply to the rule.

                Use a predefined detector via the `SystemDetector` enum, or
                provide a custom detector definition as a dictionary.

                Examples:
                    - [SystemDetector.ALL_CREDIT_CARDS]
                    - [SystemDetector.NATIONAL_ID_US_SSN]
                    - [{"type": "REGEX", "pattern": r"\\b\\d{3}-\\d{2}-\\d{4}\\b"}]
            action:
                New action to take when a violation is detected.

                Must be a `RuleAction` enum value, for example:
                    - RuleAction.ALERT_ONLY
                    - RuleAction.USER_WARNING
                    - RuleAction.TOMBSTONE
            channel_share_target:
                Optional new sharing scope for the rule.

                Must be a `ChannelShareTargetType` enum value, for example:
                    - ChannelShareTargetType.ALL
                    - ChannelShareTargetType.INTERNAL_ONLY
                    - ChannelShareTargetType.EXTERNAL_ONLY

                If omitted, the existing value is left unchanged.
            channel_type:
                Optional list of channel types the rule should apply to.

                Must contain one or more `ChannelType` enum values, for example:
                    - [ChannelType.PUBLIC]
                    - [ChannelType.PUBLIC, ChannelType.PRIVATE]

                If omitted, the existing value is left unchanged.
            custom_message:
                Optional custom message shown to users when a violation occurs.

                If omitted, the existing value is left unchanged.
            workspace_targets:
                Optional list of Slack workspace IDs to scope the rule to.

                If omitted, the existing value is left unchanged.

        Returns:
            A dictionary containing the updated rule as returned by Slack.

        Raises:
            SlackInvalidArgumentsError:
                If the provided arguments are invalid or rejected by Slack.
            SlackAuthError:
                If authentication fails or the session is invalid.
            SlackDLPError:
                For any other Slack DLP–related error.
        """
        data: dict[str, Any] = {
            "rule_id": rule_id,
            "name": name,
            "action": action.value,
            "detectors": json.dumps(self._normalise_detectors(detectors)),
            "channel_share_target": (
                channel_share_target.value if channel_share_target else None
            ),
            "channel_type_targets": channel_type if channel_type else None,
            "custom_message": custom_message if custom_message else None,
            "workspace_targets": (
                workspace_targets if workspace_targets else None
            ),
        }
        if channel_type:
            if isinstance(channel_type, list):
                data["channel_type_targets"] = ",".join(
                    ct.value for ct in channel_type
                )
            else:
                data["channel_type_targets"] = channel_type
        else:
            data["channel_type_targets"] = None

        if workspace_targets:
            if isinstance(workspace_targets, list):
                data["workspace_targets"] = ",".join(
                    wt for wt in workspace_targets
                )
            else:
                data["workspace_targets"] = workspace_targets
        else:
            data["workspace_targets"] = None

        return self._make_request(
            method="POST",
            endpoint="admin.dlp.rules.edit",
            data=data,
            reason="editNativeDlpRule",
        ).get("rule", {})

    def create_dlp_rule(
        self: ClientContext,
        name: str,
        detectors: list[SystemDetector | dict[str, str]],
        action: RuleAction,
        channel_share_target: ChannelShareTargetType,
        channel_type: list[ChannelType],
        custom_message: Optional[str] = None,
        workspace_share_target: Optional[str | list[str]] = None,
    ) -> dict[str, Any]:
        """Create a new Slack DLP rule.

        Wraps the Slack `admin.dlp.rules.create` endpoint and mirrors
        the behaviour of the Slack Admin UI.

        Args:
            name:
                Human-readable name for the rule.
            detectors:
                One or more detectors to apply to the rule.

                Use a predefined detector via the `SystemDetector` enum, or
                provide a custom detector definition as a dictionary.

                Examples:
                    - [SystemDetector.ALL_CREDIT_CARDS]
                    - [SystemDetector.NATIONAL_ID_US_SSN]
                    - [{"type": "REGEX", "pattern": r"\\b\\d{3}-\\d{2}-\\d{4}\\b"}]
            action:
                Action to take when a violation is detected.

                Must be a `RuleAction` enum value, for example:
                    - RuleAction.ALERT_ONLY
                    - RuleAction.USER_WARNING
                    - RuleAction.TOMBSTONE
            channel_share_target:
                Controls where the rule applies based on sharing context.

                Must be a `ChannelShareTargetType` enum value, for example:
                    - ChannelShareTargetType.ALL
                    - ChannelShareTargetType.INTERNAL_ONLY
                    - ChannelShareTargetType.EXTERNAL_ONLY
            channel_type:
                List of channel types the rule should apply to.

                Must contain one or more `ChannelType` enum values, for example:
                    - [ChannelType.PUBLIC]
                    - [ChannelType.PUBLIC, ChannelType.PRIVATE]
            custom_message:
                Optional custom message shown to users when a violation occurs.
            workspace_share_target:
                Optional Slack workspace ID(s) to scope the rule to a workspace(s).
                Can be a single ID or a list of IDs.

        Returns:
            A dictionary containing the newly created rule as returned by Slack.

        Raises:
            SlackInvalidArgumentsError:
                If the provided arguments are invalid or rejected by Slack.
            SlackAuthError:
                If authentication fails or the session is invalid.
            SlackDLPError:
                For any other Slack DLP–related error.
        """
        if isinstance(workspace_share_target, list):
            workspace_share_target = ",".join(workspace_share_target)

        data: dict[str, Any] = {
            "name": name,
            "action": action.value,
            "detectors": json.dumps(self._normalise_detectors(detectors)),
            "channel_share_target": channel_share_target.value,
            "channel_type_targets": ",".join(ct.value for ct in channel_type),
            "custom_message": custom_message if custom_message else None,
            "workspace_targets": (
                workspace_share_target if workspace_share_target else None
            ),
        }

        return self._make_request(
            method="POST",
            endpoint="admin.dlp.rules.create",
            data=data,
            reason="createNativeDlpRule",
        ).get("rule", {})
