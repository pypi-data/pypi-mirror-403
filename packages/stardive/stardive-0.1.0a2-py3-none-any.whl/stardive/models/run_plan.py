"""
RunPlan Model - Canonical Execution Intent for Stardive Kernel.

This module defines the RunPlan model, the core canonical representation of
execution intent in Stardive. All execution frontends (YAML workflows, Python SDK,
instrumentation hooks) compile to RunPlan.

RunPlan represents what *should* execute:
- **Immutable**: Once created, cannot be modified
- **Hashed**: Tamper-evident via plan_hash
- **Normalized**: Same logical workflow → same structure
- **Validated**: All dependencies resolved before execution

Key Principles:
1. **Single Source of Truth**: One canonical representation for all frontends
2. **Decoupling**: Frontends (YAML/SDK/Instrumentation) separate from execution
3. **Audit-Grade**: Every field supports compliance and legal requirements
4. **Provenance**: Captures who, where, and with what
5. **Validation**: Pre-execution validation prevents runtime errors

The Canonical IR Architecture:

    ┌─────────────────────────────────────────────┐
    │           Execution Frontends               │
    ├─────────────────────────────────────────────┤
    │  YAML Parser  │  SDK  │  Instrumentation    │
    │  (workflow.py)│(sdk/) │  (callbacks)        │
    └─────────────────────────────────────────────┘
                        │
                        │ All compile to
                        ▼
             ┌──────────────────────┐
             │   RunPlan (Intent)   │
             │  ─────────────────   │
             │  This module         │
             └──────────────────────┘
                        │
                        │ Drives execution
                        ▼
    ┌─────────────────────────────────────────────┐
    │          Execution Kernel                   │
    ├─────────────────────────────────────────────┤
    │  Executor  │  Adapters  │  RunRecord        │
    └─────────────────────────────────────────────┘

Compilation Examples:

    YAML Workflow:
        ```yaml
        version: "1.0"
        name: credit-check
        steps:
          - id: analyze
            type: llm
            model: gpt-4
        ```
        Compiles to RunPlan with steps={"analyze": StepSpec(...)}

    SDK Decorator:
        ```python
        @track.step("analyze")
        def analyze(data):
            return llm_call(data)
        ```
        Compiles to RunPlan with steps={"analyze": StepSpec(step_type="python")}

    Instrumentation (LangChain):
        LangChain events incrementally build RunPlan as steps execute.
        Initial RunPlan has empty steps={}, filled as events arrive.

Rationale:
    By having a single canonical IR:
    - **Simplified kernel**: One execution path, not N frontends
    - **Flexible frontends**: Add new frontends without changing kernel
    - **Consistent audit**: Same semantics regardless of input
    - **Lineage/replay**: Works uniformly across all frontends

For detailed specifications, see:
- docs/canonical-ir.md - Complete RunPlan specification
- docs/identity-provenance.md - Identity and provenance model
- docs/RUNPLAN_MODELS.md - Design rationale and examples
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_validator

from .artifacts import ArtifactSpec
from .enums import SourceType
from .identity import EnvironmentFingerprint, Identity
from .policy import PolicySpec
from .steps import StepSpec


# ============================================================================
# RunPlan (Execution Intent)
# ============================================================================


class RunPlan(BaseModel):
    """
    Canonical representation of execution intent.

    RunPlan is compiled from YAML workflows, SDK calls, or instrumentation events.
    It represents what *should* execute, normalized and validated, regardless of
    the input format.

    Purpose:
        RunPlan is the **single source of truth** for execution intent.
        All frontends compile to this canonical form, ensuring:
        - Consistent execution semantics
        - Uniform audit trails
        - Frontend-agnostic kernel
        - Replayable workflows

    Key Properties:
    ---------------
    1. **Immutable**: Once created, cannot be modified (frozen=True)
    2. **Hashed**: plan_hash enables tamper detection
    3. **Normalized**: Same logical workflow → same RunPlan structure
    4. **Validated**: All dependencies resolved, configs validated before execution

    Lifecycle:
    ----------
    1. **Frontend** (YAML/SDK/Instrumentation) → Compiler
    2. **Compiler** validates and creates RunPlan
    3. **plan_hash** is computed for integrity verification
    4. **Execution kernel** uses RunPlan to drive execution
    5. **RunRecord events** reference this RunPlan via run_id

    Compilation Modes:
    ------------------
    The source_type field indicates how the plan was created:

    | Source          | Build Time | Executor       | Use Case                  |
    |-----------------|------------|----------------|---------------------------|
    | YAML            | Before     | Kernel         | Complete workflows        |
    | SDK             | Before     | Kernel         | Single steps/partial      |
    | INSTRUMENTATION | During     | External       | Observer mode (LangChain) |

    Validation:
    -----------
    RunPlan includes validators that ensure:
    - All dependency references point to existing steps
    - All expected artifacts reference valid steps
    - No circular dependencies (future)
    - Step configurations are valid for their types (future)

    Audit Trail:
    ------------
    RunPlan captures complete provenance:
    - **Who**: initiator (Identity) - human or service account
    - **Where**: environment (EnvironmentFingerprint) - code, deps, infrastructure
    - **What**: steps (Dict[str, StepSpec]) - execution graph
    - **Policy**: policy (PolicySpec) - security and governance constraints
    - **When**: created_at - plan creation timestamp
    - **Source**: source_type, source_ref - where plan came from

    Examples:
    ---------
        YAML workflow (full execution):
            RunPlan(
                run_id="run_abc123",
                plan_hash="sha256:abc123...",
                initiator=Identity(
                    user_id="alice@company.com",
                    user_type=UserType.HUMAN,
                    auth_method=AuthMethod.OAUTH,
                    verified=True
                ),
                environment=EnvironmentFingerprint(
                    git_sha="abc123...",
                    dependencies_hash="sha256:def456...",
                    python_version="3.11.5",
                    os="Linux",
                    arch="x86_64",
                    fingerprint_hash="sha256:ghi789..."
                ),
                steps={
                    "analyze": StepSpec(
                        step_id="analyze",
                        step_type="llm",
                        config={"model": "gpt-4", "temperature": 0.7},
                        executor_ref="stardive.adapters.llm:OpenAIAdapter"
                    )
                },
                dependencies={"analyze": []},
                policy=PolicySpec(allow_network=True),
                source_type=SourceType.YAML,
                source_ref="/workflows/credit-check.yaml",
                name="credit-risk-analysis",
                version="1.0"
            )

        SDK single step:
            RunPlan(
                run_id="run_xyz789",
                plan_hash="sha256:xyz789...",
                initiator=Identity(
                    user_id="bob@company.com",
                    user_type=UserType.HUMAN,
                    auth_method=AuthMethod.API_KEY,
                    verified=True
                ),
                environment=EnvironmentFingerprint(...),
                steps={
                    "validate": StepSpec(
                        step_id="validate",
                        step_type="python",
                        config={"function_ref": "validators:check_data"},
                        executor_ref="stardive.adapters.python:PythonAdapter"
                    )
                },
                dependencies={},
                policy=PolicySpec(allow_code_execution=True),
                source_type=SourceType.SDK,
                source_ref="main.py:42"
            )

        Instrumentation mode (LangChain observer):
            RunPlan(
                run_id="run_lc456",
                plan_hash="sha256:lc456...",
                initiator=Identity(
                    user_type=UserType.SYSTEM,
                    service_id="langchain_agent",
                    auth_method=AuthMethod.NONE,
                    verified=False
                ),
                environment=EnvironmentFingerprint(...),
                steps={},  # Built incrementally as events arrive
                dependencies={},
                policy=PolicySpec(instrumentation_mode=True),
                source_type=SourceType.INSTRUMENTATION,
                source_ref="langchain://run_id_abc123"
            )
    """

    # ========================================================================
    # Core Identifiers
    # ========================================================================

    run_id: str = Field(
        default_factory=lambda: f"run_{uuid4().hex[:12]}",
        description="Unique execution identifier (globally unique)",
    )
    plan_hash: str = Field(
        ...,
        description="SHA256 hash of this plan for tamper detection",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )

    # ========================================================================
    # Identity & Provenance (Who, Where)
    # ========================================================================

    initiator: Identity = Field(
        ...,
        description="Identity of the entity that started this run (who)",
    )
    environment: EnvironmentFingerprint = Field(
        ...,
        description="Environment where this run executes (where)",
    )

    # ========================================================================
    # Execution Graph
    # ========================================================================

    steps: Dict[str, StepSpec] = Field(
        default_factory=dict,
        description="All steps in this workflow, keyed by step_id",
    )
    dependencies: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Dependency graph: {step_id: [depends_on_step_ids]}",
    )

    # ========================================================================
    # Policy & Governance
    # ========================================================================

    policy: PolicySpec = Field(
        default_factory=PolicySpec,
        description="Policy governing this execution (permits, gates, constraints)",
    )

    # ========================================================================
    # Expected Artifacts
    # ========================================================================

    expected_artifacts: List[ArtifactSpec] = Field(
        default_factory=list,
        description="Artifacts this workflow is expected to produce",
    )

    # ========================================================================
    # Metadata
    # ========================================================================

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this plan was created",
    )
    source_type: SourceType = Field(
        ...,
        description="How this plan was created (YAML, SDK, Instrumentation)",
    )
    source_ref: Optional[str] = Field(
        None,
        description="Reference to source (file path, code location, framework run ID)",
        examples=[
            "/path/to/workflow.yaml",
            "module.py:42",
            "langchain://run_lc456",
        ],
    )

    # Workflow Metadata
    name: Optional[str] = Field(
        None,
        description="Human-readable name for this workflow",
        examples=["credit-risk-analysis", "customer-onboarding"],
    )
    description: Optional[str] = Field(
        None, description="Description of what this workflow does"
    )
    version: Optional[str] = Field(
        None, description="Workflow version", examples=["1.0", "2.1.0"]
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and filtering",
    )

    # ========================================================================
    # Validation
    # ========================================================================

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(
        cls, v: Dict[str, List[str]], info
    ) -> Dict[str, List[str]]:
        """
        Validate that all dependency references point to existing steps.

        This prevents broken dependency graphs where a step depends on
        a non-existent step. Without this validation, execution would fail
        at runtime when trying to resolve dependencies.

        Validation Rules:
        1. Every key in dependencies must be a step_id in steps
        2. Every value (dependency) must be a step_id in steps
        3. No self-dependencies (step cannot depend on itself)

        Examples:
            Valid:
                steps = {"a": ..., "b": ...}
                dependencies = {"b": ["a"]}  # b depends on a ✓

            Invalid - references non-existent step:
                steps = {"a": ...}
                dependencies = {"a": ["b"]}  # b doesn't exist ✗

            Invalid - self-dependency:
                steps = {"a": ...}
                dependencies = {"a": ["a"]}  # circular ✗
        """
        steps = info.data.get("steps", {})
        for step_id, deps in v.items():
            if step_id not in steps:
                raise ValueError(
                    f"Dependency graph references non-existent step: {step_id}"
                )
            for dep in deps:
                if dep not in steps:
                    raise ValueError(
                        f"Step '{step_id}' depends on non-existent step '{dep}'"
                    )
                if dep == step_id:
                    raise ValueError(
                        f"Step '{step_id}' cannot depend on itself (self-dependency)"
                    )
        return v

    @field_validator("expected_artifacts")
    @classmethod
    def validate_expected_artifacts(
        cls, v: List[ArtifactSpec], info
    ) -> List[ArtifactSpec]:
        """
        Validate that expected artifacts reference existing steps.

        This ensures that artifact specifications are coherent with the
        workflow definition. If an artifact claims to be produced by step "X",
        step "X" must exist in the workflow.

        Validation Rules:
        1. Every ArtifactSpec.produced_by_step must be a step_id in steps

        Examples:
            Valid:
                steps = {"analyze": ...}
                expected_artifacts = [
                    ArtifactSpec(produced_by_step="analyze", ...)
                ]  ✓

            Invalid - references non-existent step:
                steps = {"analyze": ...}
                expected_artifacts = [
                    ArtifactSpec(produced_by_step="missing", ...)
                ]  ✗
        """
        steps = info.data.get("steps", {})
        for artifact in v:
            if artifact.produced_by_step not in steps:
                raise ValueError(
                    f"Expected artifact '{artifact.artifact_id}' references "
                    f"non-existent step '{artifact.produced_by_step}'"
                )
        return v

    # ========================================================================
    # Computed Properties
    # ========================================================================

    @computed_field
    @property
    def step_count(self) -> int:
        """
        Number of steps in this workflow.

        Useful for:
        - Quick workflow complexity assessment
        - Filtering workflows by size
        - Progress tracking (X of Y steps completed)
        """
        return len(self.steps)

    @computed_field
    @property
    def is_instrumentation_mode(self) -> bool:
        """
        Whether this is instrumentation mode (observer, not executor).

        Instrumentation mode means:
        - Stardive OBSERVES but doesn't EXECUTE
        - RunPlan built DURING execution (not before)
        - External framework (LangChain, OTEL) does actual execution
        - Stardive creates audit trail of what happened

        This enables zero-replacement integration with existing systems.
        """
        return self.policy.instrumentation_mode

    # ========================================================================
    # Configuration
    # ========================================================================

    model_config = {
        "frozen": True,  # Immutable after creation
        "json_schema_extra": {
            "examples": [
                {
                    "run_id": "run_abc123def456",
                    "plan_hash": "sha256:abc123...",
                    "initiator": {
                        "user_id": "alice@company.com",
                        "user_type": "human",
                        "auth_method": "oauth",
                        "verified": True,
                    },
                    "environment": {
                        "git_sha": "abc123def456789abcdef123456789abcdef1234",
                        "dependencies_hash": "sha256:def456...",
                        "python_version": "3.11.5",
                        "os": "Linux",
                        "os_version": "Ubuntu 22.04",
                        "arch": "x86_64",
                        "fingerprint_hash": "sha256:ghi789...",
                    },
                    "steps": {
                        "analyze": {
                            "step_id": "analyze",
                            "step_type": "llm",
                            "config": {"model": "gpt-4", "temperature": 0.7},
                            "executor_ref": "stardive.adapters.llm:OpenAIAdapter",
                        }
                    },
                    "dependencies": {"analyze": []},
                    "source_type": "yaml",
                    "source_ref": "/workflows/credit-check.yaml",
                    "name": "credit-risk-analysis",
                }
            ]
        },
    }


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "RunPlan",
]
