from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ...api import (
    memory_query,
    memory_redact,
    memory_redact_with_policy,
    memory_resolve,
    memory_scan_pii,
    memory_snapshot,
)
from ...memory import (
    MemoryConflictError,
    RedactionPolicy,
    configure_memory_type_registry,
    get_memory_type_registry,
    register_memory_types,
)
from ..utils import (
    format_payload_preview,
    format_table,
    parse_iso_timestamp,
    parse_json_arg,
)


def register(subparsers: argparse._SubParsersAction) -> None:
    memory_parser = subparsers.add_parser("memory", help="Memory governance commands")
    memory_sub = memory_parser.add_subparsers(dest="memory_command", required=True)

    memory_query_parser = memory_sub.add_parser("query", help="Query committed memory")
    memory_query_parser.add_argument("--key", help="Filter by memory key")
    memory_query_parser.add_argument("--type", dest="entry_type", help="Filter by memory type")
    memory_query_parser.add_argument("--source", help="Filter by memory source")
    memory_query_parser.add_argument("--created-after", help="ISO-8601 timestamp lower bound")
    memory_query_parser.add_argument("--created-before", help="ISO-8601 timestamp upper bound")
    memory_query_parser.add_argument("--min-confidence", type=float, help="Minimum confidence")
    memory_query_parser.add_argument("--max-confidence", type=float, help="Maximum confidence")
    memory_query_parser.add_argument("--limit", type=int, default=100)
    memory_query_parser.add_argument("--format", choices=["table", "json"], default="table")
    memory_query_parser.set_defaults(handler=handle_memory_query, needs_storage=True)

    memory_resolve_parser = memory_sub.add_parser("resolve", help="Resolve memory conflicts")
    memory_resolve_parser.add_argument("--key", help="Filter by memory key")
    memory_resolve_parser.add_argument("--type", dest="entry_type", help="Filter by memory type")
    memory_resolve_parser.add_argument("--source", help="Filter by memory source")
    memory_resolve_parser.add_argument("--created-after", help="ISO-8601 timestamp lower bound")
    memory_resolve_parser.add_argument("--created-before", help="ISO-8601 timestamp upper bound")
    memory_resolve_parser.add_argument("--min-confidence", type=float, help="Minimum confidence")
    memory_resolve_parser.add_argument("--max-confidence", type=float, help="Maximum confidence")
    memory_resolve_parser.add_argument("--limit", type=int, default=100)
    memory_resolve_parser.add_argument(
        "--strategy",
        choices=["latest", "highest_confidence", "reject"],
        default="latest",
    )
    memory_resolve_parser.add_argument("--format", choices=["table", "json"], default="table")
    memory_resolve_parser.set_defaults(handler=handle_memory_resolve, needs_storage=True)

    memory_scan = memory_sub.add_parser("scan-pii", help="Scan committed memory for PII")
    memory_scan.add_argument("--key", help="Filter by memory key")
    memory_scan.add_argument("--type", dest="entry_type", help="Filter by memory type")
    memory_scan.add_argument("--source", help="Filter by memory source")
    memory_scan.add_argument("--created-after", help="ISO-8601 timestamp lower bound")
    memory_scan.add_argument("--created-before", help="ISO-8601 timestamp upper bound")
    memory_scan.add_argument("--min-confidence", type=float, help="Minimum confidence")
    memory_scan.add_argument("--max-confidence", type=float, help="Maximum confidence")
    memory_scan.add_argument("--limit", type=int, default=100)
    memory_scan.add_argument("--patterns", help="JSON array of regex patterns")
    memory_scan.add_argument("--allowlist-keys", help="JSON array of allowed keys")
    memory_scan.add_argument("--allowlist-types", help="JSON array of allowed types")
    memory_scan.add_argument("--max-matches", type=int, default=50)
    memory_scan.add_argument("--format", choices=["table", "json"], default="table")
    memory_scan.set_defaults(handler=handle_memory_scan_pii, needs_storage=True)

    memory_redact_parser = memory_sub.add_parser("redact", help="Redact committed memory entries")
    memory_redact_parser.add_argument("--entry-id", help="Memory entry id to redact")
    memory_redact_parser.add_argument("--pii", action="store_true", help="Redact all entries matching PII scan")
    memory_redact_parser.add_argument("--policy", help="Path to a JSON/YAML redaction policy")
    memory_redact_parser.add_argument("--policy-json", help="Inline JSON redaction policy")
    memory_redact_parser.add_argument("--key", help="Filter by memory key (PII mode)")
    memory_redact_parser.add_argument("--type", dest="entry_type", help="Filter by memory type (PII mode)")
    memory_redact_parser.add_argument("--source", help="Filter by memory source (PII mode)")
    memory_redact_parser.add_argument("--created-after", help="ISO-8601 timestamp lower bound (PII mode)")
    memory_redact_parser.add_argument("--created-before", help="ISO-8601 timestamp upper bound (PII mode)")
    memory_redact_parser.add_argument("--min-confidence", type=float, help="Minimum confidence (PII mode)")
    memory_redact_parser.add_argument("--max-confidence", type=float, help="Maximum confidence (PII mode)")
    memory_redact_parser.add_argument("--limit", type=int, default=100)
    memory_redact_parser.add_argument("--patterns", help="JSON array of regex patterns (PII mode)")
    memory_redact_parser.add_argument("--allowlist-keys", help="JSON array of allowed keys (PII mode)")
    memory_redact_parser.add_argument("--allowlist-types", help="JSON array of allowed types (PII mode)")
    memory_redact_parser.add_argument("--max-matches", type=int, default=50)
    memory_redact_parser.add_argument("--reason", required=True, help="Redaction reason")
    memory_redact_parser.add_argument("--actor", help="Redaction actor")
    memory_redact_parser.add_argument("--replacement", default="[REDACTED]", help="Redacted value")
    memory_redact_parser.add_argument("--dry-run", action="store_true", help="Preview policy redaction changes")
    memory_redact_parser.add_argument("--format", choices=["text", "json"], default="text")
    memory_redact_parser.set_defaults(handler=handle_memory_redact, needs_storage=True)

    memory_export = memory_sub.add_parser("export", help="Export memory snapshot")
    memory_export.add_argument("--key", help="Filter by memory key")
    memory_export.add_argument("--type", dest="entry_type", help="Filter by memory type")
    memory_export.add_argument("--source", help="Filter by memory source")
    memory_export.add_argument("--created-after", help="ISO-8601 timestamp lower bound")
    memory_export.add_argument("--created-before", help="ISO-8601 timestamp upper bound")
    memory_export.add_argument("--min-confidence", type=float, help="Minimum confidence")
    memory_export.add_argument("--max-confidence", type=float, help="Maximum confidence")
    memory_export.add_argument("--limit", type=int, default=1000)
    memory_export.add_argument("--output", help="Write snapshot JSON to file")
    memory_export.set_defaults(handler=handle_memory_export, needs_storage=True)

    memory_types = memory_sub.add_parser("types", help="Configure memory type registry")
    memory_types.add_argument(
        "--mode",
        choices=["off", "warn", "strict"],
        help="Validation mode for memory types",
    )
    memory_types.add_argument("--set-types", help="JSON array of allowed types")
    memory_types.add_argument("--add-types", help="JSON array of types to add")
    memory_types.add_argument("--prefixes", help="JSON array of allowed custom prefixes")
    memory_types.add_argument("--format", choices=["table", "json"], default="table")
    memory_types.set_defaults(handler=handle_memory_types, needs_storage=True)


def handle_memory_query(storage, args: argparse.Namespace) -> int:
    entries = list(
        memory_query(
            storage,
            key=args.key,
            entry_type=args.entry_type,
            source=args.source,
            created_after=parse_iso_timestamp(args.created_after, "--created-after"),
            created_before=parse_iso_timestamp(args.created_before, "--created-before"),
            min_confidence=args.min_confidence,
            max_confidence=args.max_confidence,
            limit=args.limit,
        )
    )
    if args.format == "json":
        payload = [entry.to_dict() for entry in entries]
        print(json.dumps(payload, indent=2))
        return 0

    rows = [
        [
            entry.entry_id,
            entry.key,
            entry.type,
            format_payload_preview(entry.value),
            f"{entry.confidence:.2f}",
            entry.created_at,
        ]
        for entry in entries
    ]
    if not rows:
        print("No memory entries found.")
        return 0

    print(format_table(["ENTRY_ID", "KEY", "TYPE", "VALUE", "CONF", "CREATED_AT"], rows))
    return 0


def handle_memory_resolve(storage, args: argparse.Namespace) -> int:
    try:
        result = memory_resolve(
            storage,
            key=args.key,
            entry_type=args.entry_type,
            source=args.source,
            created_after=parse_iso_timestamp(args.created_after, "--created-after"),
            created_before=parse_iso_timestamp(args.created_before, "--created-before"),
            min_confidence=args.min_confidence,
            max_confidence=args.max_confidence,
            limit=args.limit,
            strategy=args.strategy,
        )
    except MemoryConflictError as exc:
        print(f"Conflict resolution failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        payload = {
            "strategy": result.strategy,
            "resolved": [entry.to_dict() for entry in result.resolved],
            "conflicts": [
                {
                    "key": conflict.key,
                    "entry_type": conflict.entry_type,
                    "values": conflict.values,
                    "entries": [entry.to_dict() for entry in conflict.entries],
                }
                for conflict in result.conflicts
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    rows = [
        [
            entry.entry_id,
            entry.key,
            entry.type,
            format_payload_preview(entry.value),
            f"{entry.confidence:.2f}",
            entry.created_at,
        ]
        for entry in result.resolved
    ]
    if not rows:
        print("No resolved memory entries found.")
        return 0
    print(format_table(["ENTRY_ID", "KEY", "TYPE", "VALUE", "CONF", "CREATED_AT"], rows))
    if result.conflicts:
        print(f"Conflicts detected: {len(result.conflicts)}", file=sys.stderr)
    return 0


def handle_memory_scan_pii(storage, args: argparse.Namespace) -> int:
    matches = memory_scan_pii(
        storage,
        key=args.key,
        entry_type=args.entry_type,
        source=args.source,
        created_after=parse_iso_timestamp(args.created_after, "--created-after"),
        created_before=parse_iso_timestamp(args.created_before, "--created-before"),
        min_confidence=args.min_confidence,
        max_confidence=args.max_confidence,
        limit=args.limit,
        patterns=parse_json_arg(args.patterns, "--patterns", None),
        allowlist_keys=parse_json_arg(args.allowlist_keys, "--allowlist-keys", None),
        allowlist_types=parse_json_arg(args.allowlist_types, "--allowlist-types", None),
        max_matches=args.max_matches,
    )
    if args.format == "json":
        print(json.dumps(matches, indent=2))
        return 0

    rows = [
        [
            match.get("entry_id", ""),
            match.get("key", ""),
            match.get("type", ""),
            match.get("path", ""),
            match.get("pattern", ""),
            match.get("value_hash", ""),
        ]
        for match in matches
    ]
    if not rows:
        print("No PII matches found.")
        return 0
    print(format_table(["ENTRY_ID", "KEY", "TYPE", "PATH", "PATTERN", "VALUE_HASH"], rows))
    return 0


def handle_memory_redact(storage, args: argparse.Namespace) -> int:
    if args.policy and args.policy_json:
        raise ValueError("Use either --policy or --policy-json, not both.")
    if args.policy or args.policy_json:
        policy_payload = (
            RedactionPolicy.from_file(args.policy)
            if args.policy
            else RedactionPolicy.from_dict(parse_json_arg(args.policy_json, "--policy-json", {}))
        )
        report = memory_redact_with_policy(
            storage,
            policy=policy_payload,
            key=args.key,
            entry_type=args.entry_type,
            source=args.source,
            created_after=parse_iso_timestamp(args.created_after, "--created-after"),
            created_before=parse_iso_timestamp(args.created_before, "--created-before"),
            min_confidence=args.min_confidence,
            max_confidence=args.max_confidence,
            limit=args.limit,
            reason=args.reason,
            actor=args.actor,
            dry_run=args.dry_run,
        )
        if args.format == "json" or args.dry_run:
            print(json.dumps(report.to_dict(), indent=2))
            return 0
        print(f"Redacted {len(report.changes)} entries.")
        return 0

    if args.pii:
        matches = memory_scan_pii(
            storage,
            key=args.key,
            entry_type=args.entry_type,
            source=args.source,
            created_after=parse_iso_timestamp(args.created_after, "--created-after"),
            created_before=parse_iso_timestamp(args.created_before, "--created-before"),
            min_confidence=args.min_confidence,
            max_confidence=args.max_confidence,
            limit=args.limit,
            patterns=parse_json_arg(args.patterns, "--patterns", None),
            allowlist_keys=parse_json_arg(args.allowlist_keys, "--allowlist-keys", None),
            allowlist_types=parse_json_arg(args.allowlist_types, "--allowlist-types", None),
            max_matches=args.max_matches,
        )
        entry_ids = sorted({match.get("entry_id", "") for match in matches if match.get("entry_id")})
        if not entry_ids:
            print("No PII matches found.")
            return 0
        for entry_id in entry_ids:
            memory_redact(
                storage,
                entry_id=entry_id,
                reason=args.reason,
                actor=args.actor,
                rule="pii_scan",
                redacted_value=args.replacement,
            )
        print(f"Redacted {len(entry_ids)} entries.")
        return 0

    if not args.entry_id:
        raise ValueError("--entry-id is required unless --pii is used.")
    entry = memory_redact(
        storage,
        entry_id=args.entry_id,
        reason=args.reason,
        actor=args.actor,
        redacted_value=args.replacement,
    )
    if args.format == "json":
        print(json.dumps(entry.to_dict(), indent=2))
    else:
        print(entry.entry_id)
    return 0


def handle_memory_export(storage, args: argparse.Namespace) -> int:
    snapshot = memory_snapshot(
        storage,
        key=args.key,
        entry_type=args.entry_type,
        source=args.source,
        created_after=parse_iso_timestamp(args.created_after, "--created-after"),
        created_before=parse_iso_timestamp(args.created_before, "--created-before"),
        min_confidence=args.min_confidence,
        max_confidence=args.max_confidence,
        limit=args.limit,
    )
    payload = json.dumps(snapshot, indent=2)
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
        print(f"Wrote snapshot to {args.output}")
    else:
        print(payload)
    return 0


def handle_memory_types(storage, args: argparse.Namespace) -> int:
    registry = get_memory_type_registry()
    if args.mode or args.set_types or args.prefixes:
        types = parse_json_arg(args.set_types, "--set-types", None) if args.set_types else None
        prefixes = parse_json_arg(args.prefixes, "--prefixes", None) if args.prefixes else None
        registry = configure_memory_type_registry(
            mode=args.mode,
            types=types,
            custom_prefixes=prefixes,
        )

    if args.add_types:
        add_types = parse_json_arg(args.add_types, "--add-types", None) or []
        if not isinstance(add_types, list):
            raise ValueError("--add-types must be a JSON array.")
        registry = register_memory_types(*add_types)

    payload = registry.to_dict()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return 0

    rows = [
        ["mode", payload["mode"]],
        ["custom_prefixes", json.dumps(payload["custom_prefixes"], ensure_ascii=False)],
        ["types", json.dumps(payload["types"], ensure_ascii=False)],
    ]
    print(format_table(["FIELD", "VALUE"], rows))
    return 0
