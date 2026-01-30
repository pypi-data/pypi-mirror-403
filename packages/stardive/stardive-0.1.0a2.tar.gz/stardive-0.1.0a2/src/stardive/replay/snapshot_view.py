"""
Snapshot View Module for Stardive Replay.

This module provides read-only views of execution snapshots, enabling
reconstruction of past executions without re-running them.

Mode A: Snapshot Reconstruction (Primary API)
- Input: run_id
- Output: RunSnapshotView
- Uses stored artifacts + events only
- No executors, no re-running
- Always available

Key Principles:
1. **Read-Only**: Snapshot views are projections, not mutable state
2. **Event-Anchored**: Every view is traceable to immutable stored events
3. **No Re-Execution**: Reconstruction uses stored data only
4. **Audit-Grade**: Complete provenance for every field

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4.2) - Snapshot replay requirements
- docs/RUNRECORD_DESIGN.md - RunRecord architecture
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field

from ..models.artifacts import ArtifactRef
from ..models.enums import RunStatus, StepStatus
from ..models.events import (
    Event,
    RunEndEvent,
    RunStartEvent,
    StepEndEvent,
    StepStartEvent,
)
from ..models.run_record import RunRecord
from ..storage.base import StorageBackend


# ============================================================================
# Step Snapshot View
# ============================================================================


class StepSnapshotView(BaseModel):
    """
    Read-only view of a step's execution snapshot.

    Anchored to immutable event stream for debugging and verification.
    This is a projection of step execution data, not the source of truth.

    Purpose:
        Provides a convenient view of what happened during a step's execution:
        - Inputs consumed (from StepStartEvent)
        - Outputs produced (from StepEndEvent)
        - Execution status and timing
        - Event anchors for traceability

    Event Anchors:
        Every field is traceable to immutable events via:
        - start_event_index: Index of StepStartEvent in event sequence
        - end_event_index: Index of StepEndEvent (None if step incomplete)

        This enables auditors to verify the projection against source events.

    Examples:
        Completed step:
            StepSnapshotView(
                run_id="run_abc123",
                step_id="analyze",
                step_type=StepType.LLM,
                status=StepStatus.SUCCESS,
                inputs={"data": ArtifactRef(...)},
                outputs={"result": ArtifactRef(...)},
                started_at=datetime(...),
                ended_at=datetime(...),
                duration_ms=5000,
                error=None,
                start_event_index=1,
                end_event_index=2
            )

        Failed step:
            StepSnapshotView(
                run_id="run_abc123",
                step_id="fetch",
                step_type=StepType.HTTP,
                status=StepStatus.FAILED,
                inputs={"url": ArtifactRef(...)},
                outputs={},
                started_at=datetime(...),
                ended_at=datetime(...),
                duration_ms=30000,
                error="TimeoutError: Request timed out",
                start_event_index=1,
                end_event_index=2
            )
    """

    # Core identifiers
    run_id: str = Field(..., description="Run this step belongs to")
    step_id: str = Field(..., description="Step identifier")
    step_type: Optional[str] = Field(
        None,
        description="Type of step (llm, python, http, human_approval)",
    )

    # Execution status
    status: StepStatus = Field(..., description="Final step status")

    # Inputs and outputs (by reference)
    inputs: Dict[str, ArtifactRef] = Field(
        default_factory=dict,
        description="Input artifacts (from StepStartEvent)",
    )
    outputs: Dict[str, ArtifactRef] = Field(
        default_factory=dict,
        description="Output artifacts (from StepEndEvent)",
    )

    # Timing
    started_at: datetime = Field(..., description="When step started")
    ended_at: Optional[datetime] = Field(
        None,
        description="When step ended (None if incomplete)",
    )
    duration_ms: Optional[float] = Field(
        None,
        description="Execution duration in milliseconds",
    )

    # Error information
    error: Optional[str] = Field(
        None,
        description="Error message if step failed",
    )

    # Event anchors for traceability
    start_event_index: int = Field(
        ...,
        description="Index of StepStartEvent in event sequence",
    )
    end_event_index: Optional[int] = Field(
        None,
        description="Index of StepEndEvent (None if step incomplete)",
    )

    # Retry information
    attempt: int = Field(
        default=1,
        description="Attempt number (1 for first attempt)",
    )

    model_config = {"frozen": True}


# ============================================================================
# Run Snapshot View
# ============================================================================


class RunSnapshotView(BaseModel):
    """
    Read-only view of an entire run's execution snapshot.

    This is the primary API for snapshot reconstruction (Mode A).
    It provides a complete view of what happened during execution.

    Purpose:
        Provides a convenient, read-only view of a complete run:
        - All steps with their inputs/outputs
        - Final outputs
        - Execution timeline
        - Status summary

    Event Anchors:
        The run_start_event_index and run_end_event_index fields anchor
        this view to the immutable event stream for auditing.

    Usage:
        # Reconstruct snapshot from storage
        snapshot = reconstruct_run(storage, "run_abc123")

        # Access step snapshots
        step = snapshot.get_step("analyze")
        print(step.status)  # StepStatus.SUCCESS

        # Get final outputs
        for name, ref in snapshot.final_outputs.items():
            print(f"{name}: {ref.content_hash}")

    Examples:
        Completed run:
            RunSnapshotView(
                run_id="run_abc123",
                run_plan_id="plan_abc123",
                status=RunStatus.COMPLETED,
                steps={"analyze": StepSnapshotView(...), "report": StepSnapshotView(...)},
                final_outputs={"result": ArtifactRef(...)},
                started_at=datetime(...),
                ended_at=datetime(...),
                duration_ms=15000,
                run_start_event_index=0,
                run_end_event_index=5
            )
    """

    # Core identifiers
    run_id: str = Field(..., description="Run identifier")
    run_plan_id: Optional[str] = Field(
        None,
        description="Reference to RunPlan (if available)",
    )

    # Execution status
    status: RunStatus = Field(..., description="Final run status")

    # Steps
    steps: Dict[str, StepSnapshotView] = Field(
        default_factory=dict,
        description="Step snapshots keyed by step_id",
    )

    # Final outputs
    final_outputs: Dict[str, ArtifactRef] = Field(
        default_factory=dict,
        description="Final output artifacts from RunEndEvent",
    )

    # Timing
    started_at: datetime = Field(..., description="When run started")
    ended_at: Optional[datetime] = Field(
        None,
        description="When run ended (None if incomplete)",
    )
    duration_ms: Optional[float] = Field(
        None,
        description="Total duration in milliseconds",
    )

    # Event anchors
    run_start_event_index: int = Field(
        default=0,
        description="Index of RunStartEvent (always 0)",
    )
    run_end_event_index: Optional[int] = Field(
        None,
        description="Index of RunEndEvent (None if incomplete)",
    )

    model_config = {"frozen": True}

    def get_step(self, step_id: str) -> Optional[StepSnapshotView]:
        """
        Get snapshot for a specific step.

        Args:
            step_id: Step identifier

        Returns:
            StepSnapshotView if step exists, None otherwise
        """
        return self.steps.get(step_id)

    @computed_field
    @property
    def step_count(self) -> int:
        """Number of steps in this run."""
        return len(self.steps)

    @computed_field
    @property
    def is_complete(self) -> bool:
        """Whether the run has completed (has RunEndEvent)."""
        return self.ended_at is not None


# ============================================================================
# Reconstruction Functions
# ============================================================================


def reconstruct_run(storage: StorageBackend, run_id: str) -> RunSnapshotView:
    """
    Reconstruct a read-only snapshot view from stored run.

    This is the primary API for snapshot reconstruction (Mode A).
    It builds a RunSnapshotView from the stored RunRecord without
    re-executing any steps.

    Args:
        storage: Storage backend to retrieve run from
        run_id: Run identifier to reconstruct

    Returns:
        Complete RunSnapshotView with all steps and outputs

    Raises:
        KeyError: If run_id does not exist

    Example:
        >>> storage = SQLiteStorageBackend("stardive.db")
        >>> snapshot = reconstruct_run(storage, "run_abc123")
        >>> print(snapshot.status)
        RunStatus.COMPLETED
        >>> print(snapshot.get_step("analyze").outputs)
        {"result": ArtifactRef(...)}
    """
    # Retrieve RunRecord from storage
    run_record = storage.get_run_record(run_id)

    # Delegate to RunRecord-based reconstruction
    return reconstruct_run_from_record(run_record)


def reconstruct_run_from_record(run_record: RunRecord) -> RunSnapshotView:
    """
    Reconstruct a read-only snapshot view from a RunRecord.

    This function builds a RunSnapshotView by processing the event stream
    in the RunRecord. It extracts step information from StepStartEvent
    and StepEndEvent pairs.

    Args:
        run_record: RunRecord to reconstruct from

    Returns:
        Complete RunSnapshotView with all steps and outputs

    Example:
        >>> record = RunRecord(...)
        >>> snapshot = reconstruct_run_from_record(record)
        >>> print(snapshot.status)
        RunStatus.COMPLETED
    """
    # Extract basic info
    run_id = run_record.run_id
    run_plan_id: Optional[str] = None
    status = run_record.status
    started_at: Optional[datetime] = run_record.started_at
    ended_at: Optional[datetime] = run_record.completed_at
    duration_ms = run_record.duration_ms
    final_outputs: Dict[str, ArtifactRef] = {}
    run_start_event_index = 0
    run_end_event_index: Optional[int] = None

    # Track step events for reconstruction
    step_starts: Dict[str, tuple[StepStartEvent, int]] = {}  # step_id -> (event, index)
    step_ends: Dict[str, tuple[StepEndEvent, int]] = {}  # step_id -> (event, index)

    # Process events
    for i, event in enumerate(run_record.events):
        if isinstance(event, RunStartEvent):
            run_plan_id = event.plan_ref
            started_at = event.timestamp
            run_start_event_index = i

        elif isinstance(event, RunEndEvent):
            status = event.status
            ended_at = event.timestamp
            final_outputs = dict(event.final_outputs)
            run_end_event_index = i

        elif isinstance(event, StepStartEvent):
            step_starts[event.step_id] = (event, i)

        elif isinstance(event, StepEndEvent):
            step_ends[event.step_id] = (event, i)

    # Build step snapshots
    steps: Dict[str, StepSnapshotView] = {}

    for step_id, (start_event, start_index) in step_starts.items():
        # Get corresponding end event if available
        end_event: Optional[StepEndEvent] = None
        end_index: Optional[int] = None
        if step_id in step_ends:
            end_event, end_index = step_ends[step_id]

        # Determine status
        if end_event:
            step_status = end_event.status
            outputs = dict(end_event.outputs)
            ended_at_step = end_event.timestamp
            step_duration_ms = end_event.duration_ms
            error = end_event.error.error_message if end_event.error else None
            attempt = end_event.attempt
        else:
            # Step started but not ended - still running or interrupted
            step_status = StepStatus.RUNNING
            outputs = {}
            ended_at_step = None
            step_duration_ms = None
            error = None
            attempt = 1

        # Determine step type from model/tool identity
        step_type: Optional[str] = None
        if start_event.model_identity:
            step_type = "llm"
        elif start_event.tool_identity:
            step_type = start_event.tool_identity.tool_name

        step_snapshot = StepSnapshotView(
            run_id=run_id,
            step_id=step_id,
            step_type=step_type,
            status=step_status,
            inputs=dict(start_event.inputs),
            outputs=outputs,
            started_at=start_event.timestamp,
            ended_at=ended_at_step,
            duration_ms=step_duration_ms,
            error=error,
            start_event_index=start_index,
            end_event_index=end_index,
            attempt=attempt,
        )

        steps[step_id] = step_snapshot

    # Handle missing started_at (edge case: no RunStartEvent)
    if started_at is None:
        # Use first event timestamp if available
        if run_record.events:
            started_at = run_record.events[0].timestamp
        else:
            started_at = datetime.utcnow()

    return RunSnapshotView(
        run_id=run_id,
        run_plan_id=run_plan_id,
        status=status,
        steps=steps,
        final_outputs=final_outputs,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
        run_start_event_index=run_start_event_index,
        run_end_event_index=run_end_event_index,
    )


def reconstruct_step(
    storage: StorageBackend, run_id: str, step_id: str
) -> StepSnapshotView:
    """
    Reconstruct a single step's snapshot from storage.

    This is a convenience function that reconstructs the full run
    and returns just the requested step.

    Args:
        storage: Storage backend to retrieve run from
        run_id: Run identifier
        step_id: Step identifier to reconstruct

    Returns:
        StepSnapshotView for the requested step

    Raises:
        KeyError: If run_id does not exist
        ValueError: If step_id does not exist in the run

    Example:
        >>> step = reconstruct_step(storage, "run_abc123", "analyze")
        >>> print(step.status)
        StepStatus.SUCCESS
    """
    snapshot = reconstruct_run(storage, run_id)
    step = snapshot.get_step(step_id)

    if step is None:
        raise ValueError(f"Step '{step_id}' not found in run '{run_id}'")

    return step


def reconstruct_step_from_record(
    run_record: RunRecord, step_id: str
) -> StepSnapshotView:
    """
    Reconstruct a single step's snapshot from a RunRecord.

    Args:
        run_record: RunRecord to reconstruct from
        step_id: Step identifier to reconstruct

    Returns:
        StepSnapshotView for the requested step

    Raises:
        ValueError: If step_id does not exist in the run

    Example:
        >>> step = reconstruct_step_from_record(record, "analyze")
        >>> print(step.status)
        StepStatus.SUCCESS
    """
    snapshot = reconstruct_run_from_record(run_record)
    step = snapshot.get_step(step_id)

    if step is None:
        raise ValueError(f"Step '{step_id}' not found in run '{run_record.run_id}'")

    return step


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "StepSnapshotView",
    "RunSnapshotView",
    "reconstruct_run",
    "reconstruct_run_from_record",
    "reconstruct_step",
    "reconstruct_step_from_record",
]
