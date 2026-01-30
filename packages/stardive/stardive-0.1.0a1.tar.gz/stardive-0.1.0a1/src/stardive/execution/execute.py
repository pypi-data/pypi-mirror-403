"""
Reference Execution API - Single-Step Demo Helper.

This module provides the execute_step() function for executing a single step
with full audit-grade event emission. This is a DEMO HELPER, not an orchestrator.

CRITICAL BOUNDARIES (Non-Negotiable):
1. execute_step() executes EXACTLY ONE step
2. RunContext is REQUIRED (no global state)
3. consumes/produces must be DECLARED (no inference)
4. No scheduling, no retries, no dependency resolution
5. Events are emitted immediately (step_start -> artifacts -> step_end)

This is NOT:
- An orchestrator (doesn't chain steps)
- A scheduler (doesn't plan execution)
- A retry system (single attempt only)
- An inference engine (no auto-dependency detection)

Use Cases:
- Demo applications showing Stardive instrumentation
- Testing step functions with audit trails
- Single-step execution in notebooks/scripts

For multi-step workflows, use the SDK (StardiveContext) or instrumentation API directly.
"""

from __future__ import annotations

import signal
import traceback
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from stardive.artifacts import ArtifactKind, SecretDetectionMode
from stardive.instrumentation import (
    RunContext,
    emit_artifact,
    emit_step_end,
    emit_step_start,
)
from stardive.models import ArtifactRef, ModelIdentity, StepStatus, ToolIdentity

from .types import (
    ExecutionError,
    ExecutionErrorKind,
    ExecutionResult,
)


# ============================================================================
# Timeout Context Manager
# ============================================================================


class TimeoutError(ExecutionError):
    """Timeout error with ExecutionError interface."""

    def __init__(self, timeout_seconds: float, step_id: str):
        super().__init__(
            kind=ExecutionErrorKind.TIMEOUT,
            message=f"Step '{step_id}' exceeded timeout of {timeout_seconds} seconds",
            details={"timeout_seconds": timeout_seconds, "step_id": step_id},
        )


def _timeout_handler(signum: int, frame: Any) -> None:
    """Signal handler for timeout."""
    raise TimeoutError(timeout_seconds=0, step_id="unknown")


@contextmanager
def _timeout_context(timeout_seconds: Optional[float], step_id: str):
    """
    Context manager for execution timeout.

    Uses SIGALRM on Unix systems for timeout enforcement.
    On Windows, timeout is best-effort (no signal support).

    Args:
        timeout_seconds: Maximum execution time (None = no timeout)
        step_id: Step identifier for error messages
    """
    if timeout_seconds is None or timeout_seconds <= 0:
        yield
        return

    # Store old handler
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)

    try:
        # Set alarm (integer seconds)
        signal.alarm(int(timeout_seconds))
        yield
    except TimeoutError:
        # Re-raise with correct details
        raise TimeoutError(timeout_seconds=timeout_seconds, step_id=step_id)
    finally:
        # Cancel alarm and restore handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# ============================================================================
# Validation Functions
# ============================================================================


def _validate_context(ctx: Optional[RunContext]) -> None:
    """
    Validate that RunContext is provided and valid.

    Raises ExecutionError if context is invalid.
    """
    if ctx is None:
        raise ExecutionError(
            kind=ExecutionErrorKind.INVALID_CONTEXT,
            message="RunContext is required. Use emit_run_start() to create one.",
            details={"context_provided": False},
        )

    if not hasattr(ctx, "run_id") or not ctx.run_id:
        raise ExecutionError(
            kind=ExecutionErrorKind.INVALID_CONTEXT,
            message="RunContext has no run_id. Context may be corrupted.",
            details={"context_type": type(ctx).__name__},
        )


def _validate_single_step(step_id: str, step_ids: Optional[List[str]] = None) -> None:
    """
    Validate that only a single step is being executed.

    This enforces the hard boundary: execute_step() is single-step only.

    Raises ExecutionError if multi-step execution is attempted.
    """
    if step_ids is not None and len(step_ids) > 1:
        raise ExecutionError(
            kind=ExecutionErrorKind.MULTI_STEP_REJECTED,
            message=(
                "execute_step() only executes single steps. "
                f"Got {len(step_ids)} steps: {step_ids}. "
                "Use the SDK or instrumentation API for multi-step workflows."
            ),
            details={"steps_requested": step_ids},
        )


def _validate_consumes(
    consumes: Optional[List[str]],
    inputs: Optional[Dict[str, ArtifactRef]],
) -> None:
    """
    Validate that declared consumes match provided inputs.

    If consumes is declared, inputs must match exactly.
    No inference - user must declare what they consume.

    Raises ExecutionError if mismatch detected.
    """
    if consumes is None:
        # No declaration = no validation (but user should declare)
        return

    consumes_set = set(consumes)
    inputs_set = set(inputs.keys()) if inputs else set()

    if consumes_set != inputs_set:
        missing = consumes_set - inputs_set
        extra = inputs_set - consumes_set
        raise ExecutionError(
            kind=ExecutionErrorKind.CONSUMES_MISMATCH,
            message=(
                f"Declared consumes don't match inputs. "
                f"Missing: {list(missing) if missing else 'none'}. "
                f"Extra: {list(extra) if extra else 'none'}."
            ),
            details={
                "declared_consumes": list(consumes),
                "provided_inputs": list(inputs.keys()) if inputs else [],
                "missing": list(missing),
                "extra": list(extra),
            },
        )


def _validate_produces(
    produces: Optional[List[str]],
    outputs: Dict[str, Any],
) -> None:
    """
    Validate that declared produces match actual outputs.

    If produces is declared, outputs must match exactly.
    No inference - user must declare what they produce.

    Raises ExecutionError if mismatch detected.
    """
    if produces is None:
        # No declaration = no validation (but user should declare)
        return

    produces_set = set(produces)
    outputs_set = set(outputs.keys())

    if produces_set != outputs_set:
        missing = produces_set - outputs_set
        extra = outputs_set - produces_set
        raise ExecutionError(
            kind=ExecutionErrorKind.PRODUCES_MISMATCH,
            message=(
                f"Declared produces don't match outputs. "
                f"Missing: {list(missing) if missing else 'none'}. "
                f"Extra: {list(extra) if extra else 'none'}."
            ),
            details={
                "declared_produces": list(produces),
                "actual_outputs": list(outputs.keys()),
                "missing": list(missing),
                "extra": list(extra),
            },
        )


def _validate_inputs(inputs: Optional[Dict[str, ArtifactRef]]) -> None:
    """
    Validate that all inputs are valid ArtifactRef objects.

    Raises ExecutionError if any input is invalid.
    """
    if not inputs:
        return

    for name, artifact in inputs.items():
        if not isinstance(artifact, ArtifactRef):
            raise ExecutionError(
                kind=ExecutionErrorKind.INVALID_INPUT_ARTIFACT,
                message=(
                    f"Input '{name}' must be ArtifactRef, got {type(artifact).__name__}. "
                    f"Use emit_artifact() to create ArtifactRef objects."
                ),
                details={"input_name": name, "input_type": type(artifact).__name__},
            )


# ============================================================================
# Core Execution Function
# ============================================================================


def execute_step(
    ctx: RunContext,
    step_id: str,
    func: Callable[..., Dict[str, Any]],
    inputs: Optional[Dict[str, ArtifactRef]] = None,
    consumes: Optional[List[str]] = None,
    produces: Optional[List[str]] = None,
    model_identity: Optional[ModelIdentity] = None,
    tool_identity: Optional[ToolIdentity] = None,
    timeout_seconds: Optional[float] = None,
    secret_detection_mode: SecretDetectionMode = SecretDetectionMode.BEST_EFFORT,
) -> ExecutionResult:
    """
    Execute a single step with full audit-grade event emission.

    This is a DEMO HELPER for single-step execution. It is NOT an orchestrator.

    CRITICAL BOUNDARIES:
    - Executes EXACTLY ONE step (multi-step rejected)
    - RunContext is REQUIRED (no global state)
    - consumes/produces must be DECLARED (no inference)
    - No scheduling, no retries, no dependency resolution
    - Timeout is caller's responsibility (pass timeout_seconds)

    Event Emission:
        execute_step() emits the following events in order:
        1. StepStartEvent (with inputs)
        2. ArtifactRef creation for each output
        3. StepEndEvent (with outputs, status)

        All events are stored immediately via ctx.storage.

    Args:
        ctx: RunContext from emit_run_start() - REQUIRED
        step_id: Unique identifier for this step
        func: Callable that takes **kwargs and returns Dict[str, Any]
        inputs: Input artifacts (name -> ArtifactRef)
        consumes: Expected input names (for validation)
        produces: Expected output names (for validation)
        model_identity: Model identity for LLM steps
        tool_identity: Tool identity for non-LLM steps
        timeout_seconds: Maximum execution time (None = no timeout)
        secret_detection_mode: How to handle secrets in outputs

    Returns:
        ExecutionResult: Immutable result with outputs and metadata

    Raises:
        ExecutionError: For all execution failures (deterministic)

    Examples:
        Basic function execution:
            from stardive.instrumentation import emit_run_start
            from stardive.storage import SQLiteBackend
            from stardive.execution import execute_step

            storage = SQLiteBackend(db_path="audit.db")
            ctx = emit_run_start(storage=storage, initiator={"user_id": "alice"})

            def add_numbers(a: int, b: int) -> dict:
                return {"sum": a + b}

            result = execute_step(
                ctx=ctx,
                step_id="compute",
                func=add_numbers,
                inputs={"a": artifact_a, "b": artifact_b},
                consumes=["a", "b"],
                produces=["sum"]
            )

        With timeout:
            result = execute_step(
                ctx=ctx,
                step_id="slow_task",
                func=slow_function,
                timeout_seconds=30.0
            )

        LLM step (stubbed):
            result = execute_step(
                ctx=ctx,
                step_id="analyze",
                func=llm_analyze,
                model_identity=ModelIdentity(
                    provider="openai",
                    model_name="gpt-4",
                    temperature=0.7
                )
            )
    """
    # ========================================================================
    # Phase 1: Validation (before any execution)
    # ========================================================================

    # 1. Validate context is provided and valid
    _validate_context(ctx)

    # 2. Validate single-step constraint
    _validate_single_step(step_id)

    # 3. Validate inputs are valid ArtifactRef objects
    _validate_inputs(inputs)

    # 4. Validate consumes declaration matches inputs
    _validate_consumes(consumes, inputs)

    # ========================================================================
    # Phase 2: Event Emission - StepStartEvent
    # ========================================================================

    start_time = datetime.utcnow()

    # Emit step start event
    emit_step_start(
        ctx=ctx,
        step_id=step_id,
        inputs=inputs,
        model_identity=model_identity,
        tool_identity=tool_identity,
    )

    # ========================================================================
    # Phase 3: Execute Function
    # ========================================================================

    try:
        # Prepare function arguments from input artifacts
        # Note: For demo purposes, we pass the artifact refs directly
        # In a full implementation, we'd load artifact content
        func_kwargs = {}
        if inputs:
            for name, artifact_ref in inputs.items():
                # Pass artifact ref as-is (function can extract content if needed)
                func_kwargs[name] = artifact_ref

        # Execute with optional timeout
        with _timeout_context(timeout_seconds, step_id):
            raw_outputs = func(**func_kwargs)

        # Validate outputs is a dict
        if not isinstance(raw_outputs, dict):
            raise ExecutionError(
                kind=ExecutionErrorKind.FUNCTION_ERROR,
                message=(
                    f"Step function must return dict, got {type(raw_outputs).__name__}. "
                    f"Ensure your function returns a dict of outputs."
                ),
                details={"return_type": type(raw_outputs).__name__},
            )

    except ExecutionError:
        # Re-raise execution errors as-is
        raise

    except TimeoutError as e:
        # Handle timeout (from signal)
        error = ExecutionError(
            kind=ExecutionErrorKind.TIMEOUT,
            message=f"Step '{step_id}' exceeded timeout of {timeout_seconds} seconds",
            details={"timeout_seconds": timeout_seconds, "step_id": step_id},
            original_exception=e,
        )

        # Emit step end with failure
        emit_step_end(
            ctx=ctx,
            step_id=step_id,
            status=StepStatus.FAILED,
            error=error.to_error_info(),
        )

        raise error

    except Exception as e:
        # Wrap arbitrary exceptions
        error = ExecutionError(
            kind=ExecutionErrorKind.FUNCTION_ERROR,
            message=f"Step '{step_id}' raised exception: {type(e).__name__}: {str(e)}",
            details={
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "traceback": traceback.format_exc(),
            },
            original_exception=e,
        )

        # Emit step end with failure
        emit_step_end(
            ctx=ctx,
            step_id=step_id,
            status=StepStatus.FAILED,
            error=error.to_error_info(),
        )

        raise error

    # ========================================================================
    # Phase 4: Validate Produces Declaration
    # ========================================================================

    _validate_produces(produces, raw_outputs)

    # ========================================================================
    # Phase 5: Capture Outputs as Artifacts
    # ========================================================================

    output_artifacts: Dict[str, ArtifactRef] = {}

    try:
        for name, value in raw_outputs.items():
            # Determine artifact kind based on value type
            if isinstance(value, str):
                kind = ArtifactKind.TEXT
            else:
                kind = ArtifactKind.JSON

            # Emit artifact with secret detection
            artifact_ref = emit_artifact(
                ctx=ctx,
                step_id=step_id,
                name=name,
                content=value,
                kind=kind,
                secret_detection_mode=secret_detection_mode,
            )

            output_artifacts[name] = artifact_ref

    except Exception as e:
        # Wrap artifact capture errors
        error = ExecutionError(
            kind=ExecutionErrorKind.OUTPUT_CAPTURE_FAILED,
            message=f"Failed to capture output '{name}': {type(e).__name__}: {str(e)}",
            details={
                "output_name": name,
                "exception_type": type(e).__name__,
                "exception_message": str(e),
            },
            original_exception=e,
        )

        # Emit step end with failure
        emit_step_end(
            ctx=ctx,
            step_id=step_id,
            status=StepStatus.FAILED,
            error=error.to_error_info(),
        )

        raise error

    # ========================================================================
    # Phase 6: Event Emission - StepEndEvent
    # ========================================================================

    end_time = datetime.utcnow()
    duration_ms = (end_time - start_time).total_seconds() * 1000

    # Emit step end event with success
    emit_step_end(
        ctx=ctx,
        step_id=step_id,
        outputs=output_artifacts,
        status=StepStatus.SUCCESS,
    )

    # ========================================================================
    # Phase 7: Return Result
    # ========================================================================

    return ExecutionResult(
        step_id=step_id,
        run_id=ctx.run_id,
        outputs=output_artifacts,
        duration_ms=duration_ms,
        executed_at=end_time,
    )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "execute_step",
    "ExecutionError",
    "ExecutionErrorKind",
    "ExecutionResult",
    "TimeoutError",
]
