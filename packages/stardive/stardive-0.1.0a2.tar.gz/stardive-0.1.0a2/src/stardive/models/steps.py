"""
Step Models for Stardive Execution Kernel.

This module defines the StepSpec model, which represents the atomic unit of
execution in Stardive workflows. Steps are adapter-agnostic specifications
that can be executed by different adapters.

A step is the fundamental building block of a workflow:
- Has a unique ID within the workflow
- Has a type (llm, python, sql, http, human_approval, etc.)
- Contains configuration specific to that type
- References an executor (adapter) that knows how to run it

Key Principles:
1. **Adapter-Agnostic**: Same spec can be executed by different adapters
2. **Configuration**: Step-specific config in a flexible dict
3. **Dependencies**: Steps declare what they depend on
4. **Retry Semantics**: Built-in retry configuration
5. **Timeout Support**: Steps can have execution time limits

Design Philosophy:
    Steps are **specifications**, not **implementations**. The StepSpec
    describes WHAT to execute, while the adapter implements HOW to execute it.

    This separation enables:
    - Testing with mock adapters
    - Swapping implementations (e.g., OpenAI → Anthropic)
    - Adapter evolution without changing specs
    - Validation before execution

Adapter System:
    Each step type has one or more adapters that can execute it:

    | Step Type      | Adapter(s)                                  | Use Case              |
    |----------------|---------------------------------------------|-----------------------|
    | llm            | OpenAIAdapter, AnthropicAdapter             | AI model calls        |
    | python         | PythonAdapter                               | Python functions      |
    | sql            | PostgresAdapter, MySQLAdapter               | Database queries      |
    | http           | HTTPAdapter                                 | REST API calls        |
    | human_approval | ApprovalAdapter                             | Human-in-the-loop     |

    Adapters are referenced by module:class format:
    - "stardive.adapters.llm:OpenAIAdapter"
    - "stardive.adapters.python:PythonAdapter"

For detailed specifications, see:
- docs/canonical-ir.md - Step specification in canonical IR
- src/stardive/adapters/README.md - Adapter implementation guide
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Step Models
# ============================================================================


class StepSpec(BaseModel):
    """
    Specification for a single step in a workflow.

    A step is the atomic unit of execution in Stardive. Each step has:
    - A unique ID within the workflow
    - A type (llm, python, sql, human_approval, etc.)
    - Configuration specific to that step type
    - An executor (adapter) that knows how to run it

    Purpose:
        StepSpec is a **specification**, not an **implementation**. It describes
        WHAT should be executed, while adapters implement HOW to execute it.

        This separation enables:
        - **Adapter flexibility**: Same spec, different implementations
        - **Testing**: Mock adapters for testing without real execution
        - **Validation**: Validate specs before execution
        - **Evolution**: Change adapter implementations without changing specs

    Rationale:
        Steps are designed to be adapter-agnostic. For example, an LLM step
        can be executed by:
        - OpenAIAdapter (uses OpenAI API)
        - AnthropicAdapter (uses Anthropic API)
        - MockLLMAdapter (returns canned responses for testing)

        All adapters receive the same StepSpec and must honor its config.

    Lifecycle:
        1. Frontend (YAML/SDK) creates StepSpec
        2. Compiler validates StepSpec (dependencies, config)
        3. Kernel dispatches to appropriate adapter
        4. Adapter executes step using config
        5. Kernel records result in RunRecord

    Retry Semantics:
        Steps support built-in retry logic:
        - max_retries: Number of retry attempts
        - retry_delay_seconds: Delay between retries
        - Each retry is recorded as a new StepEndEvent with attempt number

        Example:
            Step fails on attempt 1, retries after 1s, succeeds on attempt 2
            → RunRecord contains 2 StepEndEvents (attempt=1, attempt=2)

    Timeout:
        Steps can have execution time limits:
        - timeout_seconds: Maximum execution time
        - If exceeded, step fails with timeout error
        - Timeout is enforced by kernel, not adapter

    Examples:
        LLM step (OpenAI GPT-4):
            StepSpec(
                step_id="analyze_credit",
                step_type="llm",
                config={
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                executor_ref="stardive.adapters.llm:OpenAIAdapter",
                depends_on=[],
                description="Analyze credit risk using GPT-4"
            )

        Python function:
            StepSpec(
                step_id="validate_data",
                step_type="python",
                config={
                    "function_ref": "validators:check_credit_data",
                    "timeout": 30
                },
                executor_ref="stardive.adapters.python:PythonAdapter",
                depends_on=["fetch_data"],
                max_retries=3,
                retry_delay_seconds=1.0
            )

        SQL query:
            StepSpec(
                step_id="fetch_user_data",
                step_type="sql",
                config={
                    "query": "SELECT * FROM users WHERE id = :user_id",
                    "params": {"user_id": "123"}
                },
                executor_ref="stardive.adapters.sql:PostgresAdapter",
                depends_on=[]
            )

        Human approval gate:
            StepSpec(
                step_id="approve_decision",
                step_type="human_approval",
                config={
                    "prompt": "Approve this credit decision?",
                    "approvers": ["manager@company.com"]
                },
                executor_ref="stardive.adapters.human:ApprovalAdapter",
                depends_on=["analyze_credit"],
                timeout_seconds=3600  # 1 hour timeout
            )

        HTTP API call with retry:
            StepSpec(
                step_id="fetch_credit_score",
                step_type="http",
                config={
                    "url": "https://api.example.com/credit-score",
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"}
                },
                executor_ref="stardive.adapters.http:HTTPAdapter",
                depends_on=[],
                max_retries=5,
                retry_delay_seconds=2.0,
                timeout_seconds=30.0
            )
    """

    step_id: str = Field(
        ...,
        description="Unique step identifier within the workflow",
        examples=["analyze", "validate", "approve"],
    )
    step_type: str = Field(
        ...,
        description="Type of step (determines which adapter to use)",
        examples=["llm", "python", "sql", "http", "human_approval"],
    )

    # Configuration
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific configuration (depends on step_type)",
    )

    # Executor
    executor_ref: str = Field(
        ...,
        description="Adapter module and class that can execute this step",
        examples=[
            "stardive.adapters.llm:OpenAIAdapter",
            "stardive.adapters.python:PythonAdapter",
        ],
    )

    # Dependencies (optional, can also be in RunPlan.dependencies)
    depends_on: List[str] = Field(
        default_factory=list,
        description="Step IDs that must complete before this step",
    )

    # Retry Configuration
    max_retries: int = Field(
        0, description="Maximum retry attempts on failure", ge=0
    )
    retry_delay_seconds: float = Field(
        1.0, description="Delay between retries", ge=0.0
    )

    # Timeout
    timeout_seconds: Optional[float] = Field(
        None, description="Step execution timeout", ge=0.0
    )

    # Metadata
    description: Optional[str] = Field(
        None, description="Human-readable description of what this step does"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization",
        examples=[["ml", "analysis"], ["data-validation"]],
    )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "StepSpec",
]
