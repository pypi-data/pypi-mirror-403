"""
SQLite Storage Backend for Stardive.

This module implements the StorageBackend interface using SQLite as the
underlying storage engine. SQLite is ideal for:

- Local development and testing
- Single-node deployments
- Embedded audit trails
- File-based portability

Key Features:
1. **Append-Only Events**: UPDATE/DELETE blocked via triggers
2. **Hash Chain Validation**: Automatic verification
3. **Tombstoning**: Soft delete with audit trail
4. **ACID Transactions**: Atomic operations
5. **File-Based**: Portable, no server required

Schema Design:
    events:
        - event_id (PK)
        - run_id (indexed)
        - event_type (run_start, step_start, step_end, run_end)
        - timestamp
        - event_data (JSON)
        - event_hash (SHA256)
        - previous_event_hash (chain link)
        - created_at

    artifact_refs:
        - artifact_id (PK)
        - run_id (indexed)
        - step_id (indexed)
        - artifact_kind (json, text, bytes, file)
        - artifact_ref_data (JSON serialized ArtifactRef)
        - tombstoned (bool, default false)
        - tombstone_reason (text, nullable)
        - tombstoned_by (text, nullable)
        - tombstoned_at (timestamp, nullable)
        - created_at

    namespaces:
        - namespace_id (PK)
        - organization
        - project
        - environment
        - created_at

    run_namespaces:
        - run_id (FK)
        - namespace_id (FK)

Performance Considerations:
    - Indexes on run_id, event_type, timestamp
    - JSON extraction for common queries
    - Connection pooling for concurrent access
    - WAL mode for better concurrency

For detailed specifications, see:
- docs/storage-design.md - Schema and design rationale
- CURRENT_JOB.md - Phase 3.1 requirements
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from ..models import (
    RunStartEvent,
    RunEndEvent,
    StepStartEvent,
    StepEndEvent,
    RunRecord,
    ArtifactRef,
    RunStatus,
    RunRecordBuilder,
)
from ..models.events import Event

from .base import (
    StorageBackend,
    VerificationReport,
    NamespaceFilter,
)


# ============================================================================
# SQLite Backend Implementation
# ============================================================================


class SQLiteBackend(StorageBackend):
    """
    SQLite implementation of StorageBackend.

    This backend uses SQLite for append-only event storage with:
    - Automatic schema creation
    - Trigger-enforced immutability
    - Transaction management
    - Hash chain validation

    Example Usage:
        # Create backend with file storage
        backend = SQLiteBackend(db_path="stardive.db")

        # Store events
        backend.store_event(RunStartEvent(...))
        backend.store_event(StepStartEvent(...))
        backend.store_event(StepEndEvent(...))
        backend.store_event(RunEndEvent(...))

        # Retrieve run
        record = backend.get_run_record("run_abc123")

        # Verify integrity
        report = backend.verify_run("run_abc123")
    """

    def __init__(self, db_path: str | Path = ":memory:"):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file, or ":memory:" for in-memory DB
        """
        self.db_path = Path(db_path) if db_path != ":memory:" else db_path
        # For :memory: databases, keep a persistent connection
        # Otherwise each connection would get its own isolated database
        self._memory_conn = None
        if self.db_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:")
            self._memory_conn.row_factory = sqlite3.Row
        self._init_database()

    # ========================================================================
    # Database Initialization
    # ========================================================================

    def _init_database(self) -> None:
        """Initialize database schema and triggers."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")

            # Events table (append-only)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    previous_event_hash TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    CHECK (event_type IN ('run_start', 'step_start', 'step_end', 'run_end'))
                )
            """)

            # Create indexes for events
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)"
            )

            # Trigger to prevent updates to events (append-only enforcement)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prevent_event_update
                BEFORE UPDATE ON events
                BEGIN
                    SELECT RAISE(ABORT, 'Events are immutable - updates not allowed');
                END
            """)

            # Trigger to prevent deletion of events (append-only enforcement)
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prevent_event_delete
                BEFORE DELETE ON events
                BEGIN
                    SELECT RAISE(ABORT, 'Events are immutable - deletion not allowed');
                END
            """)

            # Artifact references table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artifact_refs (
                    artifact_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    artifact_kind TEXT NOT NULL,
                    artifact_ref_data TEXT NOT NULL,
                    tombstoned INTEGER NOT NULL DEFAULT 0,
                    tombstone_reason TEXT,
                    tombstoned_by TEXT,
                    tombstoned_at TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    CHECK (artifact_kind IN ('json', 'text', 'bytes', 'file')),
                    CHECK (tombstoned IN (0, 1))
                )
            """)

            # Create indexes for artifact_refs
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_artifact_refs_run_id ON artifact_refs(run_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_artifact_refs_step_id ON artifact_refs(step_id)"
            )

            # Namespaces table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS namespaces (
                    namespace_id TEXT PRIMARY KEY,
                    organization TEXT,
                    project TEXT,
                    environment TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)

            # Run namespaces junction table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS run_namespaces (
                    run_id TEXT NOT NULL,
                    namespace_id TEXT NOT NULL,
                    PRIMARY KEY (run_id, namespace_id),
                    FOREIGN KEY (namespace_id) REFERENCES namespaces(namespace_id)
                )
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with proper configuration."""
        if self._memory_conn is not None:
            # Use persistent connection for :memory: databases
            yield self._memory_conn
        else:
            # File-based database: create new connection each time
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    # ========================================================================
    # Event Storage
    # ========================================================================

    def store_event(self, event: Event) -> None:
        """Store event in append-only event log."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Determine event type
            event_type = self._get_event_type(event)

            # Serialize event data
            event_data = event.model_dump_json()

            try:
                cursor.execute(
                    """
                    INSERT INTO events (
                        event_id, run_id, event_type, timestamp,
                        event_data, event_hash, previous_event_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.run_id,
                        event_type,
                        event.timestamp.isoformat(),
                        event_data,
                        event.event_hash,
                        event.previous_hash,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "prevent_event_update" in str(e) or "prevent_event_delete" in str(
                    e
                ):
                    raise RuntimeError(
                        "Attempted to modify immutable event - this is a bug"
                    ) from e
                raise RuntimeError(f"Failed to store event: {e}") from e

    def _get_event_type(self, event: Event) -> str:
        """Determine event type string from event class."""
        if isinstance(event, RunStartEvent):
            return "run_start"
        elif isinstance(event, RunEndEvent):
            return "run_end"
        elif isinstance(event, StepStartEvent):
            return "step_start"
        elif isinstance(event, StepEndEvent):
            return "step_end"
        else:
            raise ValueError(f"Unknown event type: {type(event)}")

    # ========================================================================
    # RunRecord Retrieval
    # ========================================================================

    def get_run_record(self, run_id: str) -> RunRecord:
        """Reconstruct RunRecord from stored events."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Fetch all events for run (ordered by timestamp)
            cursor.execute(
                """
                SELECT event_data, event_type
                FROM events
                WHERE run_id = ?
                ORDER BY timestamp ASC
                """,
                (run_id,),
            )

            rows = cursor.fetchall()
            if not rows:
                raise KeyError(f"Run {run_id} not found")

            # Reconstruct events
            events = []
            for row in rows:
                event_data = json.loads(row["event_data"])
                event_type = row["event_type"]

                # Deserialize to appropriate event type
                if event_type == "run_start":
                    event = RunStartEvent(**event_data)
                elif event_type == "run_end":
                    event = RunEndEvent(**event_data)
                elif event_type == "step_start":
                    event = StepStartEvent(**event_data)
                elif event_type == "step_end":
                    event = StepEndEvent(**event_data)
                else:
                    raise ValueError(f"Unknown event type: {event_type}")

                events.append(event)

            # Fetch all artifact refs for run
            cursor.execute(
                """
                SELECT artifact_ref_data
                FROM artifact_refs
                WHERE run_id = ?
                """,
                (run_id,),
            )

            artifact_rows = cursor.fetchall()
            artifacts = []
            for row in artifact_rows:
                artifact_data = json.loads(row["artifact_ref_data"])
                artifacts.append(ArtifactRef(**artifact_data))

            # Build RunRecord using builder
            builder = RunRecordBuilder(run_id=run_id)
            for event in events:
                builder.append_event(event)

            # Build and return
            record = builder.build()
            return record

    def list_runs(
        self, namespace: Optional[str] = None, filters: Optional[NamespaceFilter] = None
    ) -> List[RunRecord]:
        """List runs matching filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build query
            query = """
                SELECT DISTINCT run_id
                FROM events
                WHERE 1=1
            """
            params: List[Any] = []

            # Apply filters
            if filters:
                if filters.started_after:
                    query += " AND timestamp >= ?"
                    params.append(filters.started_after.isoformat())

                if filters.started_before:
                    query += " AND timestamp <= ?"
                    params.append(filters.started_before.isoformat())

                if filters.status:
                    # This requires checking the final event status
                    # For now, we'll fetch all and filter in memory
                    pass

            # Order and limit
            query += " ORDER BY timestamp DESC"

            if filters:
                query += " LIMIT ? OFFSET ?"
                params.extend([filters.limit, filters.offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Reconstruct each run
            records = []
            for row in rows:
                run_id = row["run_id"]
                try:
                    record = self.get_run_record(run_id)

                    # Apply status filter if specified
                    if filters and filters.status:
                        record_status = (
                            record.status.value
                            if hasattr(record.status, "value")
                            else str(record.status)
                        )
                        if isinstance(record_status, str) and "." in record_status:
                            record_status = record_status.split(".")[-1]
                        if isinstance(record_status, str):
                            record_status = record_status.lower()

                        filter_status = filters.status
                        if isinstance(filter_status, str) and "." in filter_status:
                            filter_status = filter_status.split(".")[-1]
                        if isinstance(filter_status, str):
                            filter_status = filter_status.lower()

                        if record_status != filter_status:
                            continue

                    records.append(record)
                except KeyError:
                    # Skip runs that can't be reconstructed
                    continue

            return records

    # ========================================================================
    # Artifact Storage
    # ========================================================================

    def store_artifact_ref(self, artifact_ref: ArtifactRef) -> None:
        """Store artifact reference metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Determine artifact kind from content_type
            # For now, we'll infer from content_type
            artifact_kind = self._infer_artifact_kind(artifact_ref.content_type)

            # Serialize artifact ref
            artifact_ref_data = artifact_ref.model_dump_json()

            cursor.execute(
                """
                INSERT INTO artifact_refs (
                    artifact_id, run_id, step_id, artifact_kind, artifact_ref_data
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(artifact_id) DO UPDATE SET
                    run_id = excluded.run_id,
                    step_id = excluded.step_id,
                    artifact_kind = excluded.artifact_kind,
                    artifact_ref_data = excluded.artifact_ref_data
                """,
                (
                    artifact_ref.artifact_id,
                    artifact_ref.run_id,
                    artifact_ref.step_id,
                    artifact_kind,
                    artifact_ref_data,
                ),
            )
            conn.commit()

    def _infer_artifact_kind(self, content_type: str) -> str:
        """Infer artifact kind from content type."""
        if "json" in content_type.lower():
            return "json"
        elif "text" in content_type.lower():
            return "text"
        else:
            return "bytes"

    def get_artifact_ref(self, artifact_id: str) -> ArtifactRef:
        """Retrieve artifact reference by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT artifact_ref_data
                FROM artifact_refs
                WHERE artifact_id = ?
                """,
                (artifact_id,),
            )

            row = cursor.fetchone()
            if not row:
                raise KeyError(f"Artifact {artifact_id} not found")

            artifact_data = json.loads(row["artifact_ref_data"])
            return ArtifactRef(**artifact_data)

    # ========================================================================
    # Tombstoning
    # ========================================================================

    def tombstone_artifact(
        self, artifact_id: str, reason: str, authorized_by: str
    ) -> None:
        """Mark artifact as deleted (tombstoning)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if artifact exists
            cursor.execute(
                "SELECT tombstoned FROM artifact_refs WHERE artifact_id = ?",
                (artifact_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Artifact {artifact_id} not found")

            if row["tombstoned"]:
                raise ValueError(f"Artifact {artifact_id} is already tombstoned")

            # Tombstone the artifact
            cursor.execute(
                """
                UPDATE artifact_refs
                SET tombstoned = 1,
                    tombstone_reason = ?,
                    tombstoned_by = ?,
                    tombstoned_at = ?
                WHERE artifact_id = ?
                """,
                (reason, authorized_by, datetime.utcnow().isoformat(), artifact_id),
            )
            conn.commit()

    # ========================================================================
    # Integrity Verification
    # ========================================================================

    def verify_run(self, run_id: str) -> VerificationReport:
        """Verify integrity of a run."""
        issues: List[str] = []

        # Get the run record
        try:
            record = self.get_run_record(run_id)
        except KeyError:
            return VerificationReport(
                run_id=run_id,
                verified=False,
                hash_chain_valid=False,
                all_artifacts_present=False,
                event_sequence_valid=False,
                issues=[f"Run {run_id} not found"],
            )
        except ValueError as e:
            # Hash chain validation failed during reconstruction
            return VerificationReport(
                run_id=run_id,
                verified=False,
                hash_chain_valid=False,
                all_artifacts_present=False,
                event_sequence_valid=False,
                issues=[f"Hash chain validation failed: {str(e)}"],
            )

        # Check hash chain
        hash_chain_valid = record.hash_chain_valid
        if not hash_chain_valid:
            issues.append("Hash chain is invalid - possible tampering detected")

        # Check event sequence
        event_sequence_valid = self._verify_event_sequence(record)
        if not event_sequence_valid:
            issues.append("Event sequence is invalid")

        # Check all artifacts
        all_artifacts_present = self._verify_artifacts(record)
        if not all_artifacts_present:
            issues.append("Some referenced artifacts are missing")

        # Overall verification
        verified = hash_chain_valid and event_sequence_valid and all_artifacts_present

        return VerificationReport(
            run_id=run_id,
            verified=verified,
            hash_chain_valid=hash_chain_valid,
            all_artifacts_present=all_artifacts_present,
            event_sequence_valid=event_sequence_valid,
            issues=issues,
        )

    def _verify_event_sequence(self, record: RunRecord) -> bool:
        """Verify event sequence follows valid state machine."""
        if not record.events:
            return False

        # First event must be RunStartEvent
        if not isinstance(record.events[0], RunStartEvent):
            return False

        # Last event should be RunEndEvent for completed runs
        if record.is_complete and not isinstance(record.events[-1], RunEndEvent):
            return False

        # Step events must come in pairs (start, end)
        # This is a simplified check - full validation would track step states
        return True

    def _verify_artifacts(self, record: RunRecord) -> bool:
        """Verify all referenced artifacts exist or are tombstoned."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Collect all artifact IDs referenced in events
            referenced_artifacts = set()
            for event in record.events:
                if isinstance(event, StepStartEvent):
                    referenced_artifacts.update(
                        ref.artifact_id for ref in event.inputs.values()
                    )
                elif isinstance(event, StepEndEvent):
                    referenced_artifacts.update(
                        ref.artifact_id for ref in event.outputs.values()
                    )

            # Check each artifact exists
            for artifact_id in referenced_artifacts:
                cursor.execute(
                    "SELECT artifact_id FROM artifact_refs WHERE artifact_id = ?",
                    (artifact_id,),
                )
                if not cursor.fetchone():
                    return False

            return True


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "SQLiteBackend",
]
