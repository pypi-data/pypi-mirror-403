from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Protocol
import math

from ..memory.transactions import MemoryEntry
from ..storage.base import StorageBackend


@dataclass
class AdapterContext:
    storage: StorageBackend
    tx_id: Optional[str] = None
    actor: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def _estimate_tokens(text: str, *, chars_per_token: int) -> int:
    if chars_per_token <= 0:
        return len(text)
    return max(1, int(math.ceil(len(text) / chars_per_token)))


def _tokens_to_chars(tokens: int, *, chars_per_token: int) -> int:
    if chars_per_token <= 0:
        return max(0, tokens)
    return max(0, tokens * chars_per_token)


@dataclass
class PromptBudget:
    max_tokens: int = 1000
    chars_per_token: int = 4

    def apply(self, base_prompt: str, prompt: str) -> str:
        if self.max_tokens <= 0:
            return base_prompt

        base_tokens = _estimate_tokens(base_prompt, chars_per_token=self.chars_per_token)
        total_tokens = _estimate_tokens(prompt, chars_per_token=self.chars_per_token)
        injected_tokens = max(0, total_tokens - base_tokens)
        if injected_tokens <= self.max_tokens:
            return prompt

        allowed_injected_chars = _tokens_to_chars(
            self.max_tokens,
            chars_per_token=self.chars_per_token,
        )
        if allowed_injected_chars <= 0:
            return base_prompt

        idx = prompt.find(base_prompt)
        if idx != -1:
            prefix = prompt[:idx]
            suffix = prompt[idx + len(base_prompt) :]
            if len(prefix) + len(suffix) <= allowed_injected_chars:
                return prompt

            if len(prefix) > allowed_injected_chars:
                prefix = prefix[-allowed_injected_chars:]
                suffix = ""
            else:
                remaining = allowed_injected_chars - len(prefix)
                suffix = suffix[:remaining]

            return f"{prefix}{base_prompt}{suffix}"

        allowed_total_chars = _tokens_to_chars(
            base_tokens + self.max_tokens,
            chars_per_token=self.chars_per_token,
        )
        if len(prompt) <= allowed_total_chars:
            return prompt
        return prompt[:allowed_total_chars]


class AdapterHooks(Protocol):
    def on_write(self, entries: Iterable[MemoryEntry], context: AdapterContext) -> None:
        ...

    def before_prompt(self, prompt: str, context: AdapterContext) -> str:
        ...

    def after_action(self, action: str, result: Any, context: AdapterContext) -> None:
        ...


class AdapterPipeline:
    def __init__(
        self,
        hooks: Optional[Iterable[AdapterHooks]] = None,
        *,
        max_injected_tokens: Optional[int] = 1000,
        chars_per_token: int = 4,
    ) -> None:
        self._hooks = list(hooks or [])
        self._prompt_budget = (
            PromptBudget(max_tokens=max_injected_tokens, chars_per_token=chars_per_token)
            if max_injected_tokens is not None
            else None
        )

    def register(self, hook: AdapterHooks) -> None:
        self._hooks.append(hook)

    def on_write(self, entries: Iterable[MemoryEntry], context: AdapterContext) -> None:
        for hook in self._hooks:
            handler = getattr(hook, "on_write", None)
            if callable(handler):
                handler(entries, context)

    def before_prompt(self, prompt: str, context: AdapterContext) -> str:
        current = prompt
        base_prompt = prompt
        for hook in self._hooks:
            handler = getattr(hook, "before_prompt", None)
            if callable(handler):
                updated = handler(current, context)
                if isinstance(updated, str):
                    current = updated
        if self._prompt_budget:
            current = self._prompt_budget.apply(base_prompt, current)
        return current

    def after_action(self, action: str, result: Any, context: AdapterContext) -> None:
        for hook in self._hooks:
            handler = getattr(hook, "after_action", None)
            if callable(handler):
                handler(action, result, context)
