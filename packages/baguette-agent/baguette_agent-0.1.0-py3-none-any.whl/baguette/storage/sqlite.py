from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Optional
import json
import sqlite3
import uuid

from ..audit.journal import JournalEvent
from ..audit.traces import DecisionTrace
from ..memory.transactions import (
    MemoryEntry,
    TransactionRecord,
    ValidationRecord,
    TX_COMMITTED,
    TX_OPEN,
    TX_ROLLED_BACK,
    TX_VALIDATED,
)
from ..skills.artifacts import SkillArtifact
from ..utils import is_semver, utcnow_iso
from .base import StorageBackend


class SQLiteStorage(StorageBackend):
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _connect(self) -> Iterable[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _add_column_if_missing(self, conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
        cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    def _ensure_index(
        self,
        conn: sqlite3.Connection,
        name: str,
        ddl: str,
        *,
        unique: bool = False,
    ) -> None:
        prefix = "CREATE UNIQUE INDEX" if unique else "CREATE INDEX"
        conn.execute(f"{prefix} IF NOT EXISTS {name} {ddl}")

    def _append_journal_event(
        self,
        conn: sqlite3.Connection,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        payload: dict,
        tx_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        event_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT OR IGNORE INTO journal
                (event_id, timestamp, event_type, entity_type, entity_id, tx_id, idempotency_key, payload_json, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                utcnow_iso(),
                event_type,
                entity_type,
                entity_id,
                tx_id,
                idempotency_key,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        return event_id

    def initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS skills (
                    artifact_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    type TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    spec_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    lineage_json TEXT,
                    PRIMARY KEY (name, version)
                );

                CREATE TABLE IF NOT EXISTS decision_traces (
                    trace_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    skill_ref TEXT,
                    reason TEXT,
                    confidence REAL,
                    result TEXT NOT NULL,
                    metadata_json TEXT,
                    tx_id TEXT,
                    lineage_json TEXT
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    tx_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL,
                    actor TEXT,
                    reason TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    committed_at TEXT,
                    rolled_back_at TEXT,
                    validation_json TEXT,
                    metadata_json TEXT,
                    lineage_json TEXT
                );

                CREATE TABLE IF NOT EXISTS memory_staging (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    tx_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    type TEXT NOT NULL,
                    source TEXT,
                    confidence REAL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT,
                    lineage_json TEXT,
                    FOREIGN KEY (tx_id) REFERENCES transactions(tx_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    type TEXT NOT NULL,
                    source TEXT,
                    confidence REAL,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT,
                    lineage_json TEXT,
                    tx_id TEXT
                );

                CREATE TABLE IF NOT EXISTS journal (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    tx_id TEXT,
                    idempotency_key TEXT,
                    payload_json TEXT NOT NULL,
                    metadata_json TEXT
                );
                """
            )

            self._add_column_if_missing(conn, "skills", "artifact_id", "TEXT")
            self._add_column_if_missing(conn, "skills", "updated_at", "TEXT")
            self._add_column_if_missing(conn, "skills", "idempotency_key", "TEXT")
            self._add_column_if_missing(conn, "skills", "lineage_json", "TEXT")

            self._add_column_if_missing(conn, "decision_traces", "idempotency_key", "TEXT")
            self._add_column_if_missing(conn, "decision_traces", "lineage_json", "TEXT")

            self._add_column_if_missing(conn, "transactions", "idempotency_key", "TEXT")
            self._add_column_if_missing(conn, "transactions", "updated_at", "TEXT")
            self._add_column_if_missing(conn, "transactions", "lineage_json", "TEXT")

            self._add_column_if_missing(conn, "memory_staging", "entry_id", "TEXT")
            self._add_column_if_missing(conn, "memory_staging", "idempotency_key", "TEXT")
            self._add_column_if_missing(conn, "memory_staging", "lineage_json", "TEXT")

            self._add_column_if_missing(conn, "memory", "entry_id", "TEXT")
            self._add_column_if_missing(conn, "memory", "idempotency_key", "TEXT")
            self._add_column_if_missing(conn, "memory", "lineage_json", "TEXT")

            self._ensure_index(conn, "idx_skills_artifact_id", "ON skills(artifact_id)", unique=True)
            self._ensure_index(conn, "idx_skills_idempotency_key", "ON skills(idempotency_key)", unique=True)
            self._ensure_index(conn, "idx_transactions_idempotency_key", "ON transactions(idempotency_key)", unique=True)
            self._ensure_index(conn, "idx_memory_staging_entry_id", "ON memory_staging(entry_id)", unique=True)
            self._ensure_index(conn, "idx_memory_staging_idempotency", "ON memory_staging(idempotency_key)", unique=True)
            self._ensure_index(conn, "idx_memory_entry_id", "ON memory(entry_id)", unique=True)
            self._ensure_index(conn, "idx_memory_idempotency", "ON memory(idempotency_key)", unique=True)
            self._ensure_index(
                conn,
                "idx_decision_traces_idempotency",
                "ON decision_traces(idempotency_key)",
                unique=True,
            )
            self._ensure_index(
                conn,
                "idx_journal_idempotency",
                "ON journal(event_type, idempotency_key)",
                unique=True,
            )
            self._ensure_index(conn, "idx_journal_tx", "ON journal(tx_id, seq)")
            self._ensure_index(conn, "idx_journal_event_type", "ON journal(event_type)")
            self._ensure_index(conn, "idx_journal_entity_type", "ON journal(entity_type)")

    def upsert_skill(self, skill: SkillArtifact) -> None:
        spec_json = json.dumps(skill.spec, ensure_ascii=False)
        lineage_json = json.dumps(skill.lineage, ensure_ascii=False)
        updated_at = utcnow_iso()
        with self._connect() as conn:
            self._append_journal_event(
                conn,
                event_type="artifact.publish",
                entity_type="artifact",
                entity_id=skill.artifact_id,
                tx_id=None,
                idempotency_key=skill.idempotency_key,
                payload={**skill.to_dict(), "updated_at": updated_at},
            )
            conn.execute(
                """
                INSERT INTO skills
                    (artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name, version) DO UPDATE SET
                    artifact_id = excluded.artifact_id,
                    type = excluded.type,
                    kind = excluded.kind,
                    spec_json = excluded.spec_json,
                    updated_at = excluded.updated_at,
                    idempotency_key = excluded.idempotency_key,
                    lineage_json = excluded.lineage_json
                """,
                (
                    skill.artifact_id,
                    skill.name,
                    skill.version,
                    skill.type,
                    skill.kind,
                    spec_json,
                    skill.created_at,
                    updated_at,
                    skill.idempotency_key,
                    lineage_json,
                ),
            )

    def list_skills(self, name: Optional[str] = None) -> Iterable[SkillArtifact]:
        query = """
            SELECT artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json
            FROM skills
        """
        params: list[object] = []
        if name:
            query += " WHERE name = ?"
            params.append(name)
        query += " ORDER BY name, version"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_skill(row) for row in rows]

    def get_skill(self, name: str, version: Optional[str] = None) -> SkillArtifact:
        with self._connect() as conn:
            if version and version != "latest":
                if is_semver(version):
                    row = conn.execute(
                        """
                        SELECT artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json
                        FROM skills WHERE name = ? AND version = ?
                        """,
                        (name, version),
                    ).fetchone()
                    if row:
                        return self._row_to_skill(row)
                    raise KeyError(f"Skill not found: {name}@{version}")

                rows = conn.execute(
                    """
                    SELECT artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json
                    FROM skills WHERE name = ?
                    """,
                    (name,),
                ).fetchall()
                skills = [self._row_to_skill(row) for row in rows]
                tagged = [skill for skill in skills if self._skill_has_tag(skill, version)]
                if not tagged:
                    raise KeyError(f"Skill not found: {name}@{version}")
                tagged.sort(key=lambda skill: skill.updated_at, reverse=True)
                return tagged[0]

            row = conn.execute(
                """
                SELECT artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json
                FROM skills WHERE name = ?
                ORDER BY updated_at DESC LIMIT 1
                """,
                (name,),
            ).fetchone()

        if not row:
            raise KeyError(f"Skill not found: {name}@{version or 'latest'}")

        return self._row_to_skill(row)

    def begin_transaction(
        self,
        actor: str,
        reason: str,
        metadata: Optional[dict] = None,
        *,
        idempotency_key: Optional[str] = None,
        lineage: Optional[dict] = None,
    ) -> str:
        record = TransactionRecord.new(
            actor=actor,
            reason=reason,
            metadata=metadata,
            lineage=lineage,
            idempotency_key=idempotency_key,
        )
        with self._connect() as conn:
            if record.idempotency_key:
                existing = conn.execute(
                    "SELECT tx_id FROM transactions WHERE idempotency_key = ?",
                    (record.idempotency_key,),
                ).fetchone()
                if existing:
                    return existing[0]

            self._append_journal_event(
                conn,
                event_type="transaction.begin",
                entity_type="transaction",
                entity_id=record.tx_id,
                tx_id=record.tx_id,
                idempotency_key=record.idempotency_key,
                payload=record.to_dict(),
            )
            conn.execute(
                """
                INSERT INTO transactions
                    (tx_id, idempotency_key, actor, reason, status, created_at, updated_at, metadata_json, lineage_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.tx_id,
                    record.idempotency_key,
                    record.actor,
                    record.reason,
                    record.status,
                    record.created_at,
                    record.updated_at,
                    json.dumps(record.metadata, ensure_ascii=False),
                    json.dumps(record.lineage, ensure_ascii=False),
                ),
            )
        return record.tx_id

    def get_transaction(self, tx_id: str) -> TransactionRecord:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT tx_id, idempotency_key, actor, reason, status, created_at, updated_at,
                       committed_at, rolled_back_at, validation_json, metadata_json, lineage_json
                FROM transactions WHERE tx_id = ?
                """,
                (tx_id,),
            ).fetchone()

        if not row:
            raise KeyError(f"Transaction not found: {tx_id}")

        return self._row_to_transaction(row)

    def stage_memory(self, tx_id: str, entry: MemoryEntry) -> None:
        with self._connect() as conn:
            tx_row = conn.execute(
                "SELECT status FROM transactions WHERE tx_id = ?", (tx_id,)
            ).fetchone()
            if not tx_row:
                raise KeyError(f"Transaction not found: {tx_id}")
            if tx_row[0] not in (TX_OPEN, TX_VALIDATED):
                raise ValueError(f"Cannot stage memory for transaction in status {tx_row[0]}")

            entry.scope_to_tx(tx_id)
            self._append_journal_event(
                conn,
                event_type="memory.stage",
                entity_type="memory_entry",
                entity_id=entry.entry_id,
                tx_id=tx_id,
                idempotency_key=entry.idempotency_key,
                payload=entry.to_dict(),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO memory_staging
                    (entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at, metadata_json, lineage_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.idempotency_key,
                    tx_id,
                    entry.key,
                    json.dumps(entry.value, ensure_ascii=False),
                    entry.type,
                    entry.source,
                    entry.confidence,
                    entry.created_at,
                    json.dumps(entry.metadata, ensure_ascii=False),
                    json.dumps(entry.lineage, ensure_ascii=False),
                ),
            )

    def list_staged_memory(
        self,
        tx_id: str,
        key: Optional[str] = None,
        entry_type: Optional[str] = None,
        source: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        limit: int = 100,
    ) -> Iterable[MemoryEntry]:
        if limit <= 0:
            return []
        filters = ["tx_id = ?"]
        params: list[object] = [tx_id]
        if key:
            filters.append("key = ?")
            params.append(key)
        if entry_type:
            filters.append("type = ?")
            params.append(entry_type)
        if source:
            filters.append("source = ?")
            params.append(source)
        if min_confidence is not None:
            filters.append("confidence >= ?")
            params.append(min_confidence)
        if max_confidence is not None:
            filters.append("confidence <= ?")
            params.append(max_confidence)
        where_clause = f"WHERE {' AND '.join(filters)}"
        query = f"""
            SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                   metadata_json, lineage_json
            FROM memory_staging
            {where_clause}
            ORDER BY id ASC
            LIMIT ?
        """
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_memory(row) for row in rows]

    def list_memory(
        self,
        key: Optional[str] = None,
        entry_type: Optional[str] = None,
        source: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        limit: int = 100,
    ) -> Iterable[MemoryEntry]:
        query = """
            SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                   metadata_json, lineage_json
            FROM memory
        """
        params: list[object] = []
        filters = []
        if key:
            filters.append("key = ?")
            params.append(key)
        if entry_type:
            filters.append("type = ?")
            params.append(entry_type)
        if source:
            filters.append("source = ?")
            params.append(source)
        if created_after:
            filters.append("created_at >= ?")
            params.append(created_after)
        if created_before:
            filters.append("created_at <= ?")
            params.append(created_before)
        if min_confidence is not None:
            filters.append("confidence >= ?")
            params.append(min_confidence)
        if max_confidence is not None:
            filters.append("confidence <= ?")
            params.append(max_confidence)
        if filters:
            query += f" WHERE {' AND '.join(filters)}"
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_memory(row) for row in rows]

    def get_memory_entry(self, entry_id: str) -> MemoryEntry:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                       metadata_json, lineage_json
                FROM memory
                WHERE entry_id = ?
                """,
                (entry_id,),
            ).fetchone()

        if not row:
            raise KeyError(f"Memory entry not found: {entry_id}")
        return self._row_to_memory(row)

    def redact_memory(
        self,
        entry_id: str,
        *,
        redacted_value: object,
        metadata: dict,
    ) -> MemoryEntry:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                       metadata_json, lineage_json
                FROM memory
                WHERE entry_id = ?
                """,
                (entry_id,),
            ).fetchone()

            if not row:
                raise KeyError(f"Memory entry not found: {entry_id}")

            existing = self._row_to_memory(row)
            merged_metadata = dict(existing.metadata)
            merged_metadata.update(metadata or {})

            self._append_journal_event(
                conn,
                event_type="memory.redact",
                entity_type="memory_entry",
                entity_id=entry_id,
                tx_id=existing.tx_id,
                idempotency_key=f"{entry_id}:redact",
                payload={
                    "entry_id": entry_id,
                    "key": existing.key,
                    "type": existing.type,
                    "redacted_metadata": merged_metadata,
                },
            )
            conn.execute(
                """
                UPDATE memory
                SET value_json = ?, metadata_json = ?
                WHERE entry_id = ?
                """,
                (
                    json.dumps(redacted_value, ensure_ascii=False),
                    json.dumps(merged_metadata, ensure_ascii=False),
                    entry_id,
                ),
            )

        return self.get_memory_entry(entry_id)

    def validate_transaction(self, tx_id: str, validation: ValidationRecord) -> None:
        validation_json = json.dumps(validation.to_dict(), ensure_ascii=False)
        validated_at = utcnow_iso()
        with self._connect() as conn:
            tx_row = conn.execute(
                "SELECT status FROM transactions WHERE tx_id = ?", (tx_id,)
            ).fetchone()
            if not tx_row:
                raise KeyError(f"Transaction not found: {tx_id}")
            if tx_row[0] in (TX_COMMITTED, TX_ROLLED_BACK):
                raise ValueError(f"Cannot validate transaction in status {tx_row[0]}")

            self._append_journal_event(
                conn,
                event_type="transaction.validate",
                entity_type="transaction",
                entity_id=tx_id,
                tx_id=tx_id,
                idempotency_key=validation.idempotency_key,
                payload=validation.to_dict(),
            )
            conn.execute(
                """
                UPDATE transactions
                SET status = ?, updated_at = ?, validation_json = ?
                WHERE tx_id = ?
                """,
                (TX_VALIDATED, validated_at, validation_json, tx_id),
            )

    def commit_transaction(
        self,
        tx_id: str,
        validation: Optional[ValidationRecord] = None,
        *,
        supersede: bool = False,
    ) -> None:
        committed_at = utcnow_iso()
        with self._connect() as conn:
            tx_row = conn.execute(
                "SELECT status, validation_json FROM transactions WHERE tx_id = ?", (tx_id,)
            ).fetchone()
            if not tx_row:
                raise KeyError(f"Transaction not found: {tx_id}")
            if tx_row[0] == TX_COMMITTED:
                return
            if tx_row[0] == TX_ROLLED_BACK:
                raise ValueError(f"Cannot commit transaction in status {tx_row[0]}")

            existing_validation = self._parse_validation(tx_row[1]) if tx_row[1] else None
            self._ensure_commit_allowed(tx_row[0], existing_validation, validation)
            if validation:
                self.validate_transaction(tx_id, validation)

            staged_rows = conn.execute(
                """
                SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                       metadata_json, lineage_json
                FROM memory_staging WHERE tx_id = ?
                """,
                (tx_id,),
            ).fetchall()
            staged_entries = [self._row_to_memory(row) for row in staged_rows]

            self._append_journal_event(
                conn,
                event_type="transaction.commit",
                entity_type="transaction",
                entity_id=tx_id,
                tx_id=tx_id,
                idempotency_key=f"{tx_id}:commit",
                payload={"tx_id": tx_id, "committed_at": committed_at},
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO memory
                    (entry_id, idempotency_key, key, value_json, type, source, confidence, created_at, metadata_json, lineage_json, tx_id)
                SELECT entry_id, idempotency_key, key, value_json, type, source, confidence, created_at, metadata_json, lineage_json, tx_id
                FROM memory_staging WHERE tx_id = ?
                """,
                (tx_id,),
            )
            if supersede and staged_entries:
                self._apply_supersede(conn, tx_id, staged_entries, committed_at=committed_at)
            conn.execute("DELETE FROM memory_staging WHERE tx_id = ?", (tx_id,))
            conn.execute(
                """
                UPDATE transactions
                SET status = ?, committed_at = ?, updated_at = ?, validation_json = COALESCE(?, validation_json)
                WHERE tx_id = ?
                """,
                (
                    TX_COMMITTED,
                    committed_at,
                    committed_at,
                    json.dumps(validation.to_dict(), ensure_ascii=False) if validation else None,
                    tx_id,
                ),
            )

    def rollback_transaction(self, tx_id: str, reason: str) -> None:
        rolled_back_at = utcnow_iso()
        with self._connect() as conn:
            tx_row = conn.execute(
                "SELECT status, metadata_json FROM transactions WHERE tx_id = ?", (tx_id,)
            ).fetchone()
            if not tx_row:
                raise KeyError(f"Transaction not found: {tx_id}")
            if tx_row[0] == TX_ROLLED_BACK:
                return
            if tx_row[0] == TX_COMMITTED:
                raise ValueError(f"Cannot rollback transaction in status {tx_row[0]}")

            metadata = json.loads(tx_row[1]) if tx_row[1] else {}
            metadata["rollback_reason"] = reason
            metadata_json = json.dumps(metadata, ensure_ascii=False)

            self._append_journal_event(
                conn,
                event_type="transaction.rollback",
                entity_type="transaction",
                entity_id=tx_id,
                tx_id=tx_id,
                idempotency_key=f"{tx_id}:rollback",
                payload={"tx_id": tx_id, "reason": reason, "rolled_back_at": rolled_back_at},
            )
            conn.execute("DELETE FROM memory_staging WHERE tx_id = ?", (tx_id,))
            conn.execute(
                """
                UPDATE transactions
                SET status = ?, rolled_back_at = ?, updated_at = ?, metadata_json = ?
                WHERE tx_id = ?
                """,
                (TX_ROLLED_BACK, rolled_back_at, rolled_back_at, metadata_json, tx_id),
            )

    def record_trace(self, trace: DecisionTrace) -> None:
        with self._connect() as conn:
            self._append_journal_event(
                conn,
                event_type="trace.record",
                entity_type="decision_trace",
                entity_id=trace.trace_id,
                tx_id=trace.tx_id,
                idempotency_key=trace.idempotency_key,
                payload=trace.to_dict(),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO decision_traces
                    (trace_id, idempotency_key, timestamp, decision, skill_ref, reason, confidence, result, metadata_json, tx_id, lineage_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.trace_id,
                    trace.idempotency_key,
                    trace.timestamp,
                    trace.decision,
                    trace.skill_ref,
                    trace.reason,
                    trace.confidence,
                    trace.result,
                    json.dumps(trace.metadata, ensure_ascii=False),
                    trace.tx_id,
                    json.dumps(trace.lineage, ensure_ascii=False),
                ),
            )

    def list_traces(
        self,
        limit: int = 100,
        tx_id: Optional[str] = None,
        decision: Optional[str] = None,
        skill_ref: Optional[str] = None,
        result: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Iterable[DecisionTrace]:
        if limit <= 0:
            return []

        filters = []
        params: list[object] = []
        if tx_id:
            filters.append("tx_id = ?")
            params.append(tx_id)
        if decision:
            filters.append("decision = ?")
            params.append(decision)
        if skill_ref:
            filters.append("skill_ref = ?")
            params.append(skill_ref)
        if result:
            filters.append("result = ?")
            params.append(result)
        if created_after:
            filters.append("timestamp >= ?")
            params.append(created_after)
        if created_before:
            filters.append("timestamp <= ?")
            params.append(created_before)
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        query = f"""
            SELECT trace_id, idempotency_key, timestamp, decision, skill_ref, reason, confidence, result, metadata_json, tx_id, lineage_json
            FROM decision_traces
            {where_clause}
            ORDER BY timestamp DESC
        """
        if correlation_id is None:
            query += " LIMIT ?"
            params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        traces: list[DecisionTrace] = []
        for row in rows:
            metadata = json.loads(row[8]) if row[8] else {}
            lineage = json.loads(row[10]) if row[10] else {}
            traces.append(
                DecisionTrace(
                    trace_id=row[0],
                    idempotency_key=row[1] or "",
                    timestamp=row[2],
                    decision=row[3],
                    skill_ref=row[4],
                    reason=row[5] or "",
                    confidence=row[6] or 0.0,
                    result=row[7],
                    metadata=metadata,
                    tx_id=row[9],
                    lineage=lineage,
                )
            )
        if correlation_id:
            def _match(trace: DecisionTrace) -> bool:
                if trace.lineage.get("correlation_id") == correlation_id:
                    return True
                return trace.metadata.get("correlation_id") == correlation_id

            traces = [trace for trace in traces if _match(trace)]
        return traces[:limit]

    def list_journal(
        self,
        limit: int = 100,
        tx_id: Optional[str] = None,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> Iterable[JournalEvent]:
        filters = []
        params: list[object] = []
        if tx_id:
            filters.append("tx_id = ?")
            params.append(tx_id)
        if event_type:
            filters.append("event_type = ?")
            params.append(event_type)
        if entity_type:
            filters.append("entity_type = ?")
            params.append(entity_type)
        if entity_id:
            filters.append("entity_id = ?")
            params.append(entity_id)

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        query = f"""
            SELECT seq, event_id, timestamp, event_type, entity_type, entity_id, tx_id, idempotency_key,
                   payload_json, metadata_json
            FROM journal
            {where_clause}
            ORDER BY seq DESC
            LIMIT ?
        """
        with self._connect() as conn:
            rows = conn.execute(query, (*params, limit)).fetchall()

        events = []
        for row in rows:
            payload = json.loads(row[8]) if row[8] else {}
            metadata = json.loads(row[9]) if row[9] else {}
            if not isinstance(payload, dict):
                payload = {"value": payload}
            if not isinstance(metadata, dict):
                metadata = {}
            events.append(
                JournalEvent(
                    event_id=row[1],
                    timestamp=row[2],
                    event_type=row[3],
                    entity_type=row[4],
                    entity_id=row[5],
                    tx_id=row[6],
                    idempotency_key=row[7],
                    payload=payload,
                    metadata=metadata,
                    seq=row[0],
                )
            )
        return events

    def _parse_validation(self, raw: Optional[str]) -> Optional[ValidationRecord]:
        if not raw:
            return None
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Invalid validation payload in storage.")
        return ValidationRecord(
            status=data.get("status", ""),
            confidence=data.get("confidence", 0.0),
            evidence=data.get("evidence", ""),
            validator=data.get("validator", ""),
            validated_at=data.get("validated_at") or "",
            metadata=data.get("metadata") or {},
            idempotency_key=data.get("idempotency_key"),
        )

    def _row_to_transaction(self, row: sqlite3.Row) -> TransactionRecord:
        validation = self._parse_validation(row[9]) if row[9] else None
        metadata = json.loads(row[10]) if row[10] else {}
        lineage = json.loads(row[11]) if row[11] else {}
        return TransactionRecord(
            tx_id=row[0],
            idempotency_key=row[1] or row[0],
            actor=row[2] or "unknown",
            reason=row[3] or "unspecified",
            status=row[4],
            created_at=row[5],
            updated_at=row[6] or row[5],
            committed_at=row[7],
            rolled_back_at=row[8],
            metadata=metadata,
            lineage=lineage,
            validation=validation,
        )

    def _row_to_memory(self, row: sqlite3.Row) -> MemoryEntry:
        value = json.loads(row[4])
        metadata = json.loads(row[9]) if row[9] else {}
        lineage = json.loads(row[10]) if row[10] else {}
        return MemoryEntry(
            entry_id=row[0] or "",
            idempotency_key=row[1] or "",
            key=row[3],
            value=value,
            type=row[5],
            source=row[6] or "",
            confidence=row[7] or 0.0,
            created_at=row[8],
            metadata=metadata,
            lineage=lineage,
            tx_id=row[2],
        )

    def _row_to_skill(self, row: sqlite3.Row) -> SkillArtifact:
        spec = json.loads(row[5])
        lineage = json.loads(row[9]) if row[9] else {}
        return SkillArtifact(
            artifact_id=row[0] or "",
            name=row[1],
            version=row[2],
            type=row[3],
            kind=row[4],
            spec=spec,
            created_at=row[6],
            updated_at=row[7] or row[6],
            idempotency_key=row[8] or "",
            lineage=lineage,
        )

    def _skill_has_tag(self, skill: SkillArtifact, tag: str) -> bool:
        if not tag:
            return False
        tags = skill.spec.get("tags") or []
        if not isinstance(tags, list):
            return False
        return tag in tags

    def _ensure_commit_allowed(
        self,
        status: str,
        existing: Optional[ValidationRecord],
        validation: Optional[ValidationRecord],
    ) -> None:
        def _is_approved(record: ValidationRecord) -> bool:
            return record.status.strip().lower() == "approved"

        if validation is not None:
            if not _is_approved(validation):
                raise ValueError("Commit requires approved validation status.")
            return
        if status != TX_VALIDATED or not existing or not _is_approved(existing):
            raise ValueError("Commit requires an approved validation record.")

    def _apply_supersede(
        self,
        conn: sqlite3.Connection,
        tx_id: str,
        entries: Iterable[MemoryEntry],
        *,
        committed_at: str,
    ) -> None:
        latest: dict[tuple[str, str], MemoryEntry] = {}
        for entry in entries:
            key = (entry.key, entry.type)
            current = latest.get(key)
            if current is None or entry.created_at >= current.created_at:
                latest[key] = entry

        for (key, entry_type), entry in latest.items():
            rows = conn.execute(
                """
                SELECT entry_id, metadata_json
                FROM memory
                WHERE key = ? AND type = ? AND (tx_id IS NULL OR tx_id != ?)
                """,
                (key, entry_type, tx_id),
            ).fetchall()

            for entry_id, metadata_json in rows:
                metadata = json.loads(metadata_json) if metadata_json else {}
                if not isinstance(metadata, dict):
                    metadata = {}
                metadata["superseded"] = True
                metadata["superseded_at"] = committed_at
                metadata["superseded_by"] = entry.entry_id
                metadata["superseded_by_tx_id"] = tx_id
                conn.execute(
                    "UPDATE memory SET metadata_json = ? WHERE entry_id = ?",
                    (json.dumps(metadata, ensure_ascii=False), entry_id),
                )
