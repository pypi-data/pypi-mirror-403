from __future__ import annotations

import argparse
import copy
import json

from ...skills import SkillResolutionConfig, load_skill_file, resolve_skills
from ..utils import format_table, parse_json_arg, parse_skill_ref


def register(subparsers: argparse._SubParsersAction) -> None:
    import_parser = subparsers.add_parser("import", help="Import a skill artifact")
    import_parser.add_argument("path", help="Path to skill file (.yaml, .yml, .json, .md)")
    import_parser.add_argument("--name", help="Override skill name")
    import_parser.add_argument("--version", help="Override skill version")
    import_parser.add_argument("--type", choices=["workflow", "prompt"], help="Override skill type")
    import_parser.add_argument("--lineage", help="JSON object with lineage metadata")
    import_parser.add_argument("--idempotency-key", help="Idempotency key for publish")
    import_parser.set_defaults(handler=handle_import, needs_storage=True)

    artifact_parser = subparsers.add_parser("artifact", help="Artifact registry commands")
    artifact_sub = artifact_parser.add_subparsers(dest="artifact_command", required=True)

    artifact_publish = artifact_sub.add_parser("publish", help="Publish an artifact")
    artifact_publish.add_argument("path", help="Path to skill file (.yaml, .yml, .json, .md)")
    artifact_publish.add_argument("--name", help="Override skill name")
    artifact_publish.add_argument("--version", help="Override skill version")
    artifact_publish.add_argument("--type", choices=["workflow", "prompt"], help="Override skill type")
    artifact_publish.add_argument("--lineage", help="JSON object with lineage metadata")
    artifact_publish.add_argument("--idempotency-key", help="Idempotency key for publish")
    artifact_publish.set_defaults(handler=handle_artifact_publish, needs_storage=True)

    artifact_get = artifact_sub.add_parser("get", help="Get an artifact")
    artifact_get.add_argument("artifact_ref", help="Artifact reference name@version")
    artifact_get.add_argument("--format", choices=["json", "spec"], default="json")
    artifact_get.set_defaults(handler=handle_artifact_get, needs_storage=True)

    artifact_tag = artifact_sub.add_parser("tag", help="Tag or retag an artifact")
    artifact_tag.add_argument("artifact_ref", help="Artifact reference name@version")
    artifact_tag.add_argument("--add", action="append", default=[], help="Tag to add (repeatable)")
    artifact_tag.add_argument("--remove", action="append", default=[], help="Tag to remove (repeatable)")
    artifact_tag.add_argument("--set", dest="set_tags", help="JSON array to replace tags")
    artifact_tag.set_defaults(handler=handle_artifact_tag, needs_storage=True)

    artifact_resolve = artifact_sub.add_parser("resolve", help="Render a skill prompt section")
    artifact_resolve.add_argument("artifact_ref", nargs="?", help="Artifact reference name@version")
    artifact_resolve.add_argument("--path", help="Resolve a local skill file without publishing")
    artifact_resolve.add_argument("--mode", choices=["ref", "summary", "full"], default="summary")
    artifact_resolve.add_argument("--format", choices=["bullets", "json"], default="bullets")
    artifact_resolve.add_argument("--section-title", default="Skill Context")
    artifact_resolve.add_argument("--placement", choices=["append", "prepend"], default="append")
    artifact_resolve.add_argument("--max-tokens", type=int, default=300)
    artifact_resolve.add_argument("--max-entries", type=int, default=10)
    artifact_resolve.add_argument("--description-max-chars", type=int, default=160)
    artifact_resolve.add_argument("--content-max-chars", type=int, default=2000)
    artifact_resolve.add_argument("--include-description", action="store_true", default=None)
    artifact_resolve.add_argument("--include-tags", action="store_true", default=None)
    artifact_resolve.add_argument("--include-type", action="store_true", default=None)
    artifact_resolve.add_argument("--include-inputs", action="store_true")
    artifact_resolve.add_argument("--include-outputs", action="store_true")
    artifact_resolve.add_argument("--include-steps", action="store_true")
    artifact_resolve.add_argument("--max-steps", type=int, default=5)
    artifact_resolve.add_argument("--step-max-chars", type=int, default=120)
    artifact_resolve.add_argument("--io-schema-mode", choices=["names", "schema"], default="names")
    artifact_resolve.set_defaults(handler=handle_artifact_resolve, needs_storage=True)

    list_parser = subparsers.add_parser("list", help="List skills")
    list_parser.add_argument("--name", help="Filter by name")
    list_parser.add_argument("--format", choices=["table", "json"], default="table")
    list_parser.set_defaults(handler=handle_list, needs_storage=True)


def handle_import(storage, args: argparse.Namespace) -> int:
    args.lineage = getattr(args, "lineage", None)
    args.idempotency_key = getattr(args, "idempotency_key", None)
    return handle_artifact_publish(storage, args)


def handle_artifact_publish(storage, args: argparse.Namespace) -> int:
    lineage = parse_json_arg(args.lineage, "--lineage", {})
    artifact = load_skill_file(
        args.path,
        name=args.name,
        version=args.version,
        skill_type=args.type,
        lineage=lineage,
        idempotency_key=args.idempotency_key,
    )
    storage.upsert_skill(artifact)
    print(f"Published {artifact.ref()} ({artifact.type})")
    return 0


def handle_artifact_get(storage, args: argparse.Namespace) -> int:
    name, version = parse_skill_ref(args.artifact_ref)
    artifact = storage.get_skill(name, version)
    if args.format == "spec":
        print(json.dumps(artifact.spec, indent=2))
    else:
        print(json.dumps(artifact.to_dict(), indent=2))
    return 0


def handle_artifact_resolve(storage, args: argparse.Namespace) -> int:
    if args.path and args.artifact_ref:
        raise ValueError("Use either artifact_ref or --path, not both.")
    if not args.path and not args.artifact_ref:
        raise ValueError("Provide artifact_ref or --path to resolve a skill.")

    if args.path:
        artifact = load_skill_file(args.path)
    else:
        name, version = parse_skill_ref(args.artifact_ref)
        artifact = storage.get_skill(name, version)
    config = SkillResolutionConfig(
        section_title=args.section_title,
        placement=args.placement,
        format=args.format,
        mode=args.mode,
        max_tokens=args.max_tokens,
        max_entries=args.max_entries,
        description_max_chars=args.description_max_chars,
        content_max_chars=args.content_max_chars,
        include_description=True if args.include_description is None else args.include_description,
        include_tags=True if args.include_tags is None else args.include_tags,
        include_type=False if args.include_type is None else args.include_type,
        include_inputs=args.include_inputs,
        include_outputs=args.include_outputs,
        include_steps=args.include_steps,
        max_steps=args.max_steps,
        step_max_chars=args.step_max_chars,
        io_schema_mode=args.io_schema_mode,
    )
    rendered = resolve_skills([artifact], config)
    if rendered:
        print(rendered)
    return 0


def handle_list(storage, args: argparse.Namespace) -> int:
    skills = list(storage.list_skills(name=args.name))
    if args.format == "json":
        payload = [skill.to_dict() for skill in skills]
        print(json.dumps(payload, indent=2))
        return 0

    rows = [[skill.name, skill.version, skill.type] for skill in skills]
    if not rows:
        print("No skills found.")
        return 0

    print(format_table(["NAME", "VERSION", "TYPE"], rows))
    return 0


def _normalize_tags(tags: list[object]) -> list[str]:
    normalized = []
    for tag in tags:
        if not isinstance(tag, str):
            continue
        stripped = tag.strip()
        if not stripped:
            continue
        if stripped not in normalized:
            normalized.append(stripped)
    return normalized


def handle_artifact_tag(storage, args: argparse.Namespace) -> int:
    name, version = parse_skill_ref(args.artifact_ref)
    artifact = storage.get_skill(name, version)

    tags = artifact.spec.get("tags") or []
    if not isinstance(tags, list):
        raise ValueError("Skill tags must be a list.")

    if args.set_tags:
        tags = parse_json_arg(args.set_tags, "--set", [])
        if not isinstance(tags, list):
            raise ValueError("--set must be a JSON array.")

    tags = _normalize_tags(tags)
    remove = {tag.strip() for tag in args.remove if isinstance(tag, str) and tag.strip()}
    tags = [tag for tag in tags if tag not in remove]
    tags.extend(_normalize_tags(args.add))
    tags = _normalize_tags(tags)

    updated_spec = copy.deepcopy(artifact.spec)
    updated_spec["tags"] = tags

    updated = artifact.__class__(
        artifact_id=artifact.artifact_id,
        name=artifact.name,
        version=artifact.version,
        type=artifact.type,
        kind=artifact.kind,
        spec=updated_spec,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
        idempotency_key=artifact.idempotency_key,
        lineage=artifact.lineage,
    )
    storage.upsert_skill(updated)
    print(f"Tagged {artifact.ref()} tags={json.dumps(tags, ensure_ascii=False)}")
    return 0
