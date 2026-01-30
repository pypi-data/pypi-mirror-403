"""
Builder Patterns for Constructing Immutable IR Models.

This module provides builder classes for constructing immutable RunPlan and
RunRecord models incrementally. Since these models are frozen (immutable) after
creation, builders provide a mutable intermediate representation during construction.

Builders Provided:
- **RunPlanBuilder**: For instrumentation mode (incremental plan building)
- **RunRecordBuilder**: For all modes (event-by-event record construction)

Key Principles:
1. **Separation of Concerns**: Mutable builders vs. immutable models
2. **Incremental Construction**: Add pieces one at a time
3. **Validation**: Validate before freezing into immutable model
4. **Hash Computation**: Automatically compute hashes during build
5. **Type Safety**: Pydantic validation on final build()

Why Builders?
    RunPlan and RunRecord are marked frozen=True, making them immutable.
    This is essential for audit integrity (no tampering). However, we need
    to construct these models incrementally:

    - RunPlan in instrumentation mode: Steps added as events arrive
    - RunRecord in all modes: Events appended during execution

    Builders provide mutable construction while preserving immutable results.

For detailed specifications, see:
- docs/canonical-ir.md - IR architecture
- docs/RUNRECORD_DESIGN.md - RunRecord design (to be created)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from .artifacts import ArtifactRef, ArtifactSpec
from .enums import RunStatus, SourceType
from .events import Event, RunEndEvent, RunStartEvent, StepEndEvent, StepStartEvent
from .identity import EnvironmentFingerprint, Identity
from .policy import PolicySpec
from .run_plan import RunPlan
from .run_record import IdentityAttestation, RunRecord, TelemetryData
from .steps import StepSpec


# ============================================================================
# RunPlanBuilder (for Instrumentation Mode)
# ============================================================================


class RunPlanBuilder:
    """
    Mutable builder for constructing RunPlan incrementally.

    Purpose:
        In instrumentation mode, RunPlan is built DURING execution as events
        arrive from external frameworks (LangChain, OTEL). We can't create
        the complete RunPlan upfront because we don't know what steps will
        execute.

        RunPlanBuilder provides a mutable container for collecting steps,
        dependencies, and artifacts as they're discovered, then freezes them
        into an immutable RunPlan when execution completes.

    Lifecycle:
        1. Create builder with run metadata
        2. Add steps as they're discovered (from events)
        3. Add dependencies as they're inferred
        4. Add expected artifacts as they're produced
        5. Build immutable RunPlan when execution completes

    Thread Safety:
        RunPlanBuilder is NOT thread-safe. If building from multiple threads,
        use external synchronization.

    Examples:
        Basic instrumentation mode:
            builder = RunPlanBuilder(
                run_id="run_abc123",
                initiator=Identity(...),
                environment=EnvironmentFingerprint(...),
                source_type=SourceType.INSTRUMENTATION,
                source_ref="langchain://run_abc123"
            )

            # As LangChain executes, add steps:
            builder.add_step(StepSpec(
                step_id="analyze",
                step_type="llm",
                config={"model": "gpt-4"},
                executor_ref="stardive.adapters.llm:OpenAIAdapter"
            ))

            builder.add_step(StepSpec(
                step_id="validate",
                step_type="python",
                config={"function_ref": "validators:check"},
                executor_ref="stardive.adapters.python:PythonAdapter"
            ))

            # Add dependency (inferred from execution order)
            builder.add_dependency("validate", "analyze")

            # Build immutable plan
            plan = builder.build()
            assert plan.step_count == 2
            assert plan.is_instrumentation_mode == True

        With artifacts:
            builder = RunPlanBuilder(...)

            builder.add_step(StepSpec(step_id="generate_report", ...))

            builder.add_expected_artifact(ArtifactSpec(
                artifact_id="final_report",
                artifact_type=ArtifactType.OUTPUT,
                produced_by_step="generate_report",
                content_type="application/pdf",
                required=True
            ))

            plan = builder.build()
    """

    def __init__(
        self,
        run_id: str,
        initiator: Identity,
        environment: EnvironmentFingerprint,
        source_type: SourceType,
        source_ref: Optional[str] = None,
        policy: Optional[PolicySpec] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None,
    ):
        """
        Initialize RunPlanBuilder.

        Args:
            run_id: Unique run identifier
            initiator: Who initiated the run
            environment: Where the run executes
            source_type: How the plan was created (YAML, SDK, INSTRUMENTATION)
            source_ref: Reference to source (file path, code location, etc.)
            policy: Execution policy (defaults to permissive)
            name: Human-readable workflow name
            description: Workflow description
            version: Workflow version
        """
        self._run_id = run_id
        self._initiator = initiator
        self._environment = environment
        self._source_type = source_type
        self._source_ref = source_ref
        self._policy = policy or PolicySpec()
        self._name = name
        self._description = description
        self._version = version

        # Mutable collections
        self._steps: Dict[str, StepSpec] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self._expected_artifacts: List[ArtifactSpec] = []
        self._tags: List[str] = []
        self._created_at = datetime.utcnow()

    def add_step(self, step: StepSpec) -> None:
        """
        Add a step to the plan.

        Args:
            step: Step specification to add

        Raises:
            ValueError: If step_id already exists
        """
        if step.step_id in self._steps:
            raise ValueError(f"Step '{step.step_id}' already exists in plan")
        self._steps[step.step_id] = step

    def add_dependency(self, step_id: str, depends_on: str) -> None:
        """
        Add a dependency relationship.

        Args:
            step_id: Step that depends on another
            depends_on: Step that must complete first

        Raises:
            ValueError: If either step doesn't exist
        """
        if step_id not in self._steps:
            raise ValueError(f"Step '{step_id}' not found in plan")
        if depends_on not in self._steps:
            raise ValueError(f"Dependency '{depends_on}' not found in plan")

        if step_id not in self._dependencies:
            self._dependencies[step_id] = []
        if depends_on not in self._dependencies[step_id]:
            self._dependencies[step_id].append(depends_on)

    def add_expected_artifact(self, artifact: ArtifactSpec) -> None:
        """Add an expected artifact specification."""
        self._expected_artifacts.append(artifact)

    def add_tag(self, tag: str) -> None:
        """Add a tag for categorization."""
        if tag not in self._tags:
            self._tags.append(tag)

    def build(self) -> RunPlan:
        """
        Build immutable RunPlan from mutable builder state.

        Computes plan_hash and freezes the plan.

        Returns:
            Immutable RunPlan

        Raises:
            ValidationError: If plan validation fails
        """
        # Compute plan hash (deterministic serialization)
        plan_hash = self._compute_plan_hash()

        return RunPlan(
            run_id=self._run_id,
            plan_hash=plan_hash,
            initiator=self._initiator,
            environment=self._environment,
            steps=self._steps.copy(),  # Copy to prevent mutation
            dependencies=self._dependencies.copy(),
            policy=self._policy,
            expected_artifacts=self._expected_artifacts.copy(),
            created_at=self._created_at,
            source_type=self._source_type,
            source_ref=self._source_ref,
            name=self._name,
            description=self._description,
            version=self._version,
            tags=self._tags.copy(),
        )

    def _compute_plan_hash(self) -> str:
        """
        Compute SHA256 hash of plan for tamper detection.

        Uses canonical serialization (sorted keys, no whitespace).

        Returns:
            Hash in format "sha256:..."
        """
        # Serialize plan data deterministically
        plan_data = {
            "run_id": self._run_id,
            "steps": {k: v.model_dump() for k, v in sorted(self._steps.items())},
            "dependencies": {k: sorted(v) for k, v in sorted(self._dependencies.items())},
            "policy": self._policy.model_dump(),
            "source_type": self._source_type.value,
            "created_at": self._created_at.isoformat(),
        }

        canonical_json = json.dumps(plan_data, sort_keys=True, separators=(",", ":"))
        hash_digest = hashlib.sha256(canonical_json.encode()).hexdigest()
        return f"sha256:{hash_digest}"


# ============================================================================
# RunRecordBuilder (for All Modes)
# ============================================================================


class RunRecordBuilder:
    """
    Mutable builder for constructing RunRecord event-by-event.

    Purpose:
        RunRecord is immutable (frozen) to prevent tampering, but we need to
        build it incrementally as execution progresses. RunRecordBuilder
        provides a mutable container for appending events, then freezes
        into an immutable RunRecord when execution completes.

    Hash Chain:
        Builder automatically maintains the hash chain:
        - Computes hash for each event
        - Links events via previous_hash
        - Updates record_hash to latest event hash

    Lifecycle:
        1. Create builder with run_id
        2. Append RunStartEvent
        3. Append StepStart/End events as steps execute
        4. Append RunEndEvent when execution completes
        5. Build immutable RunRecord

    Thread Safety:
        RunRecordBuilder is NOT thread-safe. If appending from multiple
        threads, use external synchronization.

    Examples:
        Simple successful run:
            builder = RunRecordBuilder(run_id="run_abc123")

            # Execution starts
            builder.append_event(RunStartEvent(
                run_id="run_abc123",
                plan_ref="run_abc123",
                initiator=Identity(...)
            ))

            # Step executes
            builder.append_event(StepStartEvent(
                run_id="run_abc123",
                step_id="analyze",
                inputs={"data": ArtifactRef(...)}
            ))

            builder.append_event(StepEndEvent(
                run_id="run_abc123",
                step_id="analyze",
                status=StepStatus.SUCCESS,
                outputs={"result": ArtifactRef(...)},
                duration_ms=5000.0
            ))

            # Execution completes
            builder.append_event(RunEndEvent(
                run_id="run_abc123",
                status=RunStatus.COMPLETED,
                final_outputs={"result": ArtifactRef(...)},
                duration_ms=5500.0
            ))

            # Build immutable record
            record = builder.build()
            assert record.is_complete == True
            assert record.hash_chain_valid == True

        With telemetry:
            builder = RunRecordBuilder(run_id="run_abc123")

            # ... append events ...

            builder.set_telemetry(TelemetryData(
                total_duration_ms=5500.0,
                step_durations={"analyze": 5000.0}
            ))

            record = builder.build()
    """

    def __init__(self, run_id: str):
        """
        Initialize RunRecordBuilder.

        Args:
            run_id: Unique run identifier (links to RunPlan)
        """
        self._run_id = run_id
        self._events: List[Event] = []
        self._event_hashes: List[str] = []
        self._artifacts: Dict[str, ArtifactRef] = {}  # Deduplicated by artifact_id
        self._identities: List[IdentityAttestation] = []
        self._status = RunStatus.RUNNING
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._telemetry: Optional[TelemetryData] = None
        self._narrative: Optional[str] = None

    def append_event(self, event: Event) -> None:
        """
        Append an event to the record.

        Automatically:
        - Computes event hash
        - Links to previous event (hash chain)
        - Extracts artifacts from event
        - Updates run status and timestamps

        Args:
            event: Event to append (will be modified to set previous_hash)

        Note:
            Event hash and previous_hash should already be set on the event.
            This method validates they're correct and appends.
        """
        # Verify event belongs to this run
        if event.run_id != self._run_id:
            raise ValueError(
                f"Event run_id '{event.run_id}' doesn't match record run_id '{self._run_id}'"
            )

        # Verify hash chain
        expected_previous_hash = self._event_hashes[-1] if self._event_hashes else None
        if event.previous_hash != expected_previous_hash:
            raise ValueError(
                f"Event previous_hash mismatch. Expected {expected_previous_hash}, "
                f"got {event.previous_hash}"
            )

        # Append event and hash
        self._events.append(event)
        self._event_hashes.append(event.event_hash)

        # Extract artifacts (deduplicate by artifact_id)
        if isinstance(event, StepStartEvent):
            for artifact in event.inputs.values():
                self._artifacts[artifact.artifact_id] = artifact
        elif isinstance(event, StepEndEvent):
            for artifact in event.outputs.values():
                self._artifacts[artifact.artifact_id] = artifact
        elif isinstance(event, RunEndEvent):
            for artifact in event.final_outputs.values():
                self._artifacts[artifact.artifact_id] = artifact

        # Update status and timestamps
        if isinstance(event, RunStartEvent):
            self._started_at = event.timestamp
            # Add identity attestation
            self._identities.append(
                IdentityAttestation(
                    event_id=event.event_id,
                    identity=event.initiator,
                    action="initiated_run",
                    attested_at=event.timestamp,
                )
            )
        elif isinstance(event, RunEndEvent):
            self._completed_at = event.timestamp
            self._status = event.status

    def add_identity_attestation(self, attestation: IdentityAttestation) -> None:
        """Add an identity attestation."""
        self._identities.append(attestation)

    def set_telemetry(self, telemetry: TelemetryData) -> None:
        """Set performance telemetry (non-authoritative)."""
        self._telemetry = telemetry

    def set_narrative(self, narrative: str) -> None:
        """Set Layer 2 narrative (non-authoritative)."""
        self._narrative = narrative

    def build(self) -> RunRecord:
        """
        Build immutable RunRecord from mutable builder state.

        Returns:
            Immutable RunRecord

        Raises:
            ValueError: If record is incomplete or invalid
        """
        # Compute record hash (hash of latest event)
        record_hash = (
            self._event_hashes[-1]
            if self._event_hashes
            else f"sha256:{'0' * 64}"
        )

        return RunRecord(
            run_id=self._run_id,
            record_hash=record_hash,
            events=self._events.copy(),
            artifacts=list(self._artifacts.values()),
            identities=self._identities.copy(),
            event_hashes=self._event_hashes.copy(),
            status=self._status,
            started_at=self._started_at,
            completed_at=self._completed_at,
            telemetry=self._telemetry,
            narrative=self._narrative,
        )

    @property
    def event_count(self) -> int:
        """Number of events appended so far."""
        return len(self._events)

    @property
    def is_complete(self) -> bool:
        """Whether record has RunEndEvent."""
        return bool(self._events and isinstance(self._events[-1], RunEndEvent))


# ============================================================================
# Hash Computation Utilities
# ============================================================================


def compute_event_hash(
    event_id: str,
    run_id: str,
    timestamp: datetime,
    event_data: dict,
    previous_hash: Optional[str],
) -> str:
    """
    Compute SHA256 hash for an event.

    Uses canonical serialization to ensure deterministic hashing.

    Args:
        event_id: Unique event identifier
        run_id: Run identifier
        timestamp: Event timestamp
        event_data: Event-specific data (as dict)
        previous_hash: Hash of previous event (None for first event)

    Returns:
        Hash in format "sha256:..."

    Example:
        hash = compute_event_hash(
            event_id="evt_abc123",
            run_id="run_xyz789",
            timestamp=datetime.utcnow(),
            event_data={"step_id": "analyze", "status": "success"},
            previous_hash="sha256:..."
        )
    """
    # Canonical representation
    canonical_data = {
        "event_id": event_id,
        "run_id": run_id,
        "timestamp": timestamp.isoformat(),
        "data": event_data,
        "previous_hash": previous_hash,
    }

    canonical_json = json.dumps(canonical_data, sort_keys=True, separators=(",", ":"))
    hash_digest = hashlib.sha256(canonical_json.encode()).hexdigest()
    return f"sha256:{hash_digest}"


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "RunPlanBuilder",
    "RunRecordBuilder",
    "compute_event_hash",
]
