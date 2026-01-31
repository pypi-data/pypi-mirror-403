"""CLI commands for managing DLP rules."""

from slack_dlp_sdk.sdk.models import (
    ChannelShareTargetType,
    ChannelType,
    RuleAction,
)


def setup_rules_command(subparser) -> None:
    """Sets up the 'rules' command parser with subcommands."""
    rule = subparser.add_parser("rule", help="Manage DLP rules")
    rule_cmd = rule.add_subparsers(dest="command", required=True)

    rule_cmd.add_parser("list", help="List DLP rules")

    rule_get = rule_cmd.add_parser("get", help="Get DLP rule details")
    rule_get.add_argument("--id", required=True, help="Rule ID")

    rule_activate = rule_cmd.add_parser(
        "activate", help="Reactivate a DLP rule"
    )
    rule_activate.add_argument("--id", required=True, help="Rule ID")

    rule_deactivate = rule_cmd.add_parser(
        "deactivate", help="Deactivate a DLP rule"
    )
    rule_deactivate.add_argument("--id", required=True, help="Rule ID")

    rule_create = rule_cmd.add_parser("create", help="Create a DLP rule")
    rule_create.add_argument("--name", required=True, help="Rule name")
    rule_create.add_argument(
        "--detector",
        action="append",
        required=True,
        help="System detector (repeatable). "
        "Example: --detector ALL_CREDIT_CARDS",
    )
    rule_create.add_argument(
        "--action",
        required=True,
        choices=[a.value for a in RuleAction],
        help="Rule action",
    )
    rule_create.add_argument(
        "--channel-share-target",
        required=True,
        choices=[c.value for c in ChannelShareTargetType],
        help="Channel share target",
    )
    rule_create.add_argument(
        "--channel-type",
        action="append",
        required=True,
        choices=[c.value for c in ChannelType],
        help="Channel type target (repeatable)",
    )
    rule_create.add_argument(
        "--workspace-target",
        default=None,
        help="Workspace target (e.g. T0123ABCDEF)",
    )
    rule_create.add_argument(
        "--custom-message", default=None, help="Custom message"
    )

    rule_update = rule_cmd.add_parser("update", help="Update a DLP rule")
    rule_update.add_argument("--id", required=True, help="Rule ID")
    rule_update.add_argument("--name", required=True, help="Rule name")
    rule_update.add_argument(
        "--detector",
        action="append",
        required=True,
        help="System detector (repeatable).",
    )
    rule_update.add_argument(
        "--action",
        required=True,
        choices=[a.value for a in RuleAction],
        help="Rule action",
    )
    rule_update.add_argument(
        "--channel-share-target",
        required=False,
        choices=[c.value for c in ChannelShareTargetType],
        default=None,
        help="Channel share target (optional)",
    )
    rule_update.add_argument(
        "--channel-type",
        action="append",
        required=False,
        choices=[c.value for c in ChannelType],
        default=None,
        help="Channel type target (repeatable, optional)",
    )
    rule_update.add_argument(
        "--workspace-target",
        action="append",
        default=None,
        help="Workspace target (repeatable, optional)",
    )
    rule_update.add_argument(
        "--custom-message", default=None, help="Custom message"
    )
