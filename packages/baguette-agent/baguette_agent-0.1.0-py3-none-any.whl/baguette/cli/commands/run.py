from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from ...audit import DecisionTrace
from ...skills import validate_skill_inputs
from ...skills.runtime import SkillRunConfig, run_skill
from ...skills.trace import SkillTraceConfig, build_skill_trace_metadata
from ...errors import ExecutionError
from ..utils import parse_skill_ref


def register(subparsers: argparse._SubParsersAction) -> None:
    run_parser = subparsers.add_parser("run", help="Run a skill")
    run_parser.add_argument("skill_ref", help="Skill reference name@version")
    run_parser.add_argument("--inputs", help="JSON string with inputs")
    run_parser.add_argument("--reason", help="Reason for the decision trace")
    run_parser.add_argument("--confidence", type=float, default=0.8)
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--max-attempts", type=int, default=1)
    run_parser.add_argument("--retry-on", help="Comma-separated statuses (e.g. timeout,failure)")
    run_parser.add_argument("--backoff-ms", help="Comma-separated backoff delays in ms")
    run_parser.add_argument("--total-timeout-s", type=float)
    run_parser.add_argument("--step-timeout-s", type=float)
    run_parser.add_argument("--idempotency-key", help="Idempotency key for retries")
    run_parser.add_argument("--trace-inputs-preview", action="store_true")
    run_parser.add_argument("--trace-output-preview", action="store_true")
    run_parser.add_argument("--trace-preview-max-chars", type=int, default=200)
    run_parser.set_defaults(handler=handle_run, needs_storage=True)


def handle_run(storage, args: argparse.Namespace) -> int:
    name, version = parse_skill_ref(args.skill_ref)
    skill = storage.get_skill(name, version)

    inputs: Dict[str, Any] = {}
    if args.inputs:
        try:
            inputs = json.loads(args.inputs)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON for --inputs: {exc}") from exc
    validate_skill_inputs(skill.spec, inputs)

    result = "success"
    metadata: Dict[str, Any] = {"dry_run": args.dry_run}
    error: Exception | None = None

    try:
        retry_on = []
        if args.retry_on:
            retry_on = [item.strip() for item in args.retry_on.split(",") if item.strip()]
        backoff_ms = []
        if args.backoff_ms:
            backoff_ms = [int(item.strip()) for item in args.backoff_ms.split(",") if item.strip()]
        run_config = SkillRunConfig(
            max_attempts=args.max_attempts,
            retry_on=retry_on or ["timeout"],
            backoff_ms=backoff_ms,
            total_timeout_s=args.total_timeout_s,
            step_timeout_s=args.step_timeout_s,
            idempotency_key=args.idempotency_key,
        )
        skill_run = run_skill(skill, inputs, args.dry_run, run_config)
        run_result = skill_run.run
        result = run_result.status
        trace_config = SkillTraceConfig(
            include_inputs_preview=bool(args.trace_inputs_preview),
            include_output_preview=bool(args.trace_output_preview),
            preview_max_chars=args.trace_preview_max_chars,
        )
        metadata = build_skill_trace_metadata(
            tool_name=skill.name,
            skill_ref=skill.ref(),
            inputs=inputs,
            run_result=run_result,
            duration_ms=skill_run.duration_ms,
            attempt=skill_run.attempt,
            max_attempts=skill_run.max_attempts,
            config=trace_config,
            idempotency_key=skill_run.idempotency_key,
        )
        metadata["dry_run"] = args.dry_run
        if run_result.output:
            print(run_result.output)
        if run_result.error:
            metadata["error"] = run_result.error
            error = ExecutionError(run_result.error)
    except Exception as exc:
        result = "failure"
        metadata["error"] = str(exc)
        error = exc

    trace = DecisionTrace.new(
        decision="execute_skill",
        skill_ref=skill.ref(),
        reason=args.reason or "",
        confidence=args.confidence,
        result=result,
        metadata=metadata,
    )
    storage.record_trace(trace)

    if error:
        raise error
    return 0
