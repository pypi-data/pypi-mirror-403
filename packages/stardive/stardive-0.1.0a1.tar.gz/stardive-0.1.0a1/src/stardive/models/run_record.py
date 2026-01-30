"""
RunRecord - The Authoritative Execution Truth.

This module defines RunRecord, the canonical representation of what actually
happened during workflow execution. It is the SOURCE OF TRUTH for audit purposes.

RunRecord vs. RunPlan:
- **RunPlan**: Execution intent (what *should* happen)
- **RunRecord**: Execution truth (what *actually* happened)

Key Principles:
1. **Append-Only**: Events can only be added, never modified or deleted
2. **Immutable**: Once created, RunRecord cannot be changed (frozen=True)
3. **Hash-Chained**: Events form tamper-evident blockchain-style chain
4. **Authoritative**: This is legal/regulatory audit evidence
5. **Event-Based**: Truth is derived from ordered sequence of events

Truth Model - Authoritative vs. Non-Authoritative:

    AUTHORITATIVE (Audit Evidence):
    - events: All execution events with hash chain
    - artifacts: Artifact references with content hashes
    - identities: Who did what, when (with attestations)
    - event_hashes: Hash chain for tamper detection

    NON-AUTHORITATIVE (Supporting Data):
    - telemetry: Performance metrics (can be regenerated)
    - narrative: LLM-generated summary (derived, not original)
    - logs: Console output (helpful but not legally binding)

    Only authoritative data can be used for:
    - Legal/regulatory compliance
    - Audit trail evidence
    - Dispute resolution
    - Reproducibility verification

Lifecycle:
    1. Execution starts → RunRecord created with RunStartEvent
    2. Steps execute → Events appended (StepStart, StepEnd)
    3. Execution completes → Finalized with RunEndEvent
    4. RunRecord frozen → Stored in append-only storage
    5. Never modified → Immutable audit trail

Storage Model:
    RunRecord is stored in append-only storage (Phase 5):
    - SQLite: Append-only event table (no UPDATE statements)
    - PostgreSQL: Event sourcing pattern (INSERT only)
    - Events never deleted, only new events added
    - Compliance: Meets SOC 2, GDPR, HIPAA requirements

For detailed specifications, see:
- docs/canonical-ir.md - RunRecord specification
- docs/RUNRECORD_DESIGN.md - Architecture and rationale (to be created)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field

from .enums import RunStatus
from .events import Event, RunEndEvent, RunStartEvent, StepEndEvent, StepStartEvent
from .artifacts import ArtifactRef
from .identity import Identity


# ============================================================================
# RunRecord (Execution Truth)
# ============================================================================


class RunRecord(BaseModel):
    """
    Authoritative audit trail for a run.

    RunRecord is the SOURCE OF TRUTH for what happened during execution.
    Only the kernel can append events to this record. It is immutable once
    created and stored in append-only storage.

    Purpose:
        RunRecord provides a complete, tamper-evident audit trail that:
        - Proves what steps were executed
        - Shows inputs and outputs for each step
        - Records who performed each action
        - Captures exact execution timeline
        - Enables reproducibility and debugging
        - Meets legal/regulatory requirements

    Architecture:
        RunRecord is built around an ordered sequence of events:

        1. RunStartEvent (who, what plan, when)
        2. StepStartEvent (step X starts, inputs)
        3. StepEndEvent (step X ends, outputs, status)
        4. StepStartEvent (step Y starts, inputs)
        5. StepEndEvent (step Y ends, outputs, status)
        ...
        N. RunEndEvent (final status, outputs, duration)

    Hash Chain:
        Events are chained for tamper detection:

        Event 1: hash₁ = SHA256(event₁_data + None)
        Event 2: hash₂ = SHA256(event₂_data + hash₁)
        Event 3: hash₃ = SHA256(event₃_data + hash₂)

        record_hash = hash_N (hash of latest event)

        If any event is modified, the chain breaks, making tampering
        immediately detectable.

    Verification:
        To verify integrity:
        1. Walk through events sequentially
        2. Check each event.previous_hash == previous_event.event_hash
        3. Recompute each event.event_hash and verify
        4. If any hash doesn't match → tampering detected

    Truth Model:
        Only certain fields are authoritative (legally binding):
        - ✅ events: Core audit trail
        - ✅ artifacts: Content hashes prove data integrity
        - ✅ identities: Who did what (attestations)
        - ✅ event_hashes: Tamper detection
        - ❌ telemetry: Helpful but not audit evidence
        - ❌ narrative: LLM-generated, not authoritative

    Lifecycle:
        Created:    RunRecord with RunStartEvent
        Running:    Events appended as execution progresses
        Completed:  Finalized with RunEndEvent
        Stored:     Written to append-only storage
        Immutable:  Never modified after storage

    Builder Pattern:
        RunRecord is immutable (frozen), so it cannot be modified after creation.
        Use RunRecordBuilder to construct RunRecord incrementally during execution.

        See: builders.py for RunRecordBuilder implementation

    Examples:
        Minimal completed run:
            RunRecord(
                run_id="run_abc123",
                record_hash="sha256:xyz789...",  # Hash of last event
                events=[
                    RunStartEvent(
                        run_id="run_abc123",
                        plan_ref="run_abc123",
                        initiator=Identity(...),
                        event_hash="sha256:evt1...",
                        previous_hash=None
                    ),
                    StepStartEvent(
                        run_id="run_abc123",
                        step_id="analyze",
                        inputs={"data": ArtifactRef(...)},
                        event_hash="sha256:evt2...",
                        previous_hash="sha256:evt1..."
                    ),
                    StepEndEvent(
                        run_id="run_abc123",
                        step_id="analyze",
                        status=StepStatus.SUCCESS,
                        outputs={"result": ArtifactRef(...)},
                        duration_ms=5000.0,
                        event_hash="sha256:evt3...",
                        previous_hash="sha256:evt2..."
                    ),
                    RunEndEvent(
                        run_id="run_abc123",
                        status=RunStatus.COMPLETED,
                        final_outputs={"result": ArtifactRef(...)},
                        duration_ms=5500.0,
                        event_hash="sha256:xyz789...",
                        previous_hash="sha256:evt3..."
                    )
                ],
                event_hashes=[
                    "sha256:evt1...",
                    "sha256:evt2...",
                    "sha256:evt3...",
                    "sha256:xyz789..."
                ],
                artifacts=[ArtifactRef(...), ArtifactRef(...)],
                identities=[IdentityAttestation(...)],
                status=RunStatus.COMPLETED,
                started_at=datetime(2024, 12, 27, 10, 0, 0),
                completed_at=datetime(2024, 12, 27, 10, 0, 5, 500000)
            )

        Run in progress (not yet complete):
            RunRecord(
                run_id="run_def456",
                record_hash="sha256:abc123...",  # Hash of latest event so far
                events=[
                    RunStartEvent(...),
                    StepStartEvent(...),
                    StepEndEvent(...),
                    StepStartEvent(...)  # Currently executing
                ],
                event_hashes=["sha256:...", "sha256:...", ...],
                status=RunStatus.RUNNING,  # Still running
                started_at=datetime(...),
                completed_at=None  # Not yet completed
            )
    """

    # ========================================================================
    # Core Identifiers
    # ========================================================================

    run_id: str = Field(..., description="Links to RunPlan via run_id")
    record_hash: str = Field(
        ...,
        description="Current hash chain head (hash of latest event)",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )

    # ========================================================================
    # Append-Only Event Log (AUTHORITATIVE)
    # ========================================================================

    events: List[Event] = Field(
        default_factory=list,
        description="Ordered list of execution events (append-only)",
    )

    # ========================================================================
    # Artifact References (AUTHORITATIVE)
    # ========================================================================

    artifacts: List[ArtifactRef] = Field(
        default_factory=list,
        description="All produced artifacts (by reference, deduplicated)",
    )

    # ========================================================================
    # Identity Tracking (AUTHORITATIVE)
    # ========================================================================

    identities: List["IdentityAttestation"] = Field(
        default_factory=list,
        description="All identities involved (who did what, when)",
    )

    # ========================================================================
    # Hash Chain (AUTHORITATIVE)
    # ========================================================================

    event_hashes: List[str] = Field(
        default_factory=list,
        description="Hash of each event (for verification)",
    )

    # ========================================================================
    # Execution Status
    # ========================================================================

    status: RunStatus = Field(
        default=RunStatus.RUNNING, description="Current execution status"
    )

    # ========================================================================
    # Timestamps
    # ========================================================================

    started_at: Optional[datetime] = Field(
        None, description="When execution started (from RunStartEvent)"
    )
    completed_at: Optional[datetime] = Field(
        None, description="When execution completed (from RunEndEvent)"
    )

    # ========================================================================
    # Non-Authoritative Metadata
    # ========================================================================

    telemetry: Optional["TelemetryData"] = Field(
        None,
        description="Performance metrics (NOT authoritative, can be regenerated)",
    )
    narrative: Optional[str] = Field(
        None,
        description="Layer 2 narrative (LLM-generated, NOT authoritative)",
    )

    # ========================================================================
    # Computed Properties
    # ========================================================================

    @computed_field
    @property
    def event_count(self) -> int:
        """
        Total number of events in this record.

        Useful for:
        - Progress tracking
        - Complexity assessment
        - Storage estimation
        """
        return len(self.events)

    @computed_field
    @property
    def is_complete(self) -> bool:
        """
        Whether execution has completed (has RunEndEvent).

        Returns:
            True if the last event is a RunEndEvent, False otherwise

        A complete RunRecord has:
        - RunStartEvent (first)
        - Zero or more StepStart/End events (middle)
        - RunEndEvent (last)

        An incomplete RunRecord is missing the final RunEndEvent,
        meaning execution is still in progress or was interrupted.
        """
        if not self.events:
            return False
        return isinstance(self.events[-1], RunEndEvent)

    @computed_field
    @property
    def hash_chain_valid(self) -> bool:
        """
        Verify hash chain integrity.

        This is the core tamper-detection mechanism. It checks:
        1. Each event's previous_hash matches the previous event's hash
        2. Each event's hash matches the stored hash in event_hashes

        Returns:
            True if chain is valid (no tampering), False if broken

        How it works:
            Walk through events and verify:
            - event[0].previous_hash == None (first event)
            - event[1].previous_hash == event[0].event_hash
            - event[2].previous_hash == event[1].event_hash
            - etc.

        If any link is broken → tampering detected!

        Example:
            # Valid chain
            record = RunRecord(
                events=[
                    Event(event_hash="hash1", previous_hash=None),
                    Event(event_hash="hash2", previous_hash="hash1"),
                    Event(event_hash="hash3", previous_hash="hash2"),
                ],
                event_hashes=["hash1", "hash2", "hash3"]
            )
            assert record.hash_chain_valid == True

            # Broken chain (event 2 modified)
            record = RunRecord(
                events=[
                    Event(event_hash="hash1", previous_hash=None),
                    Event(event_hash="MODIFIED", previous_hash="hash1"),  # Tampered!
                    Event(event_hash="hash3", previous_hash="hash2"),
                ],
                event_hashes=["hash1", "hash2", "hash3"]
            )
            assert record.hash_chain_valid == False  # Tampering detected!
        """
        if not self.events:
            return True  # Empty record is trivially valid

        if len(self.events) != len(self.event_hashes):
            return False  # Mismatch in event count

        previous_hash = None
        for event, expected_hash in zip(self.events, self.event_hashes):
            # Verify previous_hash reference
            if event.previous_hash != previous_hash:
                return False  # Chain broken!

            # Verify event hash
            if event.event_hash != expected_hash:
                return False  # Hash mismatch!

            previous_hash = event.event_hash

        return True

    @computed_field
    @property
    def duration_ms(self) -> Optional[float]:
        """
        Total execution duration in milliseconds.

        Computed from timestamps:
        - If completed: completed_at - started_at
        - If running: None (not yet known)

        Returns:
            Duration in milliseconds, or None if not yet completed
        """
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000.0
        return None

    # ========================================================================
    # Configuration
    # ========================================================================

    model_config = {
        "frozen": True,  # Immutable once created
    }


# ============================================================================
# Supporting Models
# ============================================================================


class IdentityAttestation(BaseModel):
    """
    Authoritative record that an identity performed an action.

    This is audit evidence that proves who did what and when.

    Purpose:
        For compliance and legal purposes, we must prove:
        - WHO performed an action (identity)
        - WHAT action was performed
        - WHEN it was performed (timestamp)
        - WHICH event it relates to (event_id)

    Use Cases:
        - "Who initiated this run?" → Identity with action="initiated_run"
        - "Who approved this step?" → Identity with action="approved_step"
        - "Who executed this code?" → Identity with action="executed_step"

    Audit Trail:
        These attestations form a complete audit trail of all actors:
        - Human users (via CLI, UI)
        - Service accounts (automated systems)
        - System processes (kernel, scheduler)

    Examples:
        User initiated run:
            IdentityAttestation(
                event_id="evt_start_001",
                identity=Identity(
                    user_id="alice@company.com",
                    user_type=UserType.HUMAN,
                    auth_method=AuthMethod.OAUTH,
                    verified=True
                ),
                action="initiated_run",
                attested_at=datetime(2024, 12, 27, 10, 0, 0)
            )

        Service executed step:
            IdentityAttestation(
                event_id="evt_step_start_001",
                identity=Identity(
                    user_type=UserType.SERVICE,
                    service_id="ml-inference-service",
                    auth_method=AuthMethod.CERT,
                    verified=True
                ),
                action="executed_step",
                attested_at=datetime(2024, 12, 27, 10, 0, 5)
            )

        Human approved step:
            IdentityAttestation(
                event_id="evt_approval_001",
                identity=Identity(
                    user_id="manager@company.com",
                    user_type=UserType.HUMAN,
                    auth_method=AuthMethod.OAUTH,
                    verified=True
                ),
                action="approved_step",
                attested_at=datetime(2024, 12, 27, 10, 5, 30)
            )
    """

    event_id: str = Field(..., description="Event this attestation is for")
    identity: Identity = Field(..., description="Who performed the action")
    action: str = Field(
        ...,
        description="What action was performed",
        examples=["initiated_run", "approved_step", "executed_step"],
    )
    attested_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the action was performed",
    )

    model_config = {"frozen": True}


class TelemetryData(BaseModel):
    """
    Performance metrics (non-authoritative).

    This data aids in understanding system performance but is NOT
    audit evidence. It can be regenerated from authoritative events.

    Purpose:
        Telemetry provides operational insights:
        - How long did execution take? (duration)
        - Which steps were slowest? (step_durations)
        - How much memory was used? (memory_peak_mb)
        - How much CPU time? (cpu_time_ms)

    Non-Authoritative:
        This data is helpful but NOT legally binding because:
        - It can be derived from authoritative events
        - It may be approximate (sampling, rounding)
        - It's not part of the hash chain
        - It's for monitoring, not compliance

    Regeneration:
        Telemetry can be recomputed from RunRecord:
        - total_duration_ms: completed_at - started_at
        - step_durations: Each StepEndEvent.duration_ms
        - Other metrics: Derived from events

    Use Cases:
        - Performance monitoring dashboards
        - SLA compliance checking
        - Bottleneck identification
        - Cost estimation

    Examples:
        Basic telemetry:
            TelemetryData(
                total_duration_ms=5500.0,
                step_durations={
                    "analyze": 5000.0,
                    "validate": 400.0
                },
                memory_peak_mb=256.5,
                cpu_time_ms=3200.0
            )

        Minimal telemetry:
            TelemetryData(
                total_duration_ms=1000.0,
                step_durations={"quick_step": 1000.0}
            )
    """

    total_duration_ms: float = Field(
        ..., description="Total execution time in milliseconds"
    )
    step_durations: Dict[str, float] = Field(
        default_factory=dict,
        description="Duration per step (step_id → milliseconds)",
    )
    memory_peak_mb: Optional[float] = Field(
        None, description="Peak memory usage in megabytes"
    )
    cpu_time_ms: Optional[float] = Field(
        None, description="Total CPU time in milliseconds"
    )

    # Additional metrics
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom metrics",
    )

    model_config = {"frozen": True}


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "RunRecord",
    "IdentityAttestation",
    "TelemetryData",
]
