from __future__ import annotations

from typing import Any, Dict, Optional


def register(app, storage, _raise_http, Body, Query) -> None:
    @app.get("/journal")
    def list_journal(
        limit: int = Query(default=100),
        tx_id: Optional[str] = Query(default=None),
        event_type: Optional[str] = Query(default=None),
        entity_type: Optional[str] = Query(default=None),
        entity_id: Optional[str] = Query(default=None),
    ) -> Dict[str, Any]:
        try:
            events = [
                event.to_dict()
                for event in storage.list_journal(
                    limit=limit,
                    tx_id=tx_id,
                    event_type=event_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                )
            ]
            return {"events": events}
        except Exception as exc:
            _raise_http(exc)
