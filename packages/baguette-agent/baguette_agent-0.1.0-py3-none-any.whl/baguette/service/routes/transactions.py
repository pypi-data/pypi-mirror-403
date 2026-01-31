from __future__ import annotations

from typing import Any, Dict, Optional

from ...api import validate_with_pipeline
from ...memory import (
    LLMVerifierAgent,
    MemoryEntry,
    ValidationPipeline,
    ValidationPolicy,
    ValidationRecord,
)


def register(app, storage, _raise_http, Body, Query) -> None:
    @app.post("/transactions")
    def begin_transaction(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            tx_id = storage.begin_transaction(
                actor=payload.get("actor", ""),
                reason=payload.get("reason", ""),
                metadata=payload.get("metadata"),
                idempotency_key=payload.get("idempotency_key"),
                lineage=payload.get("lineage"),
            )
            return {"tx_id": tx_id}
        except Exception as exc:
            _raise_http(exc)

    @app.get("/transactions/{tx_id}")
    def get_transaction(tx_id: str) -> Dict[str, Any]:
        try:
            tx = storage.get_transaction(tx_id)
            return tx.to_dict()
        except Exception as exc:
            _raise_http(exc)

    @app.get("/transactions/{tx_id}/memory")
    def list_staged_memory(
        tx_id: str,
        key: Optional[str] = Query(default=None),
        entry_type: Optional[str] = Query(default=None),
        source: Optional[str] = Query(default=None),
        min_confidence: Optional[float] = Query(default=None),
        max_confidence: Optional[float] = Query(default=None),
        limit: int = Query(default=100),
    ) -> Dict[str, Any]:
        try:
            entries = [
                entry.to_dict()
                for entry in storage.list_staged_memory(
                    tx_id,
                    key=key,
                    entry_type=entry_type,
                    source=source,
                    min_confidence=min_confidence,
                    max_confidence=max_confidence,
                    limit=limit,
                )
            ]
            return {"entries": entries}
        except Exception as exc:
            _raise_http(exc)

    @app.post("/transactions/{tx_id}/memory")
    def stage_memory(tx_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            entry = MemoryEntry.new(
                key=payload.get("key", ""),
                value=payload.get("value"),
                type=payload.get("type", ""),
                source=payload.get("source", ""),
                confidence=payload.get("confidence", 0.8),
                metadata=payload.get("metadata"),
                lineage=payload.get("lineage"),
                idempotency_key=payload.get("idempotency_key"),
                tx_id=tx_id,
            )
            storage.stage_memory(tx_id, entry)
            return {"entry_id": entry.entry_id, "tx_id": tx_id}
        except Exception as exc:
            _raise_http(exc)

    @app.post("/transactions/{tx_id}/validate")
    def validate_transaction(tx_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            metadata = payload.get("metadata") or {}
            policy_payload = payload.get("policy")
            pipeline_name = payload.get("pipeline")

            if policy_payload:
                policy = ValidationPolicy.from_dict(policy_payload)
                pipeline = policy.build_pipeline()

                if payload.get("verifier") == "sample":

                    def _sample_client(prompt: str) -> Dict[str, Any]:
                        return {
                            "status": "approved",
                            "confidence": 0.9,
                            "evidence": "Sample verifier approved the update.",
                            "metadata": {"prompt_chars": len(prompt)},
                        }

                    pipeline.verifier = LLMVerifierAgent(_sample_client, validator_id="sample_verifier")

                record = validate_with_pipeline(
                    storage,
                    tx_id=tx_id,
                    pipeline=pipeline,
                    context_metadata=metadata,
                    memory_limit=payload.get("memory_limit", 50),
                )
                return record.to_dict()

            if pipeline_name:
                if pipeline_name != "default":
                    raise ValueError("Only the 'default' pipeline is supported.")
                verifier = None
                if payload.get("verifier") == "sample":

                    def _sample_client(prompt: str) -> Dict[str, Any]:
                        return {
                            "status": "approved",
                            "confidence": 0.9,
                            "evidence": "Sample verifier approved the update.",
                            "metadata": {"prompt_chars": len(prompt)},
                        }

                    verifier = LLMVerifierAgent(_sample_client, validator_id="sample_verifier")

                pipeline = ValidationPipeline.default(
                    confidence_threshold=payload.get("confidence_threshold", 0.8),
                    enable_contradiction_check=not payload.get("no_contradiction_check", False),
                    enable_staged_conflict_check=not payload.get("no_staged_conflict_check", False),
                    verifier=verifier,
                )
                record = validate_with_pipeline(
                    storage,
                    tx_id=tx_id,
                    pipeline=pipeline,
                    context_metadata=metadata,
                    memory_limit=payload.get("memory_limit", 50),
                )
                return record.to_dict()

            validation = ValidationRecord(
                status=payload.get("status", ""),
                confidence=payload.get("confidence", 0.8),
                evidence=payload.get("evidence", ""),
                validator=payload.get("validator", ""),
                metadata=metadata,
                idempotency_key=payload.get("idempotency_key"),
            )
            storage.validate_transaction(tx_id, validation)
            return validation.to_dict()
        except Exception as exc:
            _raise_http(exc)

    @app.post("/transactions/{tx_id}/commit")
    def commit_transaction(
        tx_id: str, payload: Optional[Dict[str, Any]] = Body(default=None)
    ) -> Dict[str, Any]:
        try:
            validation = None
            supersede = False
            if payload:
                validation = ValidationRecord(
                    status=payload.get("status", ""),
                    confidence=payload.get("confidence", 0.8),
                    evidence=payload.get("evidence", ""),
                    validator=payload.get("validator", ""),
                    metadata=payload.get("metadata") or {},
                    idempotency_key=payload.get("idempotency_key"),
                )
                supersede = bool(payload.get("supersede", False))
            storage.commit_transaction(tx_id, validation, supersede=supersede)
            return {"tx_id": tx_id, "status": "committed"}
        except Exception as exc:
            _raise_http(exc)

    @app.post("/transactions/{tx_id}/rollback")
    def rollback_transaction(tx_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            reason = payload.get("reason", "")
            if not reason:
                raise ValueError("Rollback reason is required.")
            storage.rollback_transaction(tx_id, reason)
            return {"tx_id": tx_id, "status": "rolled_back"}
        except Exception as exc:
            _raise_http(exc)

    @app.post("/transactions/{tx_id}/approve")
    def approve_transaction(tx_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            validation = ValidationRecord(
                status="approved",
                confidence=payload.get("confidence", 0.95),
                evidence=payload.get("evidence", ""),
                validator=payload.get("validator", ""),
                metadata=payload.get("metadata") or {},
                idempotency_key=payload.get("idempotency_key"),
            )
            storage.validate_transaction(tx_id, validation)
            return validation.to_dict()
        except Exception as exc:
            _raise_http(exc)

    @app.post("/transactions/{tx_id}/reject")
    def reject_transaction(tx_id: str, payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            validation = ValidationRecord(
                status="rejected",
                confidence=payload.get("confidence", 0.95),
                evidence=payload.get("evidence", ""),
                validator=payload.get("validator", ""),
                metadata=payload.get("metadata") or {},
                idempotency_key=payload.get("idempotency_key"),
            )
            storage.validate_transaction(tx_id, validation)
            return validation.to_dict()
        except Exception as exc:
            _raise_http(exc)
