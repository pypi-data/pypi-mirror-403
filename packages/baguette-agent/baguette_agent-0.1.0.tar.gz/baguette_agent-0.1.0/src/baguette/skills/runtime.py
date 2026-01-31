from __future__ import annotations

import ast
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence

from ..errors import ExecutionError
from .artifacts import SkillArtifact
from .templating import render_template


_ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.UAdd,
    ast.USub,
)


@dataclass
class StepRunResult:
    steps_run: int
    last_exit: int
    failed_command: Optional[str] = None
    failed_step: Optional[int] = None
    timed_out: bool = False

    @property
    def failed(self) -> bool:
        return self.failed_command is not None


@dataclass
class ConstraintResult:
    passed: bool
    checked: bool
    constraints_run: int
    failed_command: Optional[str] = None
    exit_code: Optional[int] = None


@dataclass
class RunResult:
    status: str
    metadata: Dict[str, Any]
    error: Optional[str] = None
    output: Optional[str] = None


@dataclass
class SkillRunResult:
    skill_ref: str
    skill_type: str
    run: RunResult
    attempt: int = 1
    max_attempts: int = 1
    duration_ms: int = 0
    idempotency_key: Optional[str] = None


@dataclass
class SkillRunConfig:
    max_attempts: int = 1
    retry_on: list[str] = field(default_factory=lambda: ["timeout"])
    backoff_ms: list[int] = field(default_factory=list)
    total_timeout_s: Optional[float] = None
    step_timeout_s: Optional[float] = None
    idempotency_key: Optional[str] = None

    def normalize(self) -> "SkillRunConfig":
        if self.max_attempts <= 0:
            self.max_attempts = 1
        self.retry_on = [item for item in self.retry_on if isinstance(item, str)]
        self.backoff_ms = [max(0, int(item)) for item in self.backoff_ms]
        return self


def _validate_condition_ast(node: ast.AST, allowed_names: set[str]) -> None:
    for child in ast.walk(node):
        if not isinstance(child, _ALLOWED_AST_NODES):
            raise ExecutionError(f"Unsupported success condition expression: {type(child).__name__}")
        if isinstance(child, ast.Name) and child.id not in allowed_names:
            raise ExecutionError(f"Unknown name in success condition: {child.id}")


def _evaluate_condition(condition: str, context: Dict[str, Any]) -> bool:
    expression = condition.strip()
    if not expression:
        return True
    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ExecutionError(f"Invalid success condition: {exc.msg}") from exc
    _validate_condition_ast(parsed, set(context.keys()))
    result = eval(compile(parsed, "<success_condition>", "eval"), {"__builtins__": {}}, context)
    return bool(result)


def _run_constraints(
    constraints: Sequence[str],
    inputs: Dict[str, Any],
    dry_run: bool,
    *,
    timeout_s: Optional[float] = None,
    start_time: Optional[float] = None,
    total_timeout_s: Optional[float] = None,
) -> ConstraintResult:
    if not constraints:
        return ConstraintResult(passed=True, checked=True, constraints_run=0)

    constraints_run = 0
    for idx, raw in enumerate(constraints, start=1):
        if not isinstance(raw, str) or not raw.strip():
            raise ExecutionError("Constraint entries must be non-empty strings.")
        rendered = render_template(raw, inputs)
        constraints_run += 1
        if start_time is not None and total_timeout_s is not None:
            if time.monotonic() - start_time > total_timeout_s:
                return ConstraintResult(
                    passed=False,
                    checked=True,
                    constraints_run=constraints_run,
                    failed_command=rendered,
                    exit_code=None,
                )
        if dry_run:
            print(f"[dry-run] {rendered}")
            continue
        try:
            result = subprocess.run(rendered, shell=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return ConstraintResult(
                passed=False,
                checked=True,
                constraints_run=constraints_run,
                failed_command=rendered,
                exit_code=None,
            )
        if result.returncode != 0:
            return ConstraintResult(
                passed=False,
                checked=True,
                constraints_run=constraints_run,
                failed_command=rendered,
                exit_code=result.returncode,
            )

    return ConstraintResult(passed=True, checked=not dry_run, constraints_run=constraints_run)


def _run_steps(
    steps: Sequence[Dict[str, Any]],
    inputs: Dict[str, Any],
    dry_run: bool,
    *,
    label: str,
    timeout_s: Optional[float] = None,
    start_time: Optional[float] = None,
    total_timeout_s: Optional[float] = None,
) -> StepRunResult:
    steps_run = 0
    last_exit = 0

    for idx, step in enumerate(steps, start=1):
        note = step.get("note")
        if note:
            print(f"[{label} {idx}] {note}")

        command = step.get("run")
        if not command:
            continue

        rendered = render_template(command, inputs)
        steps_run += 1
        if start_time is not None and total_timeout_s is not None:
            if time.monotonic() - start_time > total_timeout_s:
                return StepRunResult(
                    steps_run=steps_run,
                    last_exit=last_exit,
                    failed_command=rendered,
                    failed_step=idx,
                    timed_out=True,
                )
        if dry_run:
            print(f"[dry-run] {rendered}")
            continue

        try:
            result = subprocess.run(rendered, shell=True, timeout=timeout_s)
            last_exit = result.returncode
            if result.returncode != 0:
                return StepRunResult(
                    steps_run=steps_run,
                    last_exit=last_exit,
                    failed_command=rendered,
                    failed_step=idx,
                )
        except subprocess.TimeoutExpired:
            return StepRunResult(
                steps_run=steps_run,
                last_exit=last_exit,
                failed_command=rendered,
                failed_step=idx,
                timed_out=True,
            )

    return StepRunResult(steps_run=steps_run, last_exit=last_exit)


def run_workflow(
    spec: Dict[str, Any],
    inputs: Dict[str, Any],
    dry_run: bool = False,
    *,
    total_timeout_s: Optional[float] = None,
    step_timeout_s: Optional[float] = None,
) -> RunResult:
    steps = spec.get("steps", [])
    constraints = spec.get("constraints") or []
    fallback = spec.get("fallback") or []
    success = spec.get("success") or {}
    condition = success.get("condition") if isinstance(success, dict) else None

    if not isinstance(steps, list):
        raise ExecutionError("Workflow steps must be a list.")
    if not isinstance(constraints, list):
        raise ExecutionError("Workflow constraints must be a list of strings.")
    if not isinstance(fallback, list):
        raise ExecutionError("Workflow fallback must be a list of steps.")

    metadata: Dict[str, Any] = {}
    start_time = time.monotonic()
    constraint_result = _run_constraints(
        constraints,
        inputs,
        dry_run,
        timeout_s=step_timeout_s,
        start_time=start_time,
        total_timeout_s=total_timeout_s,
    )
    metadata.update(
        {
            "constraints_checked": constraint_result.checked,
            "constraints_passed": constraint_result.passed,
            "constraints_run": constraint_result.constraints_run,
        }
    )
    if not constraint_result.passed:
        metadata.update(
            {
                "constraint_failed_command": constraint_result.failed_command,
                "constraint_exit_code": constraint_result.exit_code,
            }
        )
        if total_timeout_s is not None and time.monotonic() - start_time > total_timeout_s:
            metadata["timeout"] = True
            return RunResult(
                status="timeout",
                metadata=metadata,
                error=f"Workflow exceeded total timeout: {total_timeout_s}s",
            )
        if step_timeout_s is not None and constraint_result.exit_code is None:
            metadata["timeout"] = True
            return RunResult(
                status="timeout",
                metadata=metadata,
                error=f"Constraint exceeded timeout: {step_timeout_s}s",
            )
        return RunResult(status="skipped", metadata=metadata)

    step_result = _run_steps(
        steps,
        inputs,
        dry_run,
        label="step",
        timeout_s=step_timeout_s,
        start_time=start_time,
        total_timeout_s=total_timeout_s,
    )
    metadata.update(
        {
            "steps_run": step_result.steps_run,
            "last_exit": step_result.last_exit,
        }
    )
    if step_result.failed:
        metadata.update(
            {
                "failed_step": step_result.failed_step,
                "failed_command": step_result.failed_command,
            }
        )

    success_met = True
    if condition:
        context = {
            "last_exit_code": step_result.last_exit,
            "steps_run": step_result.steps_run,
        }
        success_met = _evaluate_condition(condition, context)
        metadata["success_condition"] = condition
        metadata["success_condition_met"] = success_met

    if not step_result.failed and success_met:
        return RunResult(status="success", metadata=metadata)

    error = None
    if step_result.failed:
        if total_timeout_s is not None and time.monotonic() - start_time > total_timeout_s:
            metadata["timeout"] = True
            error = f"Workflow exceeded total timeout: {total_timeout_s}s"
            return RunResult(status="timeout", metadata=metadata, error=error)
        if step_result.timed_out:
            metadata["timeout"] = True
            error = f"Step exceeded timeout: {step_timeout_s}s"
            return RunResult(status="timeout", metadata=metadata, error=error)
        error = f"Command failed with exit code {step_result.last_exit}: {step_result.failed_command}"
    elif condition and not success_met:
        error = f"Success condition not met: {condition}"

    if fallback:
        fallback_result = _run_steps(
            fallback,
            inputs,
            dry_run,
            label="fallback",
            timeout_s=step_timeout_s,
            start_time=start_time,
            total_timeout_s=total_timeout_s,
        )
        metadata.update(
            {
                "fallback_run": True,
                "fallback_steps_run": fallback_result.steps_run,
                "fallback_last_exit": fallback_result.last_exit,
                "fallback_failed_step": fallback_result.failed_step,
                "fallback_failed_command": fallback_result.failed_command,
            }
        )
        if fallback_result.failed:
            error = (
                f"Fallback command failed with exit code {fallback_result.last_exit}: "
                f"{fallback_result.failed_command}"
            )
    else:
        metadata["fallback_run"] = False

    return RunResult(status="failure", metadata=metadata, error=error)


def run_prompt(spec: Dict[str, Any], inputs: Dict[str, Any]) -> RunResult:
    content = spec.get("content", "")
    rendered = render_template(content, inputs)
    return RunResult(status="success", metadata={"rendered_length": len(rendered)}, output=rendered)


def _should_retry(status: str, retry_on: Sequence[str]) -> bool:
    return status in retry_on


def _sleep_backoff(backoff_ms: Sequence[int], attempt: int) -> None:
    if not backoff_ms:
        return
    idx = min(len(backoff_ms) - 1, max(0, attempt - 1))
    delay_ms = backoff_ms[idx]
    if delay_ms > 0:
        time.sleep(delay_ms / 1000.0)


def run_skill(
    skill: SkillArtifact,
    inputs: Dict[str, Any],
    dry_run: bool = False,
    run_config: Optional[SkillRunConfig] = None,
) -> SkillRunResult:
    run_config = run_config.normalize() if run_config else SkillRunConfig().normalize()
    start_all = time.monotonic()
    attempt = 1
    last_run: RunResult | None = None

    while attempt <= run_config.max_attempts:
        if skill.type == "workflow":
            run_result = run_workflow(
                skill.spec,
                inputs,
                dry_run,
                total_timeout_s=run_config.total_timeout_s,
                step_timeout_s=run_config.step_timeout_s,
            )
        elif skill.type == "prompt":
            run_result = run_prompt(skill.spec, inputs)
        else:
            raise ExecutionError(f"Unsupported skill type: {skill.type}")

        last_run = run_result
        if run_result.status == "success":
            break
        if not _should_retry(run_result.status, run_config.retry_on):
            break
        if attempt >= run_config.max_attempts:
            break
        _sleep_backoff(run_config.backoff_ms, attempt)
        attempt += 1

    duration_ms = int(max(0.0, (time.monotonic() - start_all) * 1000))
    if last_run is None:
        last_run = RunResult(status="failure", metadata={}, error="No run result.")
    return SkillRunResult(
        skill_ref=skill.ref(),
        skill_type=skill.type,
        run=last_run,
        attempt=attempt,
        max_attempts=run_config.max_attempts,
        duration_ms=duration_ms,
        idempotency_key=run_config.idempotency_key,
    )
