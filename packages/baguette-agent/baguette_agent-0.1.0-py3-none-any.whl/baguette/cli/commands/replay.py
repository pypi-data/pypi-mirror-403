from __future__ import annotations

import argparse
import json

from ...api import journal_replay
from ..utils import format_payload_preview, format_table


def register(subparsers: argparse._SubParsersAction) -> None:
    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay audit journal events (oldest to newest)",
    )
    replay_parser.add_argument("--limit", type=int, default=100)
    replay_parser.add_argument("--tx-id", help="Filter by transaction id")
    replay_parser.add_argument("--event-type", help="Filter by event type")
    replay_parser.add_argument("--entity-type", help="Filter by entity type")
    replay_parser.add_argument("--entity-id", help="Filter by entity id")
    replay_parser.add_argument("--format", choices=["table", "json"], default="table")
    replay_parser.add_argument(
        "--show-payload",
        action="store_true",
        help="Include payload column in table output",
    )
    replay_parser.set_defaults(handler=handle_replay, needs_storage=True)


def handle_replay(storage, args: argparse.Namespace) -> int:
    events = list(
        journal_replay(
            storage,
            limit=args.limit,
            tx_id=args.tx_id,
            event_type=args.event_type,
            entity_type=args.entity_type,
            entity_id=args.entity_id,
        )
    )
    if args.format == "json":
        payload = [event.to_dict() for event in events]
        print(json.dumps(payload, indent=2))
        return 0

    rows = []
    for event in events:
        row = [
            str(event.seq or ""),
            event.event_type,
            event.entity_type,
            event.entity_id,
            event.tx_id or "",
            event.timestamp,
        ]
        if args.show_payload:
            row.append(format_payload_preview(event.payload))
        rows.append(row)
    if not rows:
        print("No journal events found.")
        return 0

    headers = ["SEQ", "EVENT", "ENTITY", "ENTITY_ID", "TX_ID", "TIMESTAMP"]
    if args.show_payload:
        headers.append("PAYLOAD")
    print(format_table(headers, rows))
    return 0
