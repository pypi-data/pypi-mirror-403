"""
Policy Models for Stardive Execution Kernel.

This module defines the PolicySpec model, which declares security policies,
access controls, and governance constraints for workflow execution.

Policies control:
- **Network access**: What domains/APIs can be accessed
- **Code execution**: What code/modules can be executed
- **File access**: What paths can be read/written
- **Human gates**: When human approval is required
- **Resource limits**: Execution time and memory constraints
- **Instrumentation mode**: Observer vs. executor behavior

Key Principles:
1. **Policy as Data**: Policies are data models, not code (declarative)
2. **Audit-First**: Record policies even if enforcement comes later
3. **Defense in Depth**: Multiple policy layers (network, code, data)
4. **Least Privilege**: Default deny, explicit allow
5. **Instrumentation Support**: Special mode for observation without execution

Implementation Status:
    Phase 2 (Current): Data model only, policies are recorded but NOT enforced
    Phase 3: Basic enforcement (timeouts, resource limits)
    Phase 4+: Full enforcement (network filtering, code sandboxing)

Rationale:
    Even without enforcement, recording policies provides value:
    - **Retroactive analysis**: What policies were in effect?
    - **Compliance planning**: What policies do we need?
    - **Audit evidence**: Show what constraints were intended
    - **Incremental rollout**: Record first, enforce later

Design Philosophy:
    Policies are **intent declarations**, not **implementation**.
    - They declare what SHOULD be enforced
    - Enforcement is implemented separately in the kernel
    - This allows:
      - Policies defined before enforcement exists
      - Different enforcement strategies (strict, permissive, audit-only)
      - Policy evolution without breaking existing workflows

For detailed specifications, see:
- docs/canonical-ir.md - Policy specification in RunPlan
- docs/IMPLEMENTATION_PRIORITIES.md - Policy enforcement roadmap
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Policy Models
# ============================================================================


class PolicySpec(BaseModel):
    """
    Policy specification for a run (permits, gates, constraints).

    Policies declare security and governance constraints for workflow execution.
    They control what workflows can do and require (network access, code
    execution, approvals, resource limits).

    Purpose:
        For audit-grade and regulated environments, we must:
        - **Declare** what workflows are allowed to do
        - **Record** what policies were in effect
        - **Enforce** policies during execution (future)
        - **Audit** whether policies were followed

        PolicySpec provides the declarative foundation for all of this.

    Implementation Status:
        **Phase 2 (Current)**: Data model only
        - Policies are recorded in RunPlan
        - NOT enforced during execution
        - Enables audit trail of intended policies

        **Phase 3**: Basic enforcement
        - Timeouts enforced
        - Resource limits enforced
        - Human approval gates enforced

        **Phase 4+**: Full enforcement
        - Network filtering (allowed_domains)
        - Code sandboxing (allowed_modules, allowed_paths)
        - Advanced resource controls

    Rationale:
        Why record policies before enforcement?
        1. **Audit first**: Establish what SHOULD be enforced
        2. **Incremental rollout**: Record → Warn → Enforce
        3. **Compliance**: Show intent even if enforcement incomplete
        4. **Analysis**: Understand what policies are needed

    Policy Categories:
        1. **Network Access**: Control external API/service access
        2. **Code Execution**: Control what code can be executed
        3. **Data Access**: Control file system access
        4. **Human Gates**: Require human approval at checkpoints
        5. **Resource Limits**: Prevent runaway executions
        6. **Instrumentation Mode**: Observer vs. executor behavior

    Examples:
        Permissive policy (development):
            PolicySpec(
                allow_network=True,
                allow_code_execution=True,
                allow_file_access=True,
                require_approval=False
            )

        Restrictive policy (production):
            PolicySpec(
                allow_network=True,
                allowed_domains=["api.openai.com", "api.anthropic.com"],
                allow_code_execution=True,
                allowed_modules=["validators", "processors"],
                allow_file_access=True,
                allowed_paths=["/data/inputs", "/data/outputs"],
                require_approval=True,
                approval_timeout_seconds=3600,
                max_execution_time_seconds=300,
                max_memory_mb=2048
            )

        Instrumentation mode (observer):
            PolicySpec(
                instrumentation_mode=True,
                allow_network=False,  # Observing, not executing
                allow_code_execution=False,
                allow_file_access=False
            )

        High-security with strict limits:
            PolicySpec(
                allow_network=True,
                allowed_domains=["internal-api.company.com"],
                allow_code_execution=False,  # No arbitrary code
                allow_file_access=True,
                allowed_paths=["/data/secure"],
                require_approval=True,
                approval_timeout_seconds=1800,
                max_execution_time_seconds=60,
                max_memory_mb=512
            )
    """

    # ========================================================================
    # Network Access Control
    # ========================================================================

    allow_network: bool = Field(
        True, description="Whether network access is allowed"
    )
    allowed_domains: List[str] = Field(
        default_factory=list,
        description="Allowed domains for network access (empty = all)",
    )

    # ========================================================================
    # Code Execution Control
    # ========================================================================

    allow_code_execution: bool = Field(
        True, description="Whether arbitrary code execution is allowed"
    )
    allowed_modules: List[str] = Field(
        default_factory=list,
        description="Allowed Python modules (empty = all)",
    )

    # ========================================================================
    # Data Access Control
    # ========================================================================

    allow_file_access: bool = Field(
        True, description="Whether file I/O is allowed"
    )
    allowed_paths: List[str] = Field(
        default_factory=list,
        description="Allowed file paths (empty = all)",
    )

    # ========================================================================
    # Human-in-the-Loop Gates
    # ========================================================================

    require_approval: bool = Field(
        False, description="Whether human approval is required before execution"
    )
    approval_timeout_seconds: Optional[float] = Field(
        None, description="Timeout for approval requests"
    )

    # ========================================================================
    # Resource Constraints
    # ========================================================================

    max_execution_time_seconds: Optional[float] = Field(
        None, description="Maximum total execution time"
    )
    max_memory_mb: Optional[int] = Field(
        None, description="Maximum memory usage in MB"
    )

    # ========================================================================
    # Instrumentation Mode
    # ========================================================================

    instrumentation_mode: bool = Field(
        False,
        description="Whether this is instrumentation mode (observer, not executor)",
    )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "PolicySpec",
]
