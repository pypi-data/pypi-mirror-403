"""
Event Emission API for Zero-Replacement Instrumentation.

This module provides the core emit_* functions that enable users to wrap
existing AI workflows with minimal code changes to obtain audit-grade records.

Key Functions:
- emit_run_start(): Initialize execution tracking, create RunContext
- emit_step_start(): Mark step beginning with typed inputs
- emit_artifact(): Explicitly capture and hash artifacts
- emit_step_end(): Mark step completion with typed outputs
- emit_run_end(): Finalize execution tracking

Design Principles:
1. **Explicit Context**: Every function accepts RunContext (no thread-local)
2. **Immediate Storage**: Events stored immediately for audit integrity
3. **Type Safety**: Only ArtifactRef objects in events (no arbitrary Python objects)
4. **Explicit Artifacts**: Users must call emit_artifact() to capture content
5. **Hash Chain**: Each event links to previous via hash chain

For detailed specifications, see:
- CURRENT_JOB.md (Phase 3.3 - Instrumentation API)
- docs/instrumentation-guide.md (to be created)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from stardive.artifacts import (
    ArtifactKind,
    SQLiteArtifactStorage,
    SecretDetectionMode,
    compute_hash,
    serialize_canonical,
    detect_secrets,
    SecretDetectedError,
)
from stardive.models import (
    ArtifactRef,
    EnvironmentFingerprint,
    Identity,
    ModelIdentity,
    RunRecordBuilder,
    RunRecord,
    RunStartEvent,
    RunEndEvent,
    StepStartEvent,
    StepEndEvent,
    StepStatus,
    RunStatus,
    ToolIdentity,
    ErrorInfo,
    compute_event_hash,
)
from stardive.models.enums import UserType, AuthMethod, SourceType, ArtifactType
from stardive.storage import StorageBackend

from .context import RunContext


# ============================================================================
# emit_run_start - Initialize Execution Tracking
# ============================================================================


def emit_run_start(
    storage: StorageBackend,
    initiator: Optional[Dict[str, Any]] = None,
    environment: Optional[Dict[str, Any]] = None,
    plan_ref: Optional[str] = None,
    namespace: Optional[str] = None,
) -> RunContext:
    """
    Initialize execution tracking and return a RunContext for subsequent emissions.

    This is the FIRST function you call when instrumenting a workflow. It creates
    a RunStartEvent, stores it immediately, and returns a RunContext for tracking
    the rest of execution.

    Purpose:
        emit_run_start() is the entry point for instrumentation-based tracking.
        It establishes the audit trail by:
        1. Creating a unique run_id
        2. Recording who initiated the execution (initiator)
        3. Capturing environment context (fingerprint)
        4. Initializing storage backend for immediate event persistence
        5. Creating RunContext for explicit context passing

    Design Decisions:
        - **Immediate storage**: RunStartEvent stored immediately (not buffered)
        - **Explicit context**: Returns RunContext (not just run_id string)
        - **Minimal required fields**: Only storage + initiator required
        - **Auto-capture environment**: Fingerprint computed automatically

    Args:
        storage: StorageBackend for immediate event persistence
        initiator: Identity dict or Identity object (who initiated this run)
        namespace: Optional namespace for organizing runs (org/project/env)
        plan_ref: Optional reference to RunPlan (defaults to run_id)
        environment: Optional EnvironmentFingerprint (auto-detected if not provided)

    Returns:
        RunContext: Context object for tracking this execution

    Examples:
        Basic usage with identity dict:
            from stardive.instrumentation import emit_run_start
            from stardive.storage import SQLiteBackend

            storage = SQLiteBackend(db_path="audit.db")
            run_ctx = emit_run_start(
                storage=storage,
                initiator={
                    "user_id": "alice@company.com",
                    "user_type": "human",
                    "auth_method": "oauth"
                }
            )

        With full Identity object:
            from stardive.models import Identity, UserType, AuthMethod

            run_ctx = emit_run_start(
                storage=storage,
                initiator=Identity(
                    user_id="alice@company.com",
                    user_type=UserType.HUMAN,
                    auth_method=AuthMethod.OAUTH,
                    verified=True
                )
            )

    Raises:
        ValueError: If initiator is missing required fields
        StorageError: If event storage fails
    """
    # Generate unique run_id
    run_id = f"run_{uuid4().hex[:16]}"

    # Convert initiator dict to Identity if needed
    if initiator is None:
        # Default development identity
        initiator_obj = Identity(
            user_id="dev@localhost",
            user_type=UserType.HUMAN,
            auth_method=AuthMethod.NONE,
            verified=False,
        )
    elif isinstance(initiator, dict):
        # Convert dict to Identity
        initiator_obj = Identity(**initiator)
    elif isinstance(initiator, Identity):
        initiator_obj = initiator
    else:
        raise TypeError(f"initiator must be dict or Identity, got {type(initiator)}")

    # Convert environment dict to EnvironmentFingerprint if needed
    if environment is None:
        # Minimal environment fingerprint (auto-detection could be added later)
        import platform
        import sys

        # Compute empty dependencies hash
        deps_hash = compute_hash({})

        environment_obj = EnvironmentFingerprint(
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            dependencies_hash=deps_hash,
            os=platform.system(),
            os_version=platform.release(),
            arch=platform.machine(),
            fingerprint_hash=deps_hash,  # Simple hash for default case
        )
    elif isinstance(environment, dict):
        # Fill in missing required fields with defaults
        import platform
        import sys

        # Compute dependencies hash from provided dependencies or empty dict
        deps = environment.get("dependencies", {})
        deps_hash = compute_hash(deps)

        # Merge with defaults for required fields
        env_with_defaults = {
            "python_version": environment.get(
                "python_version",
                f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            ),
            "dependencies_hash": environment.get("dependencies_hash", deps_hash),
            "os": environment.get("os", platform.system()),
            "os_version": environment.get("os_version", platform.release()),
            "arch": environment.get("arch", platform.machine()),
            "fingerprint_hash": environment.get("fingerprint_hash", deps_hash),
            # Optional fields - only include if provided
            **{k: v for k, v in environment.items()
               if k in ["git_sha", "git_branch", "git_dirty", "container_image",
                        "container_digest", "cloud_provider", "region", "instance_type",
                        "deployment_id", "namespace"]}
        }
        environment_obj = EnvironmentFingerprint(**env_with_defaults)
    elif isinstance(environment, EnvironmentFingerprint):
        environment_obj = environment
    else:
        raise TypeError(
            f"environment must be dict or EnvironmentFingerprint, got {type(environment)}"
        )

    # Use run_id as plan_ref if not provided (instrumentation mode)
    if plan_ref is None:
        plan_ref = run_id

    # Create RunRecordBuilder for incremental construction
    builder = RunRecordBuilder(run_id=run_id)

    # Create and store RunStartEvent
    start_time = datetime.utcnow()

    # Create temporary event for hash computation (bypass validation)
    temp_event = RunStartEvent.model_construct(
        run_id=run_id,
        timestamp=start_time,
        event_hash="sha256:" + "0" * 64,  # Placeholder for hash computation
        previous_hash=None,
        plan_ref=plan_ref,
        initiator=initiator_obj,
        environment=environment_obj,
    )

    # Compute hash for this event
    event_data = {
        "plan_ref": plan_ref,
        "initiator": initiator_obj.model_dump(mode='json'),
        "environment": environment_obj.model_dump(mode='json'),
    }
    event_hash = compute_event_hash(
        event_id=temp_event.event_id,
        run_id=run_id,
        timestamp=start_time,
        event_data=event_data,
        previous_hash=None,
    )

    # Create final event with computed hash
    start_event = RunStartEvent(
        run_id=run_id,
        timestamp=start_time,
        event_hash=event_hash,
        previous_hash=None,
        plan_ref=plan_ref,
        initiator=initiator_obj,
        environment=environment_obj,
    )

    # Append to builder (this validates hash chain)
    builder.append_event(start_event)

    # Store event immediately for audit integrity
    storage.store_event(start_event)

    # Create and return RunContext
    return RunContext(
        run_id=run_id,
        builder=builder,
        storage=storage,
        start_time=start_time,
    )


def emit_step_start(
    ctx: RunContext,
    step_id: str,
    inputs: Optional[Dict[str, ArtifactRef]] = None,
    parent_step_id: Optional[str] = None,
    model_identity: Optional[ModelIdentity] = None,
    tool_identity: Optional[ToolIdentity] = None,
) -> None:
    """
    Mark the beginning of a step execution.

    Creates a StepStartEvent and stores it immediately for audit integrity.
    This function should be called immediately before step execution begins.

    Args:
        ctx: RunContext from emit_run_start()
        step_id: Unique identifier for this step
        inputs: Input artifacts (name → ArtifactRef), must use ArtifactRef objects
        parent_step_id: Parent step ID for nested steps (optional)
        model_identity: Model identity for LLM steps (optional)
        tool_identity: Tool identity for non-LLM steps (optional)

    Examples:
        Basic step start:
            emit_step_start(run_ctx, step_id="process")

        With inputs from previous step:
            # First, explicitly emit the artifact
            data_artifact = emit_artifact(
                run_ctx,
                step_id="fetch",
                name="data",
                content={"values": [1, 2, 3]},
                kind=ArtifactKind.JSON
            )

            # Then pass ArtifactRef to next step
            emit_step_start(
                run_ctx,
                step_id="process",
                inputs={"data": data_artifact}
            )

        LLM step with model identity:
            emit_step_start(
                run_ctx,
                step_id="analyze",
                model_identity=ModelIdentity(
                    provider="openai",
                    model_name="gpt-4",
                    temperature=0.7
                )
            )

    Raises:
        TypeError: If inputs contains non-ArtifactRef values
        ValueError: If step_id is invalid or duplicated
        StorageError: If event storage fails
    """
    # Validate inputs are all ArtifactRef objects
    if inputs:
        for name, artifact in inputs.items():
            if not isinstance(artifact, ArtifactRef):
                raise TypeError(
                    f"Input '{name}' must be ArtifactRef, got {type(artifact)}. "
                    f"Use emit_artifact() to create ArtifactRef objects."
                )

    # Get previous event hash from builder
    previous_hash = ctx.builder._event_hashes[-1] if ctx.builder._event_hashes else None

    # Create StepStartEvent
    timestamp = datetime.utcnow()

    # Create temporary event for hash computation
    temp_event = StepStartEvent.model_construct(
        run_id=ctx.run_id,
        timestamp=timestamp,
        event_hash="sha256:" + "0" * 64,
        previous_hash=previous_hash,
        step_id=step_id,
        parent_step_id=parent_step_id,
        inputs=inputs or {},
        model_identity=model_identity,
        tool_identity=tool_identity,
    )

    # Compute hash for this event
    event_data = {
        "step_id": step_id,
        "parent_step_id": parent_step_id,
        "inputs": {k: v.model_dump(mode='json') for k, v in (inputs or {}).items()},
        "model_identity": model_identity.model_dump(mode='json') if model_identity else None,
        "tool_identity": tool_identity.model_dump(mode='json') if tool_identity else None,
    }
    event_hash = compute_event_hash(
        event_id=temp_event.event_id,
        run_id=ctx.run_id,
        timestamp=timestamp,
        event_data=event_data,
        previous_hash=previous_hash,
    )

    # Create final event with computed hash
    step_start_event = StepStartEvent(
        run_id=ctx.run_id,
        timestamp=timestamp,
        event_hash=event_hash,
        previous_hash=previous_hash,
        step_id=step_id,
        parent_step_id=parent_step_id,
        inputs=inputs or {},
        model_identity=model_identity,
        tool_identity=tool_identity,
    )

    # Append to builder (validates hash chain)
    ctx.builder.append_event(step_start_event)

    # Store event immediately for audit integrity
    ctx.storage.store_event(step_start_event)


def emit_artifact(
    ctx: RunContext,
    step_id: str,
    name: str,
    content: Any,
    kind: ArtifactKind,
    secret_detection_mode: SecretDetectionMode = SecretDetectionMode.BEST_EFFORT,
) -> ArtifactRef:
    """
    Explicitly capture and store an artifact with deterministic hashing.

    This is the ONLY way to create artifacts in the instrumentation API.
    Artifacts must be explicitly emitted - they are never automatically
    captured from function returns or arbitrary Python objects.

    Key Design Principle:
        Only JSON-serializable content is allowed. This ensures:
        - Deterministic hashing (same input → same hash)
        - Security (no arbitrary object leakage)
        - Auditability (content is inspectable)

    Args:
        ctx: RunContext from emit_run_start()
        step_id: Step that produced this artifact
        name: Artifact name (used in lineage tracing)
        content: JSON-serializable content (dict, list, str, int, float, bool, None)
        kind: ArtifactKind (JSON or TEXT in v0.1)
        secret_detection_mode: How to handle potential secrets (default: BEST_EFFORT)

    Returns:
        ArtifactRef: Reference to the stored artifact (for use in step inputs/outputs)

    Examples:
        Basic JSON artifact:
            artifact = emit_artifact(
                run_ctx,
                step_id="process",
                name="result",
                content={"prediction": 0.85, "confidence": "high"},
                kind=ArtifactKind.JSON
            )

        Text artifact:
            artifact = emit_artifact(
                run_ctx,
                step_id="summarize",
                name="summary",
                content="The analysis shows...",
                kind=ArtifactKind.TEXT
            )

        Strict secret detection (raises on suspicious fields):
            artifact = emit_artifact(
                run_ctx,
                step_id="process",
                name="result",
                content={"data": "value"},
                kind=ArtifactKind.JSON,
                secret_detection_mode=SecretDetectionMode.STRICT
            )

    Raises:
        SerializationError: If content is not JSON-serializable
        SecretDetectedError: If secrets detected in strict mode
        TypeError: If kind is not ArtifactKind.JSON or TEXT (v0.1 limitation)
        StorageError: If artifact storage fails
    """
    # v0.1 limitation: Only JSON and TEXT supported
    if kind not in (ArtifactKind.JSON, ArtifactKind.TEXT):
        raise TypeError(
            f"v0.1 only supports ArtifactKind.JSON and TEXT, got {kind}. "
            f"BYTES and FILE support coming in v0.2+"
        )

    # Detect secrets if requested
    if secret_detection_mode != SecretDetectionMode.DISABLED:
        secret_locations = detect_secrets(content, mode=secret_detection_mode)
        if secret_locations:
            if secret_detection_mode == SecretDetectionMode.STRICT:
                raise SecretDetectedError(
                    f"Secrets detected in artifact '{name}' for step '{step_id}'. "
                    f"Locations: {secret_locations}. "
                    f"Remove secrets or use SecretDetectionMode.BEST_EFFORT to redact."
                )

    # Compute hash and serialize content based on kind
    import hashlib

    if kind == ArtifactKind.JSON:
        # Use canonical JSON serialization and hash
        content_hash = compute_hash(content)
        serialized = serialize_canonical(content)
        size_bytes = len(serialized)
    elif kind == ArtifactKind.TEXT:
        # Hash raw UTF-8 bytes directly (matches storage layer logic)
        if not isinstance(content, str):
            raise TypeError(f"TEXT artifact must be string, got {type(content)}")
        content_bytes = content.encode('utf-8')
        hash_digest = hashlib.sha256(content_bytes).hexdigest()
        content_hash = f"sha256:{hash_digest}"
        serialized = content
        size_bytes = len(content_bytes)
    else:
        # This should be caught by the earlier check, but just in case
        raise TypeError(f"Unsupported artifact kind: {kind}")

    # Determine content type
    if kind == ArtifactKind.JSON:
        content_type = "application/json"
    elif kind == ArtifactKind.TEXT:
        content_type = "text/plain"
    else:
        content_type = "application/octet-stream"

    # Generate unique artifact ID
    artifact_id = f"art_{uuid4().hex[:12]}"

    # Create ArtifactRef (uri will be populated by storage backend)
    artifact_ref = ArtifactRef(
        artifact_id=artifact_id,
        run_id=ctx.run_id,
        step_id=step_id,
        artifact_type=ArtifactType.INTERMEDIATE,  # Default, can be changed to OUTPUT
        artifact_kind=kind,
        uri="",  # Will be set by storage backend
        content_hash=content_hash,
        content_type=content_type,
        size_bytes=size_bytes,
        created_at=datetime.utcnow(),
    )

    # Get artifact storage from context (need to access it)
    # For now, we'll create an artifact storage instance tied to the run
    # In practice, this should be passed in or created once
    from pathlib import Path

    # Determine storage path from backend
    if hasattr(ctx.storage, "db_path"):
        # SQLite backend - use same directory for artifact storage
        db_path = Path(ctx.storage.db_path)
        artifact_storage_path = db_path.parent / "artifacts"
    else:
        # Default to .stardive/artifacts
        artifact_storage_path = Path.home() / ".stardive" / "artifacts"

    # Ensure directory exists
    artifact_storage_path.mkdir(parents=True, exist_ok=True)

    artifact_storage = SQLiteArtifactStorage(
        db_path=str(artifact_storage_path / "artifacts.db")
    )

    # Store artifact and get URI
    uri = artifact_storage.store_artifact(artifact_ref, content, kind)

    # Update artifact_ref with actual URI
    artifact_ref = ArtifactRef(
        artifact_id=artifact_id,
        run_id=ctx.run_id,
        step_id=step_id,
        artifact_type=ArtifactType.INTERMEDIATE,
        artifact_kind=kind,
        uri=uri,
        content_hash=content_hash,
        content_type=content_type,
        size_bytes=size_bytes,
        created_at=artifact_ref.created_at,
    )

    # Store artifact ref metadata in main database for verification
    ctx.storage.store_artifact_ref(artifact_ref)

    return artifact_ref


def emit_step_end(
    ctx: RunContext,
    step_id: str,
    outputs: Optional[Dict[str, ArtifactRef]] = None,
    status: StepStatus = StepStatus.SUCCESS,
    error: Optional[ErrorInfo] = None,
    attempt: int = 1,
) -> None:
    """
    Mark the completion of a step execution.

    Creates a StepEndEvent and stores it immediately. This should be called
    after step execution completes (success or failure).

    Args:
        ctx: RunContext from emit_run_start()
        step_id: Step identifier (must match emit_step_start())
        outputs: Output artifacts (name → ArtifactRef), must use ArtifactRef objects
        status: Step status (SUCCESS, FAILED, SKIPPED)
        error: Error information (required if status=FAILED)
        attempt: Attempt number for retries (default: 1)

    Examples:
        Successful step with outputs:
            result_artifact = emit_artifact(
                run_ctx,
                step_id="process",
                name="result",
                content={"score": 0.95},
                kind=ArtifactKind.JSON
            )

            emit_step_end(
                run_ctx,
                step_id="process",
                outputs={"result": result_artifact}
            )

        Failed step with error:
            emit_step_end(
                run_ctx,
                step_id="fetch",
                status=StepStatus.FAILED,
                error=ErrorInfo(
                    error_type="TimeoutError",
                    error_message="Request timed out after 30s"
                )
            )

        Skipped step (conditional logic):
            emit_step_end(
                run_ctx,
                step_id="optional_check",
                status=StepStatus.SKIPPED
            )

    Raises:
        TypeError: If outputs contains non-ArtifactRef values
        ValueError: If status=FAILED but error is None
        ValueError: If step was never started
        StorageError: If event storage fails
    """
    # Validate outputs are all ArtifactRef objects
    if outputs:
        for name, artifact in outputs.items():
            if not isinstance(artifact, ArtifactRef):
                raise TypeError(
                    f"Output '{name}' must be ArtifactRef, got {type(artifact)}. "
                    f"Use emit_artifact() to create ArtifactRef objects."
                )

    # Validate error is provided if status is FAILED
    if status == StepStatus.FAILED and error is None:
        raise ValueError("error must be provided when status=FAILED")

    # Find corresponding StepStartEvent to calculate duration
    step_start_event = None
    for event in ctx.builder._events:
        if isinstance(event, StepStartEvent) and event.step_id == step_id:
            step_start_event = event
            # Note: We take the LAST StepStartEvent for this step_id
            # (in case of retries, each attempt has its own start/end pair)

    if step_start_event is None:
        raise ValueError(
            f"Step '{step_id}' was never started. "
            f"Call emit_step_start() before emit_step_end()."
        )

    # Calculate duration
    timestamp = datetime.utcnow()
    duration_ms = (timestamp - step_start_event.timestamp).total_seconds() * 1000

    # Get previous event hash from builder
    previous_hash = ctx.builder._event_hashes[-1] if ctx.builder._event_hashes else None

    # Create temporary event for hash computation
    temp_event = StepEndEvent.model_construct(
        run_id=ctx.run_id,
        timestamp=timestamp,
        event_hash="sha256:" + "0" * 64,
        previous_hash=previous_hash,
        step_id=step_id,
        status=status,
        outputs=outputs or {},
        error=error,
        attempt=attempt,
        duration_ms=duration_ms,
    )

    # Compute hash for this event
    event_data = {
        "step_id": step_id,
        "status": status.value,
        "outputs": {k: v.model_dump(mode='json') for k, v in (outputs or {}).items()},
        "error": error.model_dump(mode='json') if error else None,
        "attempt": attempt,
        "duration_ms": duration_ms,
    }
    event_hash = compute_event_hash(
        event_id=temp_event.event_id,
        run_id=ctx.run_id,
        timestamp=timestamp,
        event_data=event_data,
        previous_hash=previous_hash,
    )

    # Create final event with computed hash
    step_end_event = StepEndEvent(
        run_id=ctx.run_id,
        timestamp=timestamp,
        event_hash=event_hash,
        previous_hash=previous_hash,
        step_id=step_id,
        status=status,
        outputs=outputs or {},
        error=error,
        attempt=attempt,
        duration_ms=duration_ms,
    )

    # Append to builder (validates hash chain)
    ctx.builder.append_event(step_end_event)

    # Store event immediately for audit integrity
    ctx.storage.store_event(step_end_event)


def emit_run_end(
    ctx: RunContext,
    status: RunStatus = RunStatus.COMPLETED,
    final_outputs: Optional[Dict[str, ArtifactRef]] = None,
) -> RunRecord:
    """
    Mark the completion of a run execution.

    Creates a RunEndEvent, stores it immediately, and builds the final
    immutable RunRecord from all events.

    Args:
        ctx: RunContext from emit_run_start()
        status: Final run status (COMPLETED, FAILED, BLOCKED)
        final_outputs: Final output artifacts (name → ArtifactRef)

    Returns:
        RunRecord: Immutable record of the complete execution

    Examples:
        Successful run:
            final_artifact = emit_artifact(
                run_ctx,
                step_id="final_step",
                name="report",
                content={"summary": "..."},
                kind=ArtifactKind.JSON
            )

            record = emit_run_end(
                run_ctx,
                final_outputs={"report": final_artifact}
            )

        Failed run:
            record = emit_run_end(
                run_ctx,
                status=RunStatus.FAILED
            )

    Raises:
        ValueError: If run has no events
        StorageError: If event storage fails
    """
    # Validate final_outputs are all ArtifactRef objects
    if final_outputs:
        for name, artifact in final_outputs.items():
            if not isinstance(artifact, ArtifactRef):
                raise TypeError(
                    f"Final output '{name}' must be ArtifactRef, got {type(artifact)}. "
                    f"Use emit_artifact() to create ArtifactRef objects."
                )

    # Ensure run has events
    if not ctx.builder._events:
        raise ValueError("Cannot end run with no events. Call emit_run_start() first.")

    # Calculate total duration from run start
    timestamp = datetime.utcnow()
    duration_ms = (timestamp - ctx.start_time).total_seconds() * 1000

    # Get previous event hash from builder
    previous_hash = ctx.builder._event_hashes[-1] if ctx.builder._event_hashes else None

    # Create temporary event for hash computation
    temp_event = RunEndEvent.model_construct(
        run_id=ctx.run_id,
        timestamp=timestamp,
        event_hash="sha256:" + "0" * 64,
        previous_hash=previous_hash,
        status=status,
        final_outputs=final_outputs or {},
        duration_ms=duration_ms,
    )

    # Compute hash for this event
    event_data = {
        "status": status.value,
        "final_outputs": {k: v.model_dump(mode='json') for k, v in (final_outputs or {}).items()},
        "duration_ms": duration_ms,
    }
    event_hash = compute_event_hash(
        event_id=temp_event.event_id,
        run_id=ctx.run_id,
        timestamp=timestamp,
        event_data=event_data,
        previous_hash=previous_hash,
    )

    # Create final event with computed hash
    run_end_event = RunEndEvent(
        run_id=ctx.run_id,
        timestamp=timestamp,
        event_hash=event_hash,
        previous_hash=previous_hash,
        status=status,
        final_outputs=final_outputs or {},
        duration_ms=duration_ms,
    )

    # Append to builder (validates hash chain)
    ctx.builder.append_event(run_end_event)

    # Store event immediately for audit integrity
    ctx.storage.store_event(run_end_event)

    # Build final immutable RunRecord
    record = ctx.builder.build()

    return record
