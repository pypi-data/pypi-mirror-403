"""
Event Models for RunRecord - The Authoritative Audit Trail.

This module defines event models that form the atomic units of execution truth.
Events are immutable, timestamped records of what happened during workflow execution.

Events are the building blocks of RunRecord:
- **RunStartEvent**: Execution begins
- **StepStartEvent**: Step begins execution
- **StepEndEvent**: Step completes (success, failure, or skipped)
- **RunEndEvent**: Execution completes

Key Principles:
1. **Immutability**: Events cannot be modified once created (frozen=True)
2. **Hash-Chained**: Each event includes hash of previous event (blockchain-style)
3. **High-Precision Timestamps**: Events capture exact execution timeline
4. **Authoritative**: These are legal/regulatory audit evidence
5. **Append-Only**: Events can only be added to RunRecord, never removed

Hash Chain Architecture:
    Events form a tamper-evident chain similar to blockchain:

    Event 1: hash = SHA256(event_1_data + None)
             previous_hash = None

    Event 2: hash = SHA256(event_2_data + event_1_hash)
             previous_hash = event_1_hash

    Event 3: hash = SHA256(event_3_data + event_2_hash)
             previous_hash = event_2_hash

    If any event is tampered with, its hash changes, breaking the chain.
    This makes tampering immediately detectable.

Audit Trail Construction:
    Events answer critical audit questions:
    - WHEN did execution start/end? (timestamps)
    - WHAT steps were executed? (StepStart/EndEvents)
    - WHO initiated execution? (RunStartEvent.initiator)
    - WHAT were the inputs/outputs? (ArtifactRefs in events)
    - DID it succeed or fail? (StepStatus, RunStatus)
    - HOW LONG did it take? (duration_ms fields)

For detailed specifications, see:
- docs/canonical-ir.md - Event schema specification
- docs/RUNRECORD_DESIGN.md - RunRecord architecture (to be created)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .artifacts import ArtifactRef
from .enums import RunStatus, StepStatus
from .identity import EnvironmentFingerprint, Identity, ModelIdentity, ToolIdentity


# ============================================================================
# Base Event
# ============================================================================


class Event(BaseModel):
    """
    Base event class for all execution events.

    Every event in the audit trail inherits from this base class, ensuring
    consistent fields for hash chain construction and timestamp tracking.

    Purpose:
        Events are the atomic units of execution truth. Each event records
        one thing that happened at one point in time. By chaining events
        together, we create a complete, tamper-evident audit trail.

    Hash Chain:
        Events form a blockchain-style chain for tamper detection:

        1. Each event has an event_hash (SHA256 of its content)
        2. Each event has a previous_hash (hash of the previous event)
        3. The chain starts with previous_hash=None for the first event
        4. If any event is modified, its hash changes, breaking the chain

        Verification:
            To verify integrity, walk through events and check:
            - event.previous_hash == previous_event.event_hash
            - event.event_hash == SHA256(event content + previous_hash)

    Timestamps:
        Events use high-precision timestamps (microsecond accuracy) to:
        - Enable exact timeline reconstruction
        - Support performance analysis
        - Detect anomalies (e.g., events out of order)

    Examples:
        First event in chain:
            Event(
                event_id="evt_abc123",
                run_id="run_xyz789",
                timestamp=datetime.utcnow(),
                event_hash="sha256:abc123...",
                previous_hash=None  # First event has no previous
            )

        Second event in chain:
            Event(
                event_id="evt_def456",
                run_id="run_xyz789",
                timestamp=datetime.utcnow(),
                event_hash="sha256:def456...",
                previous_hash="sha256:abc123..."  # Links to first event
            )
    """

    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid4().hex[:12]}",
        description="Unique event identifier",
    )
    run_id: str = Field(..., description="Run this event belongs to")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this event occurred (high precision)",
    )

    # Hash Chain
    event_hash: str = Field(
        ...,
        description="SHA256 hash of this event (for integrity)",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )
    previous_hash: Optional[str] = Field(
        None,
        description="Hash of previous event in chain (None for first event)",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )

    model_config = {"frozen": True, "protected_namespaces": ()}


# ============================================================================
# Run-Level Events
# ============================================================================


class RunStartEvent(Event):
    """
    Execution started.

    This is ALWAYS the first event in a RunRecord. It establishes the
    beginning of the audit trail and captures who initiated the execution.

    Purpose:
        Marks the official start of execution and records:
        - WHO initiated the run (identity verification)
        - WHAT plan is being executed (link to RunPlan)
        - WHEN execution began (timestamp)

    Audit Implications:
        - Initiator identity is verified and recorded
        - Plan reference links intent (RunPlan) to truth (RunRecord)
        - Timestamp establishes start of execution window

    Example:
        RunStartEvent(
            event_id="evt_start_001",
            run_id="run_abc123",
            timestamp=datetime(2024, 12, 27, 10, 30, 0),
            event_hash="sha256:abc123...",
            previous_hash=None,  # First event
            plan_ref="run_abc123",
            initiator=Identity(
                user_id="alice@company.com",
                user_type=UserType.HUMAN,
                auth_method=AuthMethod.OAUTH,
                verified=True
            )
        )
    """

    plan_ref: str = Field(
        ..., description="Reference to RunPlan (run_id or plan_hash)"
    )
    initiator: Identity = Field(..., description="Who/what started this run")
    environment: Optional[EnvironmentFingerprint] = Field(
        None, description="Execution environment fingerprint"
    )


class RunEndEvent(Event):
    """
    Execution completed.

    This is ALWAYS the last event in a RunRecord. It establishes the
    end of the audit trail and records the final outcome.

    Purpose:
        Marks the official end of execution and records:
        - WHAT was the final status (success, failure, blocked)
        - WHAT were the final outputs (artifact references)
        - HOW LONG did execution take (total duration)

    Audit Implications:
        - Final status determines compliance/regulatory implications
        - Final outputs are the official results of the workflow
        - Duration enables SLA monitoring and performance analysis

    Examples:
        Successful execution:
            RunEndEvent(
                event_id="evt_end_001",
                run_id="run_abc123",
                timestamp=datetime(2024, 12, 27, 10, 35, 30),
                event_hash="sha256:ghi789...",
                previous_hash="sha256:def456...",
                status=RunStatus.COMPLETED,
                final_outputs={
                    "credit_score": ArtifactRef(...)
                },
                duration_ms=330000.0  # 5.5 minutes
            )

        Failed execution:
            RunEndEvent(
                event_id="evt_end_002",
                run_id="run_def456",
                timestamp=datetime(2024, 12, 27, 11, 15, 45),
                event_hash="sha256:jkl012...",
                previous_hash="sha256:ghi789...",
                status=RunStatus.FAILED,
                final_outputs={},  # No outputs on failure
                duration_ms=15000.0  # Failed after 15 seconds
            )
    """

    status: RunStatus = Field(..., description="Final run status")
    final_outputs: Dict[str, ArtifactRef] = Field(
        default_factory=dict,
        description="Final output artifacts (name → ArtifactRef)",
    )
    duration_ms: float = Field(
        ..., description="Total run duration in milliseconds", ge=0.0
    )


# ============================================================================
# Step-Level Events
# ============================================================================


class StepStartEvent(Event):
    """
    Step execution started.

    Records when a step begins execution. This event captures:
    - Input artifacts (what data the step receives)
    - Parent step (for nested/sub-steps)
    - Model/Tool identity (what's doing the execution)

    Purpose:
        Marks the beginning of a step and establishes:
        - WHAT step is executing (step_id)
        - WHAT are the inputs (artifact references)
        - WITH WHAT is it executing (model or tool identity)
        - WHEN did it start (timestamp)

    Nested Steps:
        Some steps may spawn sub-steps (e.g., LLM with tool calls).
        The parent_step_id field creates a hierarchy:

        Step "analyze" starts
          ├─ Sub-step "fetch_data" starts (parent_step_id="analyze")
          ├─ Sub-step "fetch_data" ends
          ├─ Sub-step "process" starts (parent_step_id="analyze")
          ├─ Sub-step "process" ends
        Step "analyze" ends

    Model vs. Tool Identity:
        - LLM steps have model_identity (which AI model)
        - Other steps have tool_identity (which adapter/tool)
        - Exactly one should be populated (not both)

    Examples:
        LLM step with model identity:
            StepStartEvent(
                event_id="evt_step_start_001",
                run_id="run_abc123",
                step_id="analyze",
                timestamp=datetime(2024, 12, 27, 10, 30, 5),
                event_hash="sha256:mno345...",
                previous_hash="sha256:abc123...",
                inputs={
                    "credit_application": ArtifactRef(
                        artifact_id="art_input_001",
                        content_hash="sha256:...",
                        ...
                    )
                },
                model_identity=ModelIdentity(
                    provider="openai",
                    model_name="gpt-4",
                    temperature=0.7,
                    ...
                ),
                tool_identity=None
            )

        Python step with tool identity:
            StepStartEvent(
                event_id="evt_step_start_002",
                run_id="run_abc123",
                step_id="validate",
                timestamp=datetime(2024, 12, 27, 10, 32, 0),
                event_hash="sha256:pqr678...",
                previous_hash="sha256:mno345...",
                inputs={
                    "data": ArtifactRef(...)
                },
                model_identity=None,
                tool_identity=ToolIdentity(
                    tool_name="validators",
                    tool_version="1.0.0",
                    ...
                )
            )

        Nested sub-step:
            StepStartEvent(
                event_id="evt_substep_start_001",
                run_id="run_abc123",
                step_id="fetch_data",
                parent_step_id="analyze",  # Nested under "analyze"
                timestamp=datetime(2024, 12, 27, 10, 30, 6),
                ...
            )
    """

    step_id: str = Field(..., description="Step identifier")
    parent_step_id: Optional[str] = Field(
        None, description="Parent step ID (for nested steps)"
    )

    # Inputs (by reference, not full content)
    inputs: Dict[str, ArtifactRef] = Field(
        default_factory=dict,
        description="Input artifacts (name → ArtifactRef)",
    )

    # Identity of what's executing (one should be populated)
    model_identity: Optional[ModelIdentity] = Field(
        None, description="Model identity (for LLM steps)"
    )
    tool_identity: Optional[ToolIdentity] = Field(
        None, description="Tool identity (for non-LLM steps)"
    )


class StepEndEvent(Event):
    """
    Step execution completed.

    Records the result of step execution. This is the authoritative record
    of what the step produced and whether it succeeded or failed.

    Purpose:
        Marks the end of a step and records:
        - WHAT was the outcome (success, failure, skipped)
        - WHAT were the outputs (artifact references)
        - WHY did it fail (error information, if applicable)
        - HOW LONG did it take (duration)
        - WHICH ATTEMPT was this (for retries)

    Status Meanings:
        - SUCCESS: Step completed successfully, outputs are valid
        - FAILED: Step encountered an error, see error field
        - SKIPPED: Step was skipped (conditional logic, dependency failed)

    Retry Semantics:
        When a step is retried:
        1. First attempt fails → StepEndEvent(attempt=1, status=FAILED)
        2. Step retries after delay
        3. Second attempt succeeds → StepEndEvent(attempt=2, status=SUCCESS)

        Each attempt gets its own StepStartEvent and StepEndEvent pair.
        The attempt number links them together.

    Error Information:
        If status=FAILED, the error field MUST be populated with:
        - Error type (exception class name)
        - Error message (redacted to remove secrets)
        - Error code (if applicable)
        - Stack trace (limited depth, redacted)

    Examples:
        Successful step:
            StepEndEvent(
                event_id="evt_step_end_001",
                run_id="run_abc123",
                step_id="analyze",
                timestamp=datetime(2024, 12, 27, 10, 32, 30),
                event_hash="sha256:stu901...",
                previous_hash="sha256:pqr678...",
                status=StepStatus.SUCCESS,
                outputs={
                    "credit_score": ArtifactRef(
                        artifact_id="art_output_001",
                        content_hash="sha256:...",
                        ...
                    )
                },
                error=None,
                attempt=1,
                duration_ms=25000.0  # 25 seconds
            )

        Failed step:
            StepEndEvent(
                event_id="evt_step_end_002",
                run_id="run_abc123",
                step_id="fetch_data",
                timestamp=datetime(2024, 12, 27, 10, 33, 0),
                event_hash="sha256:vwx234...",
                previous_hash="sha256:stu901...",
                status=StepStatus.FAILED,
                outputs={},  # No outputs on failure
                error=ErrorInfo(
                    error_type="TimeoutError",
                    error_message="Request timed out after 30s",
                    error_code="TIMEOUT",
                    stack_trace="Traceback (most recent call last):\\n  ..."
                ),
                attempt=1,
                duration_ms=30000.0
            )

        Retry succeeded:
            StepEndEvent(
                event_id="evt_step_end_003",
                run_id="run_abc123",
                step_id="fetch_data",
                timestamp=datetime(2024, 12, 27, 10, 33, 15),
                event_hash="sha256:yza567...",
                previous_hash="sha256:vwx234...",
                status=StepStatus.SUCCESS,
                outputs={"data": ArtifactRef(...)},
                error=None,
                attempt=2,  # Second attempt
                duration_ms=10000.0
            )

        Skipped step:
            StepEndEvent(
                event_id="evt_step_end_004",
                run_id="run_abc123",
                step_id="optional_check",
                timestamp=datetime(2024, 12, 27, 10, 33, 16),
                event_hash="sha256:bcd890...",
                previous_hash="sha256:yza567...",
                status=StepStatus.SKIPPED,
                outputs={},
                error=None,
                attempt=1,
                duration_ms=0.0  # No execution time
            )
    """

    step_id: str = Field(..., description="Step identifier")
    status: StepStatus = Field(..., description="Step execution status")

    # Outputs (by reference, not full content)
    outputs: Dict[str, ArtifactRef] = Field(
        default_factory=dict,
        description="Output artifacts (name → ArtifactRef)",
    )

    # Error information (required if status=FAILED)
    error: Optional["ErrorInfo"] = Field(
        None, description="Error details (required if status=FAILED)"
    )

    # Retry information
    attempt: int = Field(
        1,
        description="Attempt number (1 for first attempt, 2+ for retries)",
        ge=1,
    )

    # Performance
    duration_ms: float = Field(
        ..., description="Step execution duration in milliseconds", ge=0.0
    )


# ============================================================================
# Supporting Models
# ============================================================================


class ErrorInfo(BaseModel):
    """
    Error information for failed steps.

    Captures enough detail for debugging without exposing secrets.

    Purpose:
        When a step fails, we need to record WHY it failed for:
        - Debugging and root cause analysis
        - Compliance (proving we handled errors appropriately)
        - Monitoring and alerting
        - Retry decision making

    Security Considerations:
        Error messages and stack traces may contain sensitive data:
        - Secrets (API keys in error messages)
        - PII (user data in exceptions)
        - Internal paths (exposing system architecture)

        ALL error data is redacted before storage:
        - Secret patterns removed (API keys, tokens)
        - PII patterns removed (emails, SSNs)
        - Stack traces limited to N frames
        - File paths sanitized

    Fields:
        - error_type: Exception class name (e.g., "TimeoutError", "ValueError")
        - error_message: Human-readable error (REDACTED)
        - error_code: Optional error code for categorization
        - stack_trace: Python stack trace (REDACTED, limited depth)

    Examples:
        Timeout error:
            ErrorInfo(
                error_type="TimeoutError",
                error_message="Request timed out after 30s",
                error_code="TIMEOUT",
                stack_trace="Traceback (most recent call last):\\n  ..."
            )

        Validation error:
            ErrorInfo(
                error_type="ValidationError",
                error_message="Invalid credit score: must be 300-850",
                error_code="VALIDATION_FAILED",
                stack_trace=None  # May not include stack for validation errors
            )

        API error:
            ErrorInfo(
                error_type="OpenAIError",
                error_message="API rate limit exceeded (code: 429)",
                error_code="RATE_LIMIT",
                stack_trace="Traceback (most recent call last):\\n  ..."
            )

        Redacted error (contained secrets):
            ErrorInfo(
                error_type="AuthenticationError",
                error_message="Invalid API key: [REDACTED]",
                error_code="AUTH_FAILED",
                stack_trace="Traceback (most recent call last):\\n  ..."
            )
    """

    error_type: str = Field(
        ...,
        description="Error class name",
        examples=["TimeoutError", "ValueError", "OpenAIError"],
    )
    error_message: str = Field(
        ..., description="Error message (redacted for secrets/PII)"
    )
    error_code: Optional[str] = Field(
        None,
        description="Error code (if applicable)",
        examples=["TIMEOUT", "VALIDATION_FAILED", "RATE_LIMIT"],
    )
    stack_trace: Optional[str] = Field(
        None,
        description="Stack trace (redacted, limited depth)",
    )

    # Additional context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error context (redacted)",
    )

    model_config = {"frozen": True}


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Base
    "Event",
    # Run Events
    "RunStartEvent",
    "RunEndEvent",
    # Step Events
    "StepStartEvent",
    "StepEndEvent",
    # Supporting
    "ErrorInfo",
]
