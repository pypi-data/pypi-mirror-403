from __future__ import annotations

import argparse
import json

from ...audit import DecisionTrace
from ..utils import format_table, parse_iso_timestamp, parse_json_arg


def register(subparsers: argparse._SubParsersAction) -> None:
    trace_parser = subparsers.add_parser("trace", help="Decision trace commands")
    trace_sub = trace_parser.add_subparsers(dest="trace_command", required=True)

    trace_log = trace_sub.add_parser("log", help="Record a decision trace")
    trace_log.add_argument("--decision", required=True, help="Decision label")
    trace_log.add_argument("--skill-ref", help="Skill reference name@version")
    trace_log.add_argument("--reason", required=True, help="Decision rationale")
    trace_log.add_argument("--confidence", type=float, default=0.8)
    trace_log.add_argument("--result", required=True, help="Result label")
    trace_log.add_argument("--metadata", help="JSON object with metadata")
    trace_log.add_argument("--lineage", help="JSON object with lineage metadata")
    trace_log.add_argument("--tx-id", help="Associated transaction id")
    trace_log.add_argument("--idempotency-key", help="Idempotency key for trace")
    trace_log.set_defaults(handler=handle_trace_log, needs_storage=True)

    trace_query = trace_sub.add_parser("query", help="Query decision traces")
    trace_query.add_argument("--limit", type=int, default=100)
    trace_query.add_argument("--tx-id", help="Filter by transaction id")
    trace_query.add_argument("--decision", help="Filter by decision")
    trace_query.add_argument("--skill-ref", help="Filter by skill reference name@version")
    trace_query.add_argument("--result", help="Filter by result")
    trace_query.add_argument("--created-after", help="ISO-8601 timestamp lower bound")
    trace_query.add_argument("--created-before", help="ISO-8601 timestamp upper bound")
    trace_query.add_argument("--correlation-id", help="Filter by correlation id")
    trace_query.add_argument("--format", choices=["table", "json"], default="table")
    trace_query.set_defaults(handler=handle_trace_query, needs_storage=True)


def handle_trace_log(storage, args: argparse.Namespace) -> int:
    metadata = parse_json_arg(args.metadata, "--metadata", {})
    lineage = parse_json_arg(args.lineage, "--lineage", {})
    trace = DecisionTrace.new(
        decision=args.decision,
        skill_ref=args.skill_ref,
        reason=args.reason,
        confidence=args.confidence,
        result=args.result,
        metadata=metadata,
        tx_id=args.tx_id,
        lineage=lineage,
        idempotency_key=args.idempotency_key,
    )
    storage.record_trace(trace)
    print(trace.trace_id)
    return 0


def handle_trace_query(storage, args: argparse.Namespace) -> int:
    traces = list(
        storage.list_traces(
            limit=args.limit,
            tx_id=args.tx_id,
            decision=args.decision,
            skill_ref=args.skill_ref,
            result=args.result,
            created_after=parse_iso_timestamp(args.created_after, "--created-after"),
            created_before=parse_iso_timestamp(args.created_before, "--created-before"),
            correlation_id=args.correlation_id,
        )
    )
    if args.format == "json":
        payload = [trace.to_dict() for trace in traces]
        print(json.dumps(payload, indent=2))
        return 0

    rows = [
        [
            trace.trace_id,
            trace.decision,
            trace.result,
            trace.skill_ref or "",
            trace.tx_id or "",
            trace.timestamp,
        ]
        for trace in traces
    ]
    if not rows:
        print("No traces found.")
        return 0

    print(format_table(["TRACE_ID", "DECISION", "RESULT", "SKILL", "TX_ID", "TIMESTAMP"], rows))
    return 0
