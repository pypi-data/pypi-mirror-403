from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

import yaml

from .validation import (
    ConfidenceThresholdRule,
    ContradictionRule,
    PIICheckRule,
    RuleEngine,
    StagedConflictRule,
    ValidationPipeline,
)


class PolicyError(ValueError):
    pass


@dataclass
class RulePolicy:
    name: str
    enabled: bool = True
    on_fail: str = "reject"
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise PolicyError("Rule name must be a non-empty string.")
        if self.on_fail not in {"reject", "needs_review"}:
            raise PolicyError("on_fail must be 'reject' or 'needs_review'.")
        if not isinstance(self.config, dict):
            raise PolicyError("Rule config must be a dictionary.")


@dataclass
class ValidationPolicy:
    version: str = "1.0"
    rules: List[RulePolicy] = field(default_factory=list)
    require_human_approval: bool = False

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ValidationPolicy":
        if not isinstance(payload, dict):
            raise PolicyError("Policy payload must be a dictionary.")

        version = payload.get("version", "1.0")
        require_human = bool(payload.get("require_human_approval", False))
        raw_rules = payload.get("rules", [])
        if not isinstance(raw_rules, list):
            raise PolicyError("Policy rules must be a list.")

        rules: List[RulePolicy] = []
        for raw_rule in raw_rules:
            if not isinstance(raw_rule, dict):
                raise PolicyError("Each rule definition must be a dictionary.")
            name = raw_rule.get("name", "")
            enabled = raw_rule.get("enabled", True)
            on_fail = raw_rule.get("on_fail", "reject")
            config = raw_rule.get("config", {})
            rules.append(RulePolicy(name=name, enabled=enabled, on_fail=on_fail, config=config))

        return cls(version=version, rules=rules, require_human_approval=require_human)

    @classmethod
    def from_file(cls, path: str | Path) -> "ValidationPolicy":
        source = Path(path)
        if not source.exists():
            raise PolicyError(f"Policy file not found: {source}")
        raw = source.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise PolicyError("Policy file must parse to a dictionary.")
        return cls.from_dict(data)

    def build_pipeline(self) -> ValidationPipeline:
        rules = []
        rule_policies: Dict[str, RulePolicy] = {}
        for rule in self.rules:
            if not rule.enabled:
                continue
            if rule.name == "confidence_threshold":
                threshold = rule.config.get("threshold", 0.8)
                rules.append(ConfidenceThresholdRule(float(threshold)))
            elif rule.name == "contradiction_check":
                rules.append(ContradictionRule())
            elif rule.name == "staged_conflict_check":
                rules.append(StagedConflictRule())
            elif rule.name == "pii_check":
                rules.append(
                    PIICheckRule(
                        patterns=rule.config.get("patterns"),
                        allowlist_keys=rule.config.get("allowlist_keys"),
                        allowlist_types=rule.config.get("allowlist_types"),
                        max_matches=rule.config.get("max_matches", 5),
                    )
                )
            else:
                raise PolicyError(f"Unknown rule: {rule.name}")

            rule_policies[rule.name] = rule

        return ValidationPipeline(
            rule_engine=RuleEngine(rules),
            rule_policies=rule_policies,
            require_human_approval=self.require_human_approval,
        )
