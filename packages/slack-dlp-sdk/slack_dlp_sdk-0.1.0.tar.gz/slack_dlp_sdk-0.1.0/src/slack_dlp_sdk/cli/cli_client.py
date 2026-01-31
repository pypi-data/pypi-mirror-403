"""Slack DLP SDK CLI client implementation."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Optional

from slack_dlp_sdk.client import SlackDLPClient
from slack_dlp_sdk.sdk.models import (
    ChannelShareTargetType,
    ChannelType,
    RuleAction,
    SystemDetector,
)
from slack_dlp_sdk.cli.commands.rules import setup_rules_command
from slack_dlp_sdk.cli.commands.alerts import setup_alerts_command


def _add_global_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--slack-cookie",
        type=str,
        default=os.getenv("D_COOKIE", ""),
        help="Slack 'd' cookie value (prefer env var D_COOKIE).",
    )
    parser.add_argument(
        "--enterprise-domain",
        type=str,
        default=os.getenv("ENTERPRISE_DOMAIN", ""),
        help="Slack enterprise domain (prefer env var ENTERPRISE_DOMAIN).",
    )


def _require_auth(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> None:
    if not args.slack_cookie:
        parser.error(
            "Missing Slack cookie. Provide "
            "--slack-cookie or set D_COOKIE environment variable."
        )
    if not args.enterprise_domain:
        parser.error(
            "Missing enterprise domain. Provide "
            "--enterprise-domain or set ENTERPRISE_DOMAIN environment variable."
        )


def _json_print(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _parse_detectors(detector_values: list[str]) -> list[SystemDetector]:
    detectors: list[SystemDetector] = []
    for raw in detector_values:
        # Accept either enum NAME or value string
        raw_norm = raw.strip()
        try:
            detectors.append(SystemDetector[raw_norm])
            continue
        except KeyError:
            pass
        try:
            detectors.append(SystemDetector(raw_norm))
        except ValueError as e:
            valid = ", ".join([d.name for d in SystemDetector])
            raise argparse.ArgumentTypeError(
                f"Unknown detector '{raw_norm}'. Valid values: {valid}"
            ) from e
    return detectors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slack-dlp", description="Slack DLP SDK CLI"
    )
    _add_global_args(parser)

    top_level_parser = parser.add_subparsers(dest="resource", required=True)
    setup_rules_command(top_level_parser)
    setup_alerts_command(top_level_parser)

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    _require_auth(args, parser)

    with SlackDLPClient(
        d_cookie=args.slack_cookie,
        enterprise_domain=args.enterprise_domain,
    ) as client:
        if args.resource == "rule":
            if args.command == "list":
                _json_print(client.get_dlp_rules())
                return
            if args.command == "get":
                _json_print(client.get_dlp_rule_details(args.id))
                return
            if args.command == "activate":
                client.reactivate_dlp_rule(args.id)
                _json_print(
                    {"ok": True, "rule_id": args.id, "action": "activated"}
                )
                return
            if args.command == "deactivate":
                client.deactivate_dlp_rule(args.id)
                _json_print(
                    {"ok": True, "rule_id": args.id, "action": "deactivated"}
                )
                return
            if args.command == "create":
                detectors = _parse_detectors(args.detector)
                rule = client.create_dlp_rule(
                    name=args.name,
                    detectors=detectors,
                    action=RuleAction(args.action),
                    channel_share_target=ChannelShareTargetType(
                        args.channel_share_target
                    ),
                    channel_type=[ChannelType(v) for v in args.channel_type],
                    custom_message=args.custom_message,
                    workspace_share_target=args.workspace_target,
                )
                _json_print(rule)
                return
            if args.command == "update":
                detectors = _parse_detectors(args.detector)
                rule = client.update_dlp_rule(
                    rule_id=args.id,
                    name=args.name,
                    detectors=detectors,
                    action=RuleAction(args.action),
                    channel_share_target=(
                        ChannelShareTargetType(args.channel_share_target)
                        if args.channel_share_target
                        else None
                    ),
                    channel_type=(
                        [ChannelType(v) for v in args.channel_type]
                        if args.channel_type
                        else None
                    ),
                    custom_message=args.custom_message,
                    workspace_targets=args.workspace_target,
                )
                _json_print(rule)
                return

        if args.resource == "alert":
            if args.command == "list":
                alerts = client.get_dlp_alerts(
                    limit=args.limit,
                    earliest=args.earliest,
                    latest=args.latest,
                    archived_alerts=args.archived,
                )
                _json_print(alerts)
                return
            if args.command == "get":
                _json_print(client.get_dlp_alert_details(args.id))
                return
            if args.command == "archive":
                client.archive_dlp_alert(alert_ids=",".join(args.id))
                _json_print({"ok": True, "archived": args.id})
                return
            if args.command == "unarchive":
                client.unarchive_dlp_alert(alert_ids=",".join(args.id))
                _json_print({"ok": True, "unarchived": args.id})
                return

    parser.error("Unsupported command")
