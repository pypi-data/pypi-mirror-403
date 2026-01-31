from __future__ import annotations

from typing import Any, Dict, Optional

from ...audit import DecisionTrace


def register(app, storage, _raise_http, Body, Query) -> None:
    @app.post("/traces")
    def record_trace(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
        try:
            trace = DecisionTrace.new(
                decision=payload.get("decision", ""),
                skill_ref=payload.get("skill_ref"),
                reason=payload.get("reason", ""),
                confidence=payload.get("confidence", 0.8),
                result=payload.get("result", ""),
                metadata=payload.get("metadata"),
                tx_id=payload.get("tx_id"),
                lineage=payload.get("lineage"),
                idempotency_key=payload.get("idempotency_key"),
            )
            storage.record_trace(trace)
            return trace.to_dict()
        except Exception as exc:
            _raise_http(exc)

    @app.get("/traces")
    def list_traces(
        limit: int = Query(default=100),
        tx_id: Optional[str] = Query(default=None),
        decision: Optional[str] = Query(default=None),
        skill_ref: Optional[str] = Query(default=None),
        result: Optional[str] = Query(default=None),
        created_after: Optional[str] = Query(default=None),
        created_before: Optional[str] = Query(default=None),
        correlation_id: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        try:
            traces = [
                trace.to_dict()
                for trace in storage.list_traces(
                    limit=limit,
                    tx_id=tx_id,
                    decision=decision,
                    skill_ref=skill_ref,
                    result=result,
                    created_after=created_after,
                    created_before=created_before,
                    correlation_id=correlation_id,
                )
            ]
            return {"traces": traces}
        except Exception as exc:
            _raise_http(exc)
