"""CLI command setup for managing DLP alerts."""

from slack_dlp_sdk.constants import DEFAULT_LIMIT


def setup_alerts_command(subparser) -> None:
    """Sets up the 'alerts' command parser with subcommands."""
    alert = subparser.add_parser("alert", help="Manage DLP alerts")
    alert_cmd = alert.add_subparsers(dest="command", required=True)

    alert_list = alert_cmd.add_parser("list", help="List DLP alerts")
    alert_list.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    alert_list.add_argument(
        "--earliest", type=int, default=None, help="Epoch seconds"
    )
    alert_list.add_argument(
        "--latest", type=int, default=None, help="Epoch seconds"
    )
    alert_list.add_argument(
        "--archived",
        action="store_true",
        help="List archived alerts instead of active",
    )

    alert_get = alert_cmd.add_parser("get", help="Get alert details")
    alert_get.add_argument("--id", required=True, help="Alert ID")

    alert_archive = alert_cmd.add_parser("archive", help="Archive alert(s)")
    alert_archive.add_argument(
        "--id",
        action="append",
        required=True,
        help="Alert ID (repeatable)",
    )

    alert_unarchive = alert_cmd.add_parser(
        "unarchive", help="Unarchive alert(s)"
    )
    alert_unarchive.add_argument(
        "--id",
        action="append",
        required=True,
        help="Alert ID (repeatable)",
    )
