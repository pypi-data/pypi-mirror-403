"""
Reference Execution API for Stardive.

This module provides a single-step execution helper for demo and testing purposes.
It is NOT an orchestrator - it executes exactly one step with full audit-grade
event emission.

Key Functions:
- execute_step(): Execute a single step with RunContext

Key Types:
- ExecutionResult: Immutable result of successful execution
- ExecutionError: Structured error for execution failures
- ExecutionErrorKind: Enumeration of error types

CRITICAL BOUNDARIES:
1. execute_step() executes EXACTLY ONE step (multi-step rejected)
2. RunContext is REQUIRED (no global state)
3. consumes/produces must be DECLARED (no inference)
4. No scheduling, no retries, no dependency resolution

Usage Example:
    from stardive.instrumentation import emit_run_start
    from stardive.storage import SQLiteBackend
    from stardive.execution import execute_step

    # Create run context
    storage = SQLiteBackend(db_path="audit.db")
    ctx = emit_run_start(storage=storage, initiator={"user_id": "alice"})

    # Define step function
    def analyze(data: ArtifactRef) -> dict:
        # Process data...
        return {"result": "analysis complete"}

    # Execute single step
    result = execute_step(
        ctx=ctx,
        step_id="analyze",
        func=analyze,
        inputs={"data": data_artifact},
        consumes=["data"],
        produces=["result"]
    )

    # result.outputs["result"] is an ArtifactRef
"""

from .execute import execute_step
from .types import (
    ExecutionError,
    ExecutionErrorKind,
    ExecutionResult,
    InputSpec,
    OutputSpec,
    StepFunction,
)

__all__ = [
    # Core function
    "execute_step",
    # Result types
    "ExecutionResult",
    # Error types
    "ExecutionError",
    "ExecutionErrorKind",
    # Specification types
    "InputSpec",
    "OutputSpec",
    "StepFunction",
]
