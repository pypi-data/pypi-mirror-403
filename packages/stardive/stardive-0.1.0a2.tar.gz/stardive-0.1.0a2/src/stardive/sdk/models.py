"""
SDK Models - Data structures for SDK-based workflow registration.

This module provides models for the SDK compiler infrastructure. These models
represent functions registered via decorators, context managers, or explicit API
before they're compiled into the canonical RunPlan IR.

Models:
- RegisteredStep: Metadata about a function registered as a workflow step

For canonical IR models, see: stardive.kernel.models
"""

from __future__ import annotations

from typing import Any, Callable, Dict

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# SDK Models
# ============================================================================


class RegisteredStep(BaseModel):
    """
    Metadata about a function registered as a workflow step.

    This is the intermediate representation between SDK registration
    (decorator/context/explicit) and canonical IR compilation (StepSpec).

    When a function is registered via @track.step() or similar, we capture:
    - The function itself (for introspection and execution)
    - User-specified metadata (step_id, step_type, config)
    - Source location (for provenance and auditability)

    Lifecycle:
        1. User registers function via SDK (decorator/context/API)
        2. RegisteredStep created with metadata
        3. Stored in StepRegistry
        4. SDKCompiler converts RegisteredStep → StepSpec
        5. StepSpec included in canonical RunPlan

    Attributes:
        step_id: Unique identifier for this step (user-specified)
        function: The actual Python function to execute
        step_type: Type of step (python, llm, sql, http, etc.)
        config: Step-specific configuration (model name, query, etc.)
        source_ref: Source code location in format "file.py:line"

    Examples:
        From decorator:
            @track.step("analyze", step_type="python")
            def analyze_data(data):
                return result

            # Creates:
            RegisteredStep(
                step_id="analyze",
                function=analyze_data,
                step_type="python",
                config={},
                source_ref="workflow.py:42"
            )

        From explicit API:
            sd.define_step(
                step_id="query_db",
                step_type="sql",
                function=run_query,
                config={"query": "SELECT * FROM users"}
            )

            # Creates:
            RegisteredStep(
                step_id="query_db",
                function=run_query,
                step_type="sql",
                config={"query": "SELECT * FROM users"},
                source_ref="workflow.py:87"
            )
    """

    step_id: str = Field(..., min_length=1, description="Unique step identifier")
    function: Callable = Field(..., description="Python function to execute")
    step_type: str = Field(..., min_length=1, description="Step type (python, llm, sql, http)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step-specific configuration")
    source_ref: str = Field(..., description="Source code location (file.py:line)")

    model_config = {
        "arbitrary_types_allowed": True,  # Allow Callable type
        "frozen": False,  # Mutable during registration (unlike RunPlan which is frozen)
    }

    @field_validator("function")
    @classmethod
    def validate_function_callable(cls, v: Any) -> Callable:
        """Validate that function is callable."""
        if not callable(v):
            raise ValueError(f"function must be callable, got {type(v).__name__}")
        return v


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "RegisteredStep",
]
