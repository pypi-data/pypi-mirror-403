from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from ..audit.journal import JournalEvent
from ..audit.traces import DecisionTrace
from ..memory.transactions import MemoryEntry, TransactionRecord, ValidationRecord
from ..skills.artifacts import SkillArtifact


class StorageBackend(ABC):
    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert_skill(self, skill: SkillArtifact) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_skills(self, name: Optional[str] = None) -> Iterable[SkillArtifact]:
        raise NotImplementedError

    @abstractmethod
    def get_skill(self, name: str, version: Optional[str] = None) -> SkillArtifact:
        raise NotImplementedError

    @abstractmethod
    def begin_transaction(
        self,
        actor: str,
        reason: str,
        metadata: Optional[dict] = None,
        *,
        idempotency_key: Optional[str] = None,
        lineage: Optional[dict] = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_transaction(self, tx_id: str) -> TransactionRecord:
        raise NotImplementedError

    @abstractmethod
    def stage_memory(self, tx_id: str, entry: MemoryEntry) -> None:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def get_memory_entry(self, entry_id: str) -> MemoryEntry:
        raise NotImplementedError

    @abstractmethod
    def redact_memory(
        self,
        entry_id: str,
        *,
        redacted_value: object,
        metadata: dict,
    ) -> MemoryEntry:
        raise NotImplementedError

    @abstractmethod
    def validate_transaction(self, tx_id: str, validation: ValidationRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def commit_transaction(
        self,
        tx_id: str,
        validation: Optional[ValidationRecord] = None,
        *,
        supersede: bool = False,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def rollback_transaction(self, tx_id: str, reason: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def record_trace(self, trace: DecisionTrace) -> None:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def list_journal(
        self,
        limit: int = 100,
        tx_id: Optional[str] = None,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
    ) -> Iterable[JournalEvent]:
        raise NotImplementedError
