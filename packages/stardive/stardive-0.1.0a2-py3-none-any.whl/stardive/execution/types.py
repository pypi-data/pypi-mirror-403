"""
Execution Types for Reference Execution API.

This module defines the core types for the single-step reference execution API.
These types enforce the hard boundaries of the reference executor:
- Single-step only (no multi-step chaining)
- Explicit consumes/produces (no inference)
- Deterministic error handling

Key Types:
- ExecutionResult: Immutable result of successful step execution
- ExecutionError: Structured error for execution failures
- StepFunction: Protocol for executable step functions

Design Principles:
1. **Explicit over Implicit**: All inputs/outputs declared upfront
2. **Single-Step Only**: API rejects multi-step operations by design
3. **Deterministic Errors**: Error types are explicit, not arbitrary exceptions
4. **Audit-Grade**: Every execution produces valid RunRecord events
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Union

from pydantic import BaseModel, Field

from stardive.models import ArtifactRef, ErrorInfo


# ============================================================================
# Execution Boundary Errors
# ============================================================================


class ExecutionErrorKind(str, Enum):
    """
    Enumeration of deterministic execution error types.

    These are the ONLY error types that execute_step() can produce.
    This ensures errors are predictable and auditable.
    """
    # Boundary violations (hard constraints)
    MULTI_STEP_REJECTED = "multi_step_rejected"  # Tried to execute multiple steps
    INVALID_CONTEXT = "invalid_context"  # RunContext is invalid or missing
    CONSUMES_MISMATCH = "consumes_mismatch"  # Declared consumes don't match inputs
    PRODUCES_MISMATCH = "produces_mismatch"  # Declared produces don't match outputs

    # Execution errors
    TIMEOUT = "timeout"  # Step exceeded timeout
    FUNCTION_ERROR = "function_error"  # Step function raised exception
    SERIALIZATION_ERROR = "serialization_error"  # Output not serializable
    SECRET_DETECTED = "secret_detected"  # Secrets in output (strict mode)

    # Artifact errors
    INVALID_INPUT_ARTIFACT = "invalid_input_artifact"  # Input artifact invalid/missing
    OUTPUT_CAPTURE_FAILED = "output_capture_failed"  # Failed to capture output as artifact


class ExecutionError(Exception):
    """
    Structured error for step execution failures.

    ExecutionError provides deterministic, auditable error information.
    Every execution failure produces an ExecutionError with:
    - kind: The specific error type (from ExecutionErrorKind)
    - message: Human-readable error description
    - details: Additional context (JSON-serializable)
    - original_exception: The underlying exception (if any)

    Design Decision:
        Using a structured error instead of arbitrary exceptions ensures:
        1. Errors are predictable (finite set of error types)
        2. Errors are auditable (can be stored in RunRecord)
        3. Errors are actionable (specific remediation per type)

    Examples:
        Timeout error:
            raise ExecutionError(
                kind=ExecutionErrorKind.TIMEOUT,
                message="Step 'analyze' exceeded timeout of 30 seconds",
                details={"timeout_seconds": 30, "elapsed_seconds": 35}
            )

        Multi-step rejection:
            raise ExecutionError(
                kind=ExecutionErrorKind.MULTI_STEP_REJECTED,
                message="execute_step() only executes single steps",
                details={"steps_requested": ["step_a", "step_b"]}
            )
    """

    def __init__(
        self,
        kind: ExecutionErrorKind,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.details = details or {}
        self.original_exception = original_exception

    def to_error_info(self) -> ErrorInfo:
        """
        Convert to ErrorInfo for storage in StepEndEvent.

        This allows the execution error to be recorded in the audit trail.
        """
        return ErrorInfo(
            error_type=self.kind.value,
            error_message=self.message,
            stack_trace=None,  # We don't store stack traces by default
            error_code=self.kind.value,
            context=self.details,  # ErrorInfo uses 'context' field
        )

    def __repr__(self) -> str:
        return (
            f"ExecutionError(kind={self.kind.value!r}, "
            f"message={self.message!r}, "
            f"details={self.details!r})"
        )


# ============================================================================
# Execution Result
# ============================================================================


class ExecutionResult(BaseModel):
    """
    Immutable result of successful step execution.

    ExecutionResult contains:
    - outputs: The produced artifacts (name -> ArtifactRef)
    - duration_ms: Execution time in milliseconds
    - step_id: The executed step identifier
    - run_id: The run this step belongs to

    Design Decision:
        ExecutionResult is immutable (frozen=True) to ensure:
        1. Results can't be modified after execution
        2. Results are safe to store and pass around
        3. Results match the immutability of ArtifactRef

    Examples:
        Successful execution:
            result = ExecutionResult(
                step_id="analyze",
                run_id="run_abc123",
                outputs={"prediction": artifact_ref},
                duration_ms=1234.5
            )
    """

    step_id: str = Field(..., description="Executed step identifier")
    run_id: str = Field(..., description="Run this step belongs to")
    outputs: Dict[str, ArtifactRef] = Field(
        default_factory=dict,
        description="Produced artifacts (name -> ArtifactRef)"
    )
    duration_ms: float = Field(..., description="Execution time in milliseconds", ge=0)
    executed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When step completed"
    )

    model_config = {"frozen": True}


# ============================================================================
# Step Function Protocol
# ============================================================================


# Type variable for step function return type
T = TypeVar("T")


class StepFunction(Protocol[T]):
    """
    Protocol for executable step functions.

    A step function must:
    1. Accept keyword arguments (inputs from artifacts)
    2. Return a JSON-serializable dict (outputs for artifacts)

    Design Decision:
        Using a Protocol allows any callable that matches this signature.
        No need for special decorators or base classes.

    Examples:
        Simple function:
            def add_numbers(a: int, b: int) -> dict:
                return {"sum": a + b}

        LLM call (stubbed):
            def analyze_text(text: str) -> dict:
                # LLM call would happen here
                return {"sentiment": "positive", "confidence": 0.95}
    """

    def __call__(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute the step with given inputs and return outputs."""
        ...


# ============================================================================
# Input/Output Specifications
# ============================================================================


class InputSpec(BaseModel):
    """
    Specification for a step input.

    Declares what artifact an input expects, enabling validation
    that consumes declarations match actual inputs.
    """

    name: str = Field(..., description="Input parameter name")
    artifact_ref: ArtifactRef = Field(..., description="Artifact providing this input")

    model_config = {"frozen": True}


class OutputSpec(BaseModel):
    """
    Specification for a step output.

    Declares what output a step will produce, enabling validation
    that produces declarations match actual outputs.
    """

    name: str = Field(..., description="Output name")
    kind: str = Field(
        default="json",
        description="Artifact kind (json, text, bytes, file)"
    )

    model_config = {"frozen": True}


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "ExecutionErrorKind",
    "ExecutionError",
    "ExecutionResult",
    "StepFunction",
    "InputSpec",
    "OutputSpec",
]
