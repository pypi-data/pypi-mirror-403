"""
Storage Backend Interface for Stardive.

This module defines the abstract storage backend interface that all storage
implementations must implement. The storage layer is responsible for:

1. **Event Storage**: Append-only event log (no updates)
2. **Artifact Reference Storage**: Metadata about artifacts
3. **RunRecord Reconstruction**: Building RunRecord from events
4. **Integrity Verification**: Hash chain validation
5. **Tombstoning**: Marking artifacts as deleted (not physical deletion)

Key Principles:
1. **Append-Only**: Events can only be added, never updated or deleted
2. **Immutable Storage**: No UPDATE or DELETE operations on events
3. **Hash Chain Integrity**: Every event links to previous event
4. **Tombstoning Not Deletion**: Artifacts marked deleted, not erased
5. **Namespace Isolation**: Runs organized by namespace (org/project/env)

Design Philosophy:
    Stardive is an audit-grade truth layer. The storage backend must guarantee:
    - No event can be modified after creation
    - No event can be deleted
    - Hash chain remains intact for tamper detection
    - All operations are traceable

    This makes Stardive storage suitable for:
    - Regulatory compliance (SOC 2, HIPAA, GDPR)
    - Legal audit trails
    - Reproducibility verification
    - Dispute resolution

For detailed specifications, see:
- docs/storage-design.md - Storage architecture
- CURRENT_JOB.md - Phase 3.1 requirements
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from pydantic import BaseModel, Field

from ..models import (
    RunRecord,
    ArtifactRef,
)
from ..models.events import Event


# ============================================================================
# Verification Models
# ============================================================================


class VerificationReport(BaseModel):
    """
    Result of RunRecord integrity verification.

    This report proves whether a RunRecord can be trusted:
    - Hash chain is valid (no tampering)
    - All artifacts exist (or are tombstoned)
    - Event sequence is valid

    Purpose:
        For audit and compliance purposes, we must be able to prove:
        - Has the RunRecord been tampered with?
        - Are all artifacts accounted for?
        - Is the event sequence valid?

        This report provides mechanically verifiable proof of integrity.

    Examples:
        Valid run:
            VerificationReport(
                run_id="run_abc123",
                verified=True,
                hash_chain_valid=True,
                all_artifacts_present=True,
                event_sequence_valid=True,
                issues=[]
            )

        Tampered run:
            VerificationReport(
                run_id="run_def456",
                verified=False,
                hash_chain_valid=False,
                all_artifacts_present=True,
                event_sequence_valid=True,
                issues=[
                    "Hash chain broken at event 3: expected sha256:abc123, got sha256:xyz789"
                ]
            )

        Missing artifacts:
            VerificationReport(
                run_id="run_ghi789",
                verified=False,
                hash_chain_valid=True,
                all_artifacts_present=False,
                event_sequence_valid=True,
                issues=[
                    "Artifact art_output_001 referenced but not found (not tombstoned)"
                ]
            )
    """

    run_id: str = Field(..., description="Run ID being verified")
    verified: bool = Field(
        ..., description="Overall verification status (True if all checks pass)"
    )

    # Individual checks
    hash_chain_valid: bool = Field(
        ..., description="Whether hash chain is intact (no tampering)"
    )
    all_artifacts_present: bool = Field(
        ..., description="Whether all referenced artifacts exist or are tombstoned"
    )
    event_sequence_valid: bool = Field(
        ..., description="Whether event sequence follows valid state machine"
    )

    # Detailed issues
    issues: List[str] = Field(
        default_factory=list,
        description="List of verification issues (empty if verified=True)",
    )

    # Metadata
    verified_at: datetime = Field(
        default_factory=datetime.utcnow, description="When verification was performed"
    )

    model_config = {"frozen": True}


# ============================================================================
# Namespace Filters
# ============================================================================


class NamespaceFilter(BaseModel):
    """
    Filter for querying runs by namespace.

    Namespaces provide hierarchical organization:
    - organization: Company or team (e.g., "acme-corp")
    - project: Project or service (e.g., "credit-analysis")
    - environment: Deployment environment (e.g., "production", "staging")

    Examples:
        All runs in organization:
            NamespaceFilter(organization="acme-corp")

        All production runs for project:
            NamespaceFilter(
                organization="acme-corp",
                project="credit-analysis",
                environment="production"
            )

        All runs for project across environments:
            NamespaceFilter(
                organization="acme-corp",
                project="credit-analysis"
            )
    """

    organization: Optional[str] = None
    project: Optional[str] = None
    environment: Optional[str] = None

    # Time range filters
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None

    # Status filters
    status: Optional[str] = None  # RunStatus value

    # Pagination
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


# ============================================================================
# Storage Backend Interface
# ============================================================================


class StorageBackend(ABC):
    """
    Abstract interface for Stardive storage backends.

    All storage implementations (SQLite, PostgreSQL, etc.) must implement
    this interface to ensure consistency and portability.

    Design Philosophy:
        The storage backend is the TRUTH KERNEL of Stardive. It must:
        - Guarantee append-only semantics (no updates to events)
        - Maintain hash chain integrity
        - Support tombstoning (not deletion)
        - Enable integrity verification
        - Provide namespace isolation

    Implementation Requirements:
        1. **Append-Only Events**: Reject UPDATE/DELETE on events table
        2. **Hash Chain**: Store and validate previous_hash references
        3. **Tombstoning**: Mark artifacts deleted, don't erase them
        4. **Transactions**: Atomic operations for consistency
        5. **Isolation**: Namespace-based multi-tenancy

    Thread Safety:
        Implementations should be thread-safe for concurrent reads.
        Writes should use appropriate locking/transactions.

    Example Implementation:
        See storage/sqlite.py for reference SQLite implementation.
    """

    # ========================================================================
    # Event Storage (Append-Only)
    # ========================================================================

    @abstractmethod
    def store_event(self, event: Event) -> None:
        """
        Store an event in the append-only event log.

        This is the core storage operation. Events form the authoritative
        audit trail and MUST be immutable once stored.

        Requirements:
            - Events can only be inserted, never updated
            - Event must include valid hash chain (event_hash, previous_hash)
            - Event run_id must exist or be created
            - Operation must be atomic (transaction)

        Args:
            event: Event to store (RunStartEvent, StepStartEvent, etc.)

        Raises:
            ValueError: If event is invalid or hash chain is broken
            RuntimeError: If storage operation fails

        Example:
            backend.store_event(
                RunStartEvent(
                    run_id="run_abc123",
                    plan_ref="run_abc123",
                    initiator=Identity(...),
                    event_hash="sha256:...",
                    previous_hash=None
                )
            )
        """
        pass

    # ========================================================================
    # RunRecord Retrieval
    # ========================================================================

    @abstractmethod
    def get_run_record(self, run_id: str) -> RunRecord:
        """
        Reconstruct RunRecord from stored events.

        This operation rebuilds the complete RunRecord by:
        1. Fetching all events for the run (ordered)
        2. Fetching all artifact references
        3. Reconstructing RunRecord from events

        Args:
            run_id: Run identifier

        Returns:
            Complete RunRecord with all events and artifacts

        Raises:
            KeyError: If run_id does not exist
            RuntimeError: If reconstruction fails

        Example:
            record = backend.get_run_record("run_abc123")
            assert record.run_id == "run_abc123"
            assert record.is_complete
            assert record.hash_chain_valid
        """
        pass

    @abstractmethod
    def list_runs(
        self, namespace: Optional[str] = None, filters: Optional[NamespaceFilter] = None
    ) -> List[RunRecord]:
        """
        List runs matching filters.

        Args:
            namespace: Namespace pattern (e.g., "acme-corp/credit-analysis/prod")
            filters: Additional filters (time range, status, pagination)

        Returns:
            List of RunRecords matching filters (ordered by started_at desc)

        Example:
            # All production runs
            runs = backend.list_runs(
                filters=NamespaceFilter(environment="production", limit=10)
            )

            # Runs in last 24 hours
            runs = backend.list_runs(
                filters=NamespaceFilter(
                    started_after=datetime.utcnow() - timedelta(days=1)
                )
            )
        """
        pass

    # ========================================================================
    # Artifact Storage
    # ========================================================================

    @abstractmethod
    def store_artifact_ref(self, artifact_ref: ArtifactRef) -> None:
        """
        Store artifact reference (metadata only).

        Note: This stores the ArtifactRef metadata, not the artifact content.
        Content storage is handled by the artifact management layer.

        Args:
            artifact_ref: Artifact reference to store

        Raises:
            ValueError: If artifact_ref is invalid
            RuntimeError: If storage operation fails

        Example:
            backend.store_artifact_ref(
                ArtifactRef(
                    artifact_id="art_abc123",
                    run_id="run_xyz789",
                    step_id="analyze",
                    artifact_type=ArtifactType.OUTPUT,
                    uri="db://artifacts/art_abc123",
                    content_hash="sha256:...",
                    content_type="application/json",
                    size_bytes=1024
                )
            )
        """
        pass

    @abstractmethod
    def get_artifact_ref(self, artifact_id: str) -> ArtifactRef:
        """
        Retrieve artifact reference by ID.

        Args:
            artifact_id: Artifact identifier

        Returns:
            ArtifactRef with metadata

        Raises:
            KeyError: If artifact_id does not exist

        Example:
            ref = backend.get_artifact_ref("art_abc123")
            assert ref.content_hash == "sha256:..."
        """
        pass

    # ========================================================================
    # Tombstoning (NOT Deletion)
    # ========================================================================

    @abstractmethod
    def tombstone_artifact(
        self, artifact_id: str, reason: str, authorized_by: str
    ) -> None:
        """
        Mark artifact as deleted (tombstoning, not physical deletion).

        For audit compliance, we NEVER physically delete artifacts.
        Instead, we mark them as tombstoned with a reason and authorization.

        This creates an audit trail of:
        - What was deleted
        - Why it was deleted
        - Who authorized the deletion
        - When it was deleted

        Args:
            artifact_id: Artifact to tombstone
            reason: Reason for deletion (e.g., "GDPR_RIGHT_TO_ERASURE", "DATA_RETENTION_POLICY")
            authorized_by: Identity who authorized deletion (e.g., "alice@company.com")

        Raises:
            KeyError: If artifact_id does not exist
            ValueError: If artifact is already tombstoned

        Example:
            backend.tombstone_artifact(
                artifact_id="art_pii_001",
                reason="GDPR_RIGHT_TO_ERASURE",
                authorized_by="privacy-officer@company.com"
            )
        """
        pass

    # ========================================================================
    # Integrity Verification
    # ========================================================================

    @abstractmethod
    def verify_run(self, run_id: str) -> VerificationReport:
        """
        Verify integrity of a run.

        This is the core audit verification operation. It checks:
        1. Hash chain integrity (no tampering)
        2. All artifacts exist (or are tombstoned)
        3. Event sequence validity (valid state machine)

        Args:
            run_id: Run to verify

        Returns:
            VerificationReport with detailed results

        Raises:
            KeyError: If run_id does not exist

        Example:
            report = backend.verify_run("run_abc123")
            if report.verified:
                print("Run is valid and untampered")
            else:
                print(f"Issues: {report.issues}")
        """
        pass


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "StorageBackend",
    "VerificationReport",
    "NamespaceFilter",
]
