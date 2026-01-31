from __future__ import annotations

from typing import Any, Dict, Optional

from ...skills import load_skill_file, load_skill_spec


def register(app, storage, _raise_http, Body, Query) -> None:
    @app.post("/skills")
    def publish_skill(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            spec = payload.get("spec")
            path = payload.get("path")
            name = payload.get("name")
            version = payload.get("version")
            skill_type = payload.get("type")
            lineage = payload.get("lineage")
            idempotency_key = payload.get("idempotency_key")
            source_label = payload.get("source_label", "<inline>")

            if path:
                artifact = load_skill_file(
                    path,
                    name=name,
                    version=version,
                    skill_type=skill_type,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                )
            elif spec is not None:
                artifact = load_skill_spec(
                    spec,
                    name=name,
                    version=version,
                    skill_type=skill_type,
                    lineage=lineage,
                    idempotency_key=idempotency_key,
                    source_label=source_label,
                )
            else:
                raise ValueError("Provide either 'spec' or 'path' to publish a skill.")

            storage.upsert_skill(artifact)
            return artifact.to_dict()
        except Exception as exc:
            _raise_http(exc)

    @app.get("/skills")
    def list_skills(name: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        try:
            skills = [skill.to_dict() for skill in storage.list_skills(name=name)]
            return {"skills": skills}
        except Exception as exc:
            _raise_http(exc)

    @app.get("/skills/{name}")
    def get_skill(name: str, version: Optional[str] = Query(default=None)) -> Dict[str, Any]:
        try:
            skill = storage.get_skill(name, version)
            return skill.to_dict()
        except Exception as exc:
            _raise_http(exc)
