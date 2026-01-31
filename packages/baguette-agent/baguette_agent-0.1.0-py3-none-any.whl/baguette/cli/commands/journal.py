from __future__ import annotations

import argparse
import json

from ..utils import format_payload_preview, format_table


def register(subparsers: argparse._SubParsersAction) -> None:
    journal_parser = subparsers.add_parser("journal", help="Audit journal commands")
    journal_sub = journal_parser.add_subparsers(dest="journal_command", required=True)

    journal_query = journal_sub.add_parser("query", help="Query journal events")
    journal_query.add_argument("--limit", type=int, default=100)
    journal_query.add_argument("--tx-id", help="Filter by transaction id")
    journal_query.add_argument("--event-type", help="Filter by event type")
    journal_query.add_argument("--entity-type", help="Filter by entity type")
    journal_query.add_argument("--entity-id", help="Filter by entity id")
    journal_query.add_argument("--format", choices=["table", "json"], default="table")
    journal_query.add_argument("--show-payload", action="store_true", help="Include payload column in table output")
    journal_query.set_defaults(handler=handle_journal_query, needs_storage=True)


def handle_journal_query(storage, args: argparse.Namespace) -> int:
    events = list(
        storage.list_journal(
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
