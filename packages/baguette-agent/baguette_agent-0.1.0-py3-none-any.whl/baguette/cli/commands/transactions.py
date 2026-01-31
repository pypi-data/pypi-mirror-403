from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from ...memory import (
    LLMVerifierAgent,
    MemoryEntry,
    ValidationPipeline,
    ValidationPolicy,
    ValidationRecord,
)
from ...api import validate_with_pipeline
from ..utils import (
    format_kv_table,
    format_payload_preview,
    format_table,
    parse_json_arg,
    parse_json_or_text,
)


def register(subparsers: argparse._SubParsersAction) -> None:
    tx_parser = subparsers.add_parser("tx", help="Transactional memory commands")
    tx_sub = tx_parser.add_subparsers(dest="tx_command", required=True)

    tx_begin = tx_sub.add_parser("begin", help="Begin a transaction")
    tx_begin.add_argument("--actor", required=True, help="Actor initiating the transaction")
    tx_begin.add_argument("--reason", required=True, help="Reason for the transaction")
    tx_begin.add_argument("--metadata", help="JSON object with metadata")
    tx_begin.add_argument("--lineage", help="JSON object with lineage metadata")
    tx_begin.add_argument("--idempotency-key", help="Idempotency key for transaction begin")
    tx_begin.set_defaults(handler=handle_tx_begin, needs_storage=True)

    tx_stage = tx_sub.add_parser("stage", help="Stage a memory entry")
    tx_stage.add_argument("tx_id", help="Transaction id")
    tx_stage.add_argument("--key", required=True, help="Memory key")
    tx_stage.add_argument("--value", required=True, help="Value (JSON or raw string)")
    tx_stage.add_argument("--type", dest="entry_type", required=True, help="Memory type")
    tx_stage.add_argument("--source", required=True, help="Memory source")
    tx_stage.add_argument("--confidence", type=float, default=0.8)
    tx_stage.add_argument("--metadata", help="JSON object with metadata")
    tx_stage.add_argument("--lineage", help="JSON object with lineage metadata")
    tx_stage.add_argument("--idempotency-key", help="Idempotency key for memory entry")
    tx_stage.set_defaults(handler=handle_tx_stage, needs_storage=True)

    tx_staged = tx_sub.add_parser("staged", help="List staged memory entries")
    tx_staged.add_argument("tx_id", help="Transaction id")
    tx_staged.add_argument("--key", help="Filter by memory key")
    tx_staged.add_argument("--type", dest="entry_type", help="Filter by memory type")
    tx_staged.add_argument("--source", help="Filter by memory source")
    tx_staged.add_argument("--min-confidence", type=float, help="Minimum confidence")
    tx_staged.add_argument("--max-confidence", type=float, help="Maximum confidence")
    tx_staged.add_argument("--limit", type=int, default=100)
    tx_staged.add_argument("--format", choices=["table", "json"], default="table")
    tx_staged.set_defaults(handler=handle_tx_staged, needs_storage=True)

    tx_validate = tx_sub.add_parser("validate", help="Validate a transaction")
    tx_validate.add_argument("tx_id", help="Transaction id")
    tx_validate.add_argument("--status", help="Validation status")
    tx_validate.add_argument("--confidence", type=float, default=0.8)
    tx_validate.add_argument("--evidence", help="Validation evidence")
    tx_validate.add_argument("--validator", help="Validator identifier")
    tx_validate.add_argument("--metadata", help="JSON object with metadata")
    tx_validate.add_argument("--idempotency-key", help="Idempotency key for validation")
    tx_validate.add_argument(
        "--pipeline",
        choices=["default"],
        help="Use the built-in validation pipeline",
    )
    tx_validate.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.8,
        help="Minimum confidence required to approve staged memory",
    )
    tx_validate.add_argument(
        "--no-contradiction-check",
        action="store_true",
        help="Disable contradiction checks against stored memory",
    )
    tx_validate.add_argument(
        "--no-staged-conflict-check",
        action="store_true",
        help="Disable staged conflict checks within the transaction",
    )
    tx_validate.add_argument(
        "--memory-limit",
        type=int,
        default=50,
        help="Limit number of stored entries to check per key",
    )
    tx_validate.add_argument(
        "--verifier",
        choices=["sample"],
        help="Attach a sample verifier agent to the pipeline",
    )
    tx_validate.add_argument(
        "--policy",
        help="Path to a JSON/YAML validation policy",
    )
    tx_validate.add_argument(
        "--policy-json",
        help="Inline JSON validation policy",
    )
    tx_validate.set_defaults(handler=handle_tx_validate, needs_storage=True)

    tx_commit = tx_sub.add_parser("commit", help="Commit a transaction")
    tx_commit.add_argument("tx_id", help="Transaction id")
    tx_commit.add_argument(
        "--supersede",
        action="store_true",
        help="Mark prior entries with the same key/type as superseded",
    )
    tx_commit.set_defaults(handler=handle_tx_commit, needs_storage=True)

    tx_rollback = tx_sub.add_parser("rollback", help="Rollback a transaction")
    tx_rollback.add_argument("tx_id", help="Transaction id")
    tx_rollback.add_argument("--reason", required=True, help="Rollback reason")
    tx_rollback.set_defaults(handler=handle_tx_rollback, needs_storage=True)

    tx_status = tx_sub.add_parser("status", help="Show transaction status")
    tx_status.add_argument("tx_id", help="Transaction id")
    tx_status.add_argument("--format", choices=["table", "json"], default="table")
    tx_status.set_defaults(handler=handle_tx_status, needs_storage=True)

    tx_approve = tx_sub.add_parser("approve", help="Approve a transaction (human)")
    tx_approve.add_argument("tx_id", help="Transaction id")
    tx_approve.add_argument("--validator", required=True, help="Human validator identifier")
    tx_approve.add_argument("--evidence", required=True, help="Approval evidence")
    tx_approve.add_argument("--confidence", type=float, default=0.95)
    tx_approve.add_argument("--metadata", help="JSON object with metadata")
    tx_approve.add_argument("--idempotency-key", help="Idempotency key for approval")
    tx_approve.set_defaults(handler=handle_tx_approve, needs_storage=True)

    tx_reject = tx_sub.add_parser("reject", help="Reject a transaction (human)")
    tx_reject.add_argument("tx_id", help="Transaction id")
    tx_reject.add_argument("--validator", required=True, help="Human validator identifier")
    tx_reject.add_argument("--evidence", required=True, help="Rejection evidence")
    tx_reject.add_argument("--confidence", type=float, default=0.95)
    tx_reject.add_argument("--metadata", help="JSON object with metadata")
    tx_reject.add_argument("--idempotency-key", help="Idempotency key for rejection")
    tx_reject.set_defaults(handler=handle_tx_reject, needs_storage=True)


def handle_tx_begin(storage, args: argparse.Namespace) -> int:
    metadata = parse_json_arg(args.metadata, "--metadata", {})
    lineage = parse_json_arg(args.lineage, "--lineage", {})
    tx_id = storage.begin_transaction(
        actor=args.actor,
        reason=args.reason,
        metadata=metadata,
        idempotency_key=args.idempotency_key,
        lineage=lineage,
    )
    print(tx_id)
    return 0


def handle_tx_stage(storage, args: argparse.Namespace) -> int:
    metadata = parse_json_arg(args.metadata, "--metadata", {})
    lineage = parse_json_arg(args.lineage, "--lineage", {})
    value = parse_json_or_text(args.value)
    entry = MemoryEntry.new(
        key=args.key,
        value=value,
        type=args.entry_type,
        source=args.source,
        confidence=args.confidence,
        metadata=metadata,
        lineage=lineage,
        idempotency_key=args.idempotency_key,
        tx_id=args.tx_id,
    )
    storage.stage_memory(args.tx_id, entry)
    print(entry.entry_id)
    return 0


def handle_tx_staged(storage, args: argparse.Namespace) -> int:
    entries = list(
        storage.list_staged_memory(
            args.tx_id,
            key=args.key,
            entry_type=args.entry_type,
            source=args.source,
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
        print("No staged memory entries found.")
        return 0

    print(format_table(["ENTRY_ID", "KEY", "TYPE", "VALUE", "CONF", "CREATED_AT"], rows))
    return 0


def handle_tx_validate(storage, args: argparse.Namespace) -> int:
    metadata = parse_json_arg(args.metadata, "--metadata", {})
    if args.policy and args.policy_json:
        raise ValueError("Use either --policy or --policy-json, not both.")

    if args.policy or args.policy_json:
        policy_payload = (
            ValidationPolicy.from_file(args.policy)
            if args.policy
            else ValidationPolicy.from_dict(parse_json_arg(args.policy_json, "--policy-json", {}))
        )

        verifier = None
        if args.verifier == "sample":

            def _sample_client(prompt: str) -> Dict[str, Any]:
                return {
                    "status": "approved",
                    "confidence": 0.9,
                    "evidence": "Sample verifier approved the update.",
                    "metadata": {"prompt_chars": len(prompt)},
                }

            verifier = LLMVerifierAgent(_sample_client, validator_id="sample_verifier")

        pipeline = policy_payload.build_pipeline()
        if verifier:
            pipeline.verifier = verifier

        record = validate_with_pipeline(
            storage,
            tx_id=args.tx_id,
            pipeline=pipeline,
            context_metadata=metadata,
            memory_limit=args.memory_limit,
        )
        print(f"Validated {args.tx_id} status={record.status} confidence={record.confidence:.2f}")
        return 0

    if args.pipeline:
        verifier = None
        if args.verifier == "sample":

            def _sample_client(prompt: str) -> Dict[str, Any]:
                return {
                    "status": "approved",
                    "confidence": 0.9,
                    "evidence": "Sample verifier approved the update.",
                    "metadata": {"prompt_chars": len(prompt)},
                }

            verifier = LLMVerifierAgent(_sample_client, validator_id="sample_verifier")

        pipeline = ValidationPipeline.default(
            confidence_threshold=args.confidence_threshold,
            enable_contradiction_check=not args.no_contradiction_check,
            enable_staged_conflict_check=not args.no_staged_conflict_check,
            verifier=verifier,
        )
        record = validate_with_pipeline(
            storage,
            tx_id=args.tx_id,
            pipeline=pipeline,
            context_metadata=metadata,
            memory_limit=args.memory_limit,
        )
        print(f"Validated {args.tx_id} status={record.status} confidence={record.confidence:.2f}")
        return 0

    if not args.status or not args.evidence or not args.validator:
        raise ValueError("--status, --evidence, and --validator are required without --pipeline.")

    validation = ValidationRecord(
        status=args.status,
        confidence=args.confidence,
        evidence=args.evidence,
        validator=args.validator,
        metadata=metadata,
        idempotency_key=args.idempotency_key,
    )
    storage.validate_transaction(args.tx_id, validation)
    print(f"Validated {args.tx_id}")
    return 0


def handle_tx_commit(storage, args: argparse.Namespace) -> int:
    storage.commit_transaction(args.tx_id, supersede=args.supersede)
    print(f"Committed {args.tx_id}")
    return 0


def handle_tx_rollback(storage, args: argparse.Namespace) -> int:
    storage.rollback_transaction(args.tx_id, args.reason)
    print(f"Rolled back {args.tx_id}")
    return 0


def handle_tx_status(storage, args: argparse.Namespace) -> int:
    tx = storage.get_transaction(args.tx_id)
    payload = tx.to_dict()
    if args.format == "json":
        print(json.dumps(payload, indent=2))
        return 0

    order = [
        "tx_id",
        "status",
        "actor",
        "reason",
        "created_at",
        "updated_at",
        "committed_at",
        "rolled_back_at",
        "idempotency_key",
        "metadata",
        "lineage",
        "validation",
    ]
    print(format_kv_table(payload, order))
    return 0


def handle_tx_human_review(storage, args: argparse.Namespace, status: str) -> int:
    metadata = parse_json_arg(args.metadata, "--metadata", {})
    validation = ValidationRecord(
        status=status,
        confidence=args.confidence,
        evidence=args.evidence,
        validator=args.validator,
        metadata=metadata,
        idempotency_key=args.idempotency_key,
    )
    storage.validate_transaction(args.tx_id, validation)
    print(f"Validated {args.tx_id} status={status}")
    return 0


def handle_tx_approve(storage, args: argparse.Namespace) -> int:
    return handle_tx_human_review(storage, args, "approved")


def handle_tx_reject(storage, args: argparse.Namespace) -> int:
    return handle_tx_human_review(storage, args, "rejected")
