from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable, Optional, Any
import json
import re
import uuid

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

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


_SCHEMA_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PostgresStorage(StorageBackend):
    def __init__(
        self,
        *,
        dsn: str,
        schema: str = "public",
        connect_timeout: int = 10,
        application_name: str = "baguette",
    ) -> None:
        if not dsn:
            raise ValueError("Postgres DSN is required.")
        if not _SCHEMA_RE.match(schema):
            raise ValueError("Postgres schema name must be alphanumeric/underscore.")
        self.dsn = dsn
        self.schema = schema
        self.connect_timeout = connect_timeout
        self.application_name = application_name

    @contextmanager
    def _connect(self) -> Iterable[psycopg.Connection]:
        conn = psycopg.connect(
            self.dsn,
            connect_timeout=self.connect_timeout,
            application_name=self.application_name,
        )
        try:
            conn.execute(
                sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema))
            )
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _qualified(self, table: str) -> sql.Composed:
        return sql.SQL("{}.{}").format(sql.Identifier(self.schema), sql.Identifier(table))

    def _ensure_index(
        self,
        conn: psycopg.Connection,
        name: str,
        ddl: sql.SQL,
    ) -> None:
        conn.execute(
            sql.SQL("CREATE INDEX IF NOT EXISTS {} ").format(sql.Identifier(name)) + ddl
        )

    def _ensure_unique_index(
        self,
        conn: psycopg.Connection,
        name: str,
        ddl: sql.SQL,
    ) -> None:
        conn.execute(
            sql.SQL("CREATE UNIQUE INDEX IF NOT EXISTS {} ").format(sql.Identifier(name)) + ddl
        )

    def _append_journal_event(
        self,
        conn: psycopg.Connection,
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
            sql.SQL(
                """
                INSERT INTO {journal}
                    (event_id, timestamp, event_type, entity_type, entity_id, tx_id, idempotency_key, payload_json, metadata_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """
            ).format(journal=self._qualified("journal")),
            (
                event_id,
                utcnow_iso(),
                event_type,
                entity_type,
                entity_id,
                tx_id,
                idempotency_key,
                Jsonb(payload),
                Jsonb(metadata or {}),
            ),
        )
        return event_id

    def initialize(self) -> None:
        conn = psycopg.connect(
            self.dsn,
            connect_timeout=self.connect_timeout,
            application_name=self.application_name,
        )
        try:
            conn.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(self.schema)
                )
            )
            conn.execute(
                sql.SQL("SET search_path TO {}").format(sql.Identifier(self.schema))
            )
            conn.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {skills} (
                        artifact_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        version TEXT NOT NULL,
                        type TEXT NOT NULL,
                        kind TEXT NOT NULL,
                        spec_json JSONB NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        idempotency_key TEXT NOT NULL,
                        lineage_json JSONB,
                        PRIMARY KEY (name, version)
                    );
                    """
                ).format(skills=self._qualified("skills"))
            )
            conn.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {decision_traces} (
                        trace_id TEXT PRIMARY KEY,
                        idempotency_key TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        skill_ref TEXT,
                        reason TEXT,
                        confidence DOUBLE PRECISION,
                        result TEXT NOT NULL,
                        metadata_json JSONB,
                        tx_id TEXT,
                        lineage_json JSONB
                    );
                    """
                ).format(decision_traces=self._qualified("decision_traces"))
            )
            conn.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {transactions} (
                        tx_id TEXT PRIMARY KEY,
                        idempotency_key TEXT NOT NULL,
                        actor TEXT,
                        reason TEXT,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        committed_at TEXT,
                        rolled_back_at TEXT,
                        validation_json JSONB,
                        metadata_json JSONB,
                        lineage_json JSONB
                    );
                    """
                ).format(transactions=self._qualified("transactions"))
            )
            conn.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {memory_staging} (
                        id BIGSERIAL PRIMARY KEY,
                        entry_id TEXT NOT NULL,
                        idempotency_key TEXT NOT NULL,
                        tx_id TEXT NOT NULL REFERENCES {transactions}(tx_id) ON DELETE CASCADE,
                        key TEXT NOT NULL,
                        value_json JSONB NOT NULL,
                        type TEXT NOT NULL,
                        source TEXT,
                        confidence DOUBLE PRECISION,
                        created_at TEXT NOT NULL,
                        metadata_json JSONB,
                        lineage_json JSONB
                    );
                    """
                ).format(
                    memory_staging=self._qualified("memory_staging"),
                    transactions=self._qualified("transactions"),
                )
            )
            conn.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {memory} (
                        id BIGSERIAL PRIMARY KEY,
                        entry_id TEXT NOT NULL,
                        idempotency_key TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value_json JSONB NOT NULL,
                        type TEXT NOT NULL,
                        source TEXT,
                        confidence DOUBLE PRECISION,
                        created_at TEXT NOT NULL,
                        metadata_json JSONB,
                        lineage_json JSONB,
                        tx_id TEXT
                    );
                    """
                ).format(memory=self._qualified("memory"))
            )
            conn.execute(
                sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {journal} (
                        seq BIGSERIAL PRIMARY KEY,
                        event_id TEXT NOT NULL UNIQUE,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        tx_id TEXT,
                        idempotency_key TEXT,
                        payload_json JSONB NOT NULL,
                        metadata_json JSONB
                    );
                    """
                ).format(journal=self._qualified("journal"))
            )

            self._ensure_unique_index(
                conn,
                "idx_skills_artifact_id",
                sql.SQL("ON {} (artifact_id)").format(self._qualified("skills")),
            )
            self._ensure_unique_index(
                conn,
                "idx_skills_idempotency_key",
                sql.SQL("ON {} (idempotency_key)").format(self._qualified("skills")),
            )
            self._ensure_unique_index(
                conn,
                "idx_transactions_idempotency_key",
                sql.SQL("ON {} (idempotency_key)").format(self._qualified("transactions")),
            )
            self._ensure_unique_index(
                conn,
                "idx_memory_staging_entry_id",
                sql.SQL("ON {} (entry_id)").format(self._qualified("memory_staging")),
            )
            self._ensure_unique_index(
                conn,
                "idx_memory_staging_idempotency",
                sql.SQL("ON {} (idempotency_key)").format(self._qualified("memory_staging")),
            )
            self._ensure_unique_index(
                conn,
                "idx_memory_entry_id",
                sql.SQL("ON {} (entry_id)").format(self._qualified("memory")),
            )
            self._ensure_unique_index(
                conn,
                "idx_memory_idempotency",
                sql.SQL("ON {} (idempotency_key)").format(self._qualified("memory")),
            )
            self._ensure_unique_index(
                conn,
                "idx_decision_traces_idempotency",
                sql.SQL("ON {} (idempotency_key)").format(
                    self._qualified("decision_traces")
                ),
            )
            self._ensure_unique_index(
                conn,
                "idx_journal_idempotency",
                sql.SQL("ON {} (event_type, idempotency_key)").format(
                    self._qualified("journal")
                ),
            )
            self._ensure_index(
                conn,
                "idx_journal_tx",
                sql.SQL("ON {} (tx_id, seq)").format(self._qualified("journal")),
            )
            self._ensure_index(
                conn,
                "idx_journal_event_type",
                sql.SQL("ON {} (event_type)").format(self._qualified("journal")),
            )
            self._ensure_index(
                conn,
                "idx_journal_entity_type",
                sql.SQL("ON {} (entity_type)").format(self._qualified("journal")),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    def upsert_skill(self, skill: SkillArtifact) -> None:
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
                sql.SQL(
                    """
                    INSERT INTO {skills}
                        (artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name, version) DO UPDATE SET
                        artifact_id = EXCLUDED.artifact_id,
                        type = EXCLUDED.type,
                        kind = EXCLUDED.kind,
                        spec_json = EXCLUDED.spec_json,
                        updated_at = EXCLUDED.updated_at,
                        idempotency_key = EXCLUDED.idempotency_key,
                        lineage_json = EXCLUDED.lineage_json
                    """
                ).format(skills=self._qualified("skills")),
                (
                    skill.artifact_id,
                    skill.name,
                    skill.version,
                    skill.type,
                    skill.kind,
                    Jsonb(skill.spec),
                    skill.created_at,
                    updated_at,
                    skill.idempotency_key,
                    Jsonb(skill.lineage),
                ),
            )

    def list_skills(self, name: Optional[str] = None) -> Iterable[SkillArtifact]:
        query = sql.SQL(
            """
            SELECT artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json
            FROM {skills}
            """
        ).format(skills=self._qualified("skills"))
        params: list[Any] = []
        if name:
            query += sql.SQL(" WHERE name = %s")
            params.append(name)
        query += sql.SQL(" ORDER BY name, version")

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_skill(row) for row in rows]

    def get_skill(self, name: str, version: Optional[str] = None) -> SkillArtifact:
        with self._connect() as conn:
            if version and version != "latest":
                if is_semver(version):
                    row = conn.execute(
                        sql.SQL(
                            """
                            SELECT artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json
                            FROM {skills} WHERE name = %s AND version = %s
                            """
                        ).format(skills=self._qualified("skills")),
                        (name, version),
                    ).fetchone()
                    if row:
                        return self._row_to_skill(row)
                    raise KeyError(f"Skill not found: {name}@{version}")

                rows = conn.execute(
                    sql.SQL(
                        """
                        SELECT artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json
                        FROM {skills} WHERE name = %s
                        """
                    ).format(skills=self._qualified("skills")),
                    (name,),
                ).fetchall()
                skills = [self._row_to_skill(row) for row in rows]
                tagged = [skill for skill in skills if self._skill_has_tag(skill, version)]
                if not tagged:
                    raise KeyError(f"Skill not found: {name}@{version}")
                tagged.sort(key=lambda skill: skill.updated_at, reverse=True)
                return tagged[0]

            row = conn.execute(
                sql.SQL(
                    """
                    SELECT artifact_id, name, version, type, kind, spec_json, created_at, updated_at, idempotency_key, lineage_json
                    FROM {skills} WHERE name = %s
                    ORDER BY updated_at DESC LIMIT 1
                    """
                ).format(skills=self._qualified("skills")),
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
                    sql.SQL("SELECT tx_id FROM {transactions} WHERE idempotency_key = %s").format(
                        transactions=self._qualified("transactions")
                    ),
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
                sql.SQL(
                    """
                    INSERT INTO {transactions}
                        (tx_id, idempotency_key, actor, reason, status, created_at, updated_at, metadata_json, lineage_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                ).format(transactions=self._qualified("transactions")),
                (
                    record.tx_id,
                    record.idempotency_key,
                    record.actor,
                    record.reason,
                    record.status,
                    record.created_at,
                    record.updated_at,
                    Jsonb(record.metadata),
                    Jsonb(record.lineage),
                ),
            )
        return record.tx_id

    def get_transaction(self, tx_id: str) -> TransactionRecord:
        with self._connect() as conn:
            row = conn.execute(
                sql.SQL(
                    """
                    SELECT tx_id, idempotency_key, actor, reason, status, created_at, updated_at,
                           committed_at, rolled_back_at, validation_json, metadata_json, lineage_json
                    FROM {transactions} WHERE tx_id = %s
                    """
                ).format(transactions=self._qualified("transactions")),
                (tx_id,),
            ).fetchone()

        if not row:
            raise KeyError(f"Transaction not found: {tx_id}")

        return self._row_to_transaction(row)

    def stage_memory(self, tx_id: str, entry: MemoryEntry) -> None:
        with self._connect() as conn:
            tx_row = conn.execute(
                sql.SQL("SELECT status FROM {transactions} WHERE tx_id = %s").format(
                    transactions=self._qualified("transactions")
                ),
                (tx_id,),
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
                sql.SQL(
                    """
                    INSERT INTO {memory_staging}
                        (entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at, metadata_json, lineage_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """
                ).format(memory_staging=self._qualified("memory_staging")),
                (
                    entry.entry_id,
                    entry.idempotency_key,
                    tx_id,
                    entry.key,
                    Jsonb(entry.value),
                    entry.type,
                    entry.source,
                    entry.confidence,
                    entry.created_at,
                    Jsonb(entry.metadata),
                    Jsonb(entry.lineage),
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
        filters = [sql.SQL("tx_id = %s")]
        params: list[Any] = [tx_id]
        if key:
            filters.append(sql.SQL("key = %s"))
            params.append(key)
        if entry_type:
            filters.append(sql.SQL("type = %s"))
            params.append(entry_type)
        if source:
            filters.append(sql.SQL("source = %s"))
            params.append(source)
        if min_confidence is not None:
            filters.append(sql.SQL("confidence >= %s"))
            params.append(min_confidence)
        if max_confidence is not None:
            filters.append(sql.SQL("confidence <= %s"))
            params.append(max_confidence)
        where_clause = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(filters)
        query = (
            sql.SQL(
                """
                SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                       metadata_json, lineage_json
                FROM {memory_staging}
                """
            ).format(memory_staging=self._qualified("memory_staging"))
            + where_clause
            + sql.SQL(" ORDER BY id ASC LIMIT %s")
        )
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
        query = sql.SQL(
            """
            SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                   metadata_json, lineage_json
            FROM {memory}
            """
        ).format(memory=self._qualified("memory"))
        params: list[Any] = []
        filters = []
        if key:
            filters.append(sql.SQL("key = %s"))
            params.append(key)
        if entry_type:
            filters.append(sql.SQL("type = %s"))
            params.append(entry_type)
        if source:
            filters.append(sql.SQL("source = %s"))
            params.append(source)
        if created_after:
            filters.append(sql.SQL("created_at >= %s"))
            params.append(created_after)
        if created_before:
            filters.append(sql.SQL("created_at <= %s"))
            params.append(created_before)
        if min_confidence is not None:
            filters.append(sql.SQL("confidence >= %s"))
            params.append(min_confidence)
        if max_confidence is not None:
            filters.append(sql.SQL("confidence <= %s"))
            params.append(max_confidence)
        if filters:
            query += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(filters)
        query += sql.SQL(" ORDER BY created_at DESC LIMIT %s")
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_memory(row) for row in rows]

    def get_memory_entry(self, entry_id: str) -> MemoryEntry:
        with self._connect() as conn:
            row = conn.execute(
                sql.SQL(
                    """
                    SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                           metadata_json, lineage_json
                    FROM {memory}
                    WHERE entry_id = %s
                    """
                ).format(memory=self._qualified("memory")),
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
                sql.SQL(
                    """
                    SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                           metadata_json, lineage_json
                    FROM {memory}
                    WHERE entry_id = %s
                    """
                ).format(memory=self._qualified("memory")),
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
                sql.SQL(
                    """
                    UPDATE {memory}
                    SET value_json = %s, metadata_json = %s
                    WHERE entry_id = %s
                    """
                ).format(memory=self._qualified("memory")),
                (Jsonb(redacted_value), Jsonb(merged_metadata), entry_id),
            )

        return self.get_memory_entry(entry_id)
    def validate_transaction(self, tx_id: str, validation: ValidationRecord) -> None:
        validated_at = utcnow_iso()
        with self._connect() as conn:
            tx_row = conn.execute(
                sql.SQL("SELECT status FROM {transactions} WHERE tx_id = %s").format(
                    transactions=self._qualified("transactions")
                ),
                (tx_id,),
            ).fetchone()
            if not tx_row:
                raise KeyError(f"Transaction not found: {tx_id}")
            if tx_row[0] in (TX_COMMITTED, TX_ROLLED_BACK):
                raise ValueError(f"Cannot validate transaction in status {tx_row[0]}")

            validation_payload = validation.to_dict()
            self._append_journal_event(
                conn,
                event_type="transaction.validate",
                entity_type="transaction",
                entity_id=tx_id,
                tx_id=tx_id,
                idempotency_key=validation.idempotency_key,
                payload=validation_payload,
            )
            conn.execute(
                sql.SQL(
                    """
                    UPDATE {transactions}
                    SET status = %s, updated_at = %s, validation_json = %s
                    WHERE tx_id = %s
                    """
                ).format(transactions=self._qualified("transactions")),
                (TX_VALIDATED, validated_at, Jsonb(validation_payload), tx_id),
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
                sql.SQL("SELECT status, validation_json FROM {transactions} WHERE tx_id = %s").format(
                    transactions=self._qualified("transactions")
                ),
                (tx_id,),
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
                sql.SQL(
                    """
                    SELECT entry_id, idempotency_key, tx_id, key, value_json, type, source, confidence, created_at,
                           metadata_json, lineage_json
                    FROM {memory_staging} WHERE tx_id = %s
                    """
                ).format(memory_staging=self._qualified("memory_staging")),
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
                sql.SQL(
                    """
                    INSERT INTO {memory}
                        (entry_id, idempotency_key, key, value_json, type, source, confidence, created_at, metadata_json, lineage_json, tx_id)
                    SELECT entry_id, idempotency_key, key, value_json, type, source, confidence, created_at, metadata_json, lineage_json, tx_id
                    FROM {memory_staging} WHERE tx_id = %s
                    ON CONFLICT DO NOTHING
                    """
                ).format(
                    memory=self._qualified("memory"),
                    memory_staging=self._qualified("memory_staging"),
                ),
                (tx_id,),
            )
            if supersede and staged_entries:
                self._apply_supersede(conn, tx_id, staged_entries, committed_at=committed_at)
            conn.execute(
                sql.SQL("DELETE FROM {memory_staging} WHERE tx_id = %s").format(
                    memory_staging=self._qualified("memory_staging")
                ),
                (tx_id,),
            )
            conn.execute(
                sql.SQL(
                    """
                    UPDATE {transactions}
                    SET status = %s, committed_at = %s, updated_at = %s, validation_json = COALESCE(%s, validation_json)
                    WHERE tx_id = %s
                    """
                ).format(transactions=self._qualified("transactions")),
                (
                    TX_COMMITTED,
                    committed_at,
                    committed_at,
                    Jsonb(validation.to_dict()) if validation else None,
                    tx_id,
                ),
            )

    def rollback_transaction(self, tx_id: str, reason: str) -> None:
        rolled_back_at = utcnow_iso()
        with self._connect() as conn:
            tx_row = conn.execute(
                sql.SQL("SELECT status, metadata_json FROM {transactions} WHERE tx_id = %s").format(
                    transactions=self._qualified("transactions")
                ),
                (tx_id,),
            ).fetchone()
            if not tx_row:
                raise KeyError(f"Transaction not found: {tx_id}")
            if tx_row[0] == TX_ROLLED_BACK:
                return
            if tx_row[0] == TX_COMMITTED:
                raise ValueError(f"Cannot rollback transaction in status {tx_row[0]}")

            metadata = self._ensure_dict(tx_row[1])
            metadata["rollback_reason"] = reason

            self._append_journal_event(
                conn,
                event_type="transaction.rollback",
                entity_type="transaction",
                entity_id=tx_id,
                tx_id=tx_id,
                idempotency_key=f"{tx_id}:rollback",
                payload={"tx_id": tx_id, "reason": reason, "rolled_back_at": rolled_back_at},
            )
            conn.execute(
                sql.SQL("DELETE FROM {memory_staging} WHERE tx_id = %s").format(
                    memory_staging=self._qualified("memory_staging")
                ),
                (tx_id,),
            )
            conn.execute(
                sql.SQL(
                    """
                    UPDATE {transactions}
                    SET status = %s, rolled_back_at = %s, updated_at = %s, metadata_json = %s
                    WHERE tx_id = %s
                    """
                ).format(transactions=self._qualified("transactions")),
                (
                    TX_ROLLED_BACK,
                    rolled_back_at,
                    rolled_back_at,
                    Jsonb(metadata),
                    tx_id,
                ),
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
                sql.SQL(
                    """
                    INSERT INTO {decision_traces}
                        (trace_id, idempotency_key, timestamp, decision, skill_ref, reason, confidence, result, metadata_json, tx_id, lineage_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """
                ).format(decision_traces=self._qualified("decision_traces")),
                (
                    trace.trace_id,
                    trace.idempotency_key,
                    trace.timestamp,
                    trace.decision,
                    trace.skill_ref,
                    trace.reason,
                    trace.confidence,
                    trace.result,
                    Jsonb(trace.metadata),
                    trace.tx_id,
                    Jsonb(trace.lineage),
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
        params: list[Any] = []
        if tx_id:
            filters.append(sql.SQL("tx_id = %s"))
            params.append(tx_id)
        if decision:
            filters.append(sql.SQL("decision = %s"))
            params.append(decision)
        if skill_ref:
            filters.append(sql.SQL("skill_ref = %s"))
            params.append(skill_ref)
        if result:
            filters.append(sql.SQL("result = %s"))
            params.append(result)
        if created_after:
            filters.append(sql.SQL("timestamp >= %s"))
            params.append(created_after)
        if created_before:
            filters.append(sql.SQL("timestamp <= %s"))
            params.append(created_before)
        where_clause = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(filters) if filters else sql.SQL("")
        query = (
            sql.SQL(
                """
                SELECT trace_id, idempotency_key, timestamp, decision, skill_ref, reason, confidence, result, metadata_json, tx_id, lineage_json
                FROM {decision_traces}
                """
            ).format(decision_traces=self._qualified("decision_traces"))
            + where_clause
            + sql.SQL(" ORDER BY timestamp DESC")
        )
        if correlation_id is None:
            query += sql.SQL(" LIMIT %s")
            params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        traces = []
        for row in rows:
            metadata = self._ensure_dict(row[8])
            lineage = self._ensure_dict(row[10])
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
        params: list[Any] = []
        if tx_id:
            filters.append(sql.SQL("tx_id = %s"))
            params.append(tx_id)
        if event_type:
            filters.append(sql.SQL("event_type = %s"))
            params.append(event_type)
        if entity_type:
            filters.append(sql.SQL("entity_type = %s"))
            params.append(entity_type)
        if entity_id:
            filters.append(sql.SQL("entity_id = %s"))
            params.append(entity_id)

        where_clause = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(filters) if filters else sql.SQL("")
        query = (
            sql.SQL(
                """
                SELECT seq, event_id, timestamp, event_type, entity_type, entity_id, tx_id, idempotency_key,
                       payload_json, metadata_json
                FROM {journal}
                """
            ).format(journal=self._qualified("journal"))
            + where_clause
            + sql.SQL(" ORDER BY seq DESC LIMIT %s")
        )
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        events = []
        for row in rows:
            payload = self._ensure_dict(row[8])
            metadata = self._ensure_dict(row[9])
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
    def _ensure_dict(self, payload: Any) -> dict:
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            data = json.loads(payload)
            if isinstance(data, dict):
                return data
            return {"value": data}
        return {"value": payload}

    def _parse_validation(self, raw: Any) -> Optional[ValidationRecord]:
        if raw is None:
            return None
        data = raw if isinstance(raw, dict) else json.loads(raw)
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

    def _row_to_transaction(self, row: tuple[Any, ...]) -> TransactionRecord:
        validation = self._parse_validation(row[9]) if row[9] else None
        metadata = self._ensure_dict(row[10])
        lineage = self._ensure_dict(row[11])
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

    def _row_to_memory(self, row: tuple[Any, ...]) -> MemoryEntry:
        value = row[4]
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
        metadata = self._ensure_dict(row[9])
        lineage = self._ensure_dict(row[10])
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

    def _row_to_skill(self, row: tuple[Any, ...]) -> SkillArtifact:
        spec = row[5]
        if isinstance(spec, str):
            spec = json.loads(spec)
        lineage = self._ensure_dict(row[9])
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
        conn,
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
                sql.SQL(
                    """
                    SELECT entry_id, metadata_json
                    FROM {memory}
                    WHERE key = %s AND type = %s AND (tx_id IS NULL OR tx_id != %s)
                    """
                ).format(memory=self._qualified("memory")),
                (key, entry_type, tx_id),
            ).fetchall()

            for entry_id, metadata_json in rows:
                metadata = self._ensure_dict(metadata_json)
                metadata["superseded"] = True
                metadata["superseded_at"] = committed_at
                metadata["superseded_by"] = entry.entry_id
                metadata["superseded_by_tx_id"] = tx_id
                conn.execute(
                    sql.SQL("UPDATE {memory} SET metadata_json = %s WHERE entry_id = %s").format(
                        memory=self._qualified("memory")
                    ),
                    (Jsonb(metadata), entry_id),
                )
