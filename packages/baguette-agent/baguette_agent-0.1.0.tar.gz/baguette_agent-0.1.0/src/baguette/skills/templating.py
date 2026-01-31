from __future__ import annotations

from string import Formatter
from typing import Any, Dict
import re

from jinja2 import StrictUndefined, TemplateError
from jinja2.sandbox import SandboxedEnvironment


_LEGACY_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_JINJA_ENV = SandboxedEnvironment(undefined=StrictUndefined, autoescape=False)


class _LegacyFormatter(Formatter):
    def get_field(self, field_name: str, args: tuple[object, ...], kwargs: Dict[str, Any]):
        if not _LEGACY_FIELD_RE.match(field_name):
            raise ValueError(f"Unsafe legacy placeholder: {field_name!r}")
        return super().get_field(field_name, args, kwargs)


def _render_legacy(template: str, inputs: Dict[str, Any]) -> str:
    formatter = _LegacyFormatter()
    for _, field_name, format_spec, conversion in formatter.parse(template):
        if field_name is None:
            continue
        if conversion:
            raise ValueError("Legacy templates do not allow conversions (e.g. {!r}).")
        if format_spec:
            raise ValueError("Legacy templates do not allow format specs.")

    try:
        return formatter.vformat(template, (), inputs)
    except KeyError as exc:
        raise ValueError(f"Missing input for template: {exc}") from exc


def _render_jinja(template: str, inputs: Dict[str, Any]) -> str:
    try:
        compiled = _JINJA_ENV.from_string(template)
        return compiled.render(inputs)
    except TemplateError as exc:
        raise ValueError(f"Template rendering error: {exc}") from exc


def render_template(template: str, inputs: Dict[str, Any]) -> str:
    if "{{" in template or "{%" in template or "{#" in template:
        return _render_jinja(template, inputs)

    return _render_legacy(template, inputs)
