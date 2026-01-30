"""
Enumeration types for Stardive Execution Kernel.

This module defines all enumeration types used throughout the Stardive kernel for
type-safe representation of execution states, sources, and configurations.

Enumerations provide:
- Type safety and IDE autocomplete
- Clear valid values for fields
- Self-documenting code
- Prevention of invalid values

Organization:
- Execution Enums: SourceType, StepStatus, RunStatus
- Identity Enums: UserType, AuthMethod
- Artifact Enums: ArtifactType
- Security Enums: SecretSource
- Replay Enums: ReplayStrategy

For usage in models, see:
- identity.py - Uses UserType, AuthMethod
- artifacts.py - Uses ArtifactType
- run_plan.py - Uses SourceType, StepStatus, RunStatus
"""

from enum import Enum


# ============================================================================
# Execution Enums
# ============================================================================


class SourceType(str, Enum):
    """
    How an execution plan was created.

    This distinguishes between different frontends that compile to RunPlan:
    - YAML: Declarative workflow files
    - SDK: Python decorator or context manager
    - INSTRUMENTATION: Observer mode for external frameworks

    The source type affects how the RunPlan is built:
    - YAML/SDK: Plan is built BEFORE execution
    - INSTRUMENTATION: Plan is built DURING execution (incremental)
    """

    YAML = "yaml"  # From YAML workflow file
    SDK = "sdk"  # From Python SDK decorator/context manager
    INSTRUMENTATION = "instrumentation"  # From external framework (LangChain, OTEL)


class StepStatus(str, Enum):
    """
    Execution status of an individual step.

    State Machine:
        PENDING → RUNNING → (SUCCESS | FAILED | SKIPPED)

    Status Meanings:
    - PENDING: Step has not started yet (waiting on dependencies)
    - RUNNING: Step is currently executing
    - SUCCESS: Step completed successfully
    - FAILED: Step failed with an error
    - SKIPPED: Step was skipped (conditional, dependency failed, etc.)

    Used in:
    - StepEndEvent to record final step status
    - RunRecord to track step-by-step progress
    """

    PENDING = "pending"  # Not yet started
    RUNNING = "running"  # Currently executing
    SUCCESS = "success"  # Completed successfully
    FAILED = "failed"  # Failed with error
    SKIPPED = "skipped"  # Skipped due to conditions


class RunStatus(str, Enum):
    """
    Overall execution status of a run.

    Represents the aggregate status of all steps in a workflow.

    State Machine:
        RUNNING → (COMPLETED | FAILED | BLOCKED)

    Status Meanings:
    - RUNNING: Execution in progress (one or more steps running)
    - COMPLETED: All steps completed successfully
    - FAILED: One or more steps failed
    - BLOCKED: Execution blocked by policy or approval gate

    Run Status Derivation:
    - If any step is BLOCKED → Run is BLOCKED
    - If any step is FAILED → Run is FAILED
    - If all steps are SUCCESS → Run is COMPLETED
    - Otherwise → Run is RUNNING

    Used in:
    - RunRecord to track overall execution status
    - RunEndEvent to record final run outcome
    """

    RUNNING = "running"  # Execution in progress
    COMPLETED = "completed"  # All steps completed successfully
    FAILED = "failed"  # One or more steps failed
    BLOCKED = "blocked"  # Blocked by policy or approval gate


# ============================================================================
# Identity & Authentication Enums
# ============================================================================


class UserType(str, Enum):
    """
    Type of entity initiating an execution.

    This distinguishes between human users, service accounts, and system processes
    for audit trail purposes.

    Type Meanings:
    - HUMAN: Human user via CLI, UI, or interactive session
    - SERVICE: Service account or automated system (CI/CD, cron job)
    - SYSTEM: Internal system process (kernel, scheduler)

    Audit Implications:
    - HUMAN: May require approval workflows, MFA verification
    - SERVICE: Requires service account authorization
    - SYSTEM: Internal processes, typically pre-authorized

    Used in:
    - Identity model to categorize initiators
    - Audit logs to distinguish human vs. automated actions
    """

    HUMAN = "human"  # Human user via CLI/UI
    SERVICE = "service"  # Service account or automated system
    SYSTEM = "system"  # Internal system process


class AuthMethod(str, Enum):
    """
    Authentication method used to verify an identity.

    This records HOW an identity was verified for audit purposes.

    Method Meanings:
    - API_KEY: API key authentication (HMAC signature verification)
    - OAUTH: OAuth 2.0 token (JWT verification)
    - CERT: X.509 certificate chain validation
    - NONE: No authentication (development/testing only, not for production)

    Security Implications:
    - API_KEY: Moderate security, shared secrets
    - OAUTH: High security, token-based, supports MFA
    - CERT: Highest security, cryptographic proof
    - NONE: Insecure, dev/test only

    Used in:
    - Identity model to record authentication method
    - Audit logs for security analysis
    - Policy decisions (e.g., require CERT for production)
    """

    API_KEY = "api_key"
    OAUTH = "oauth"
    CERT = "cert"  # X.509 certificate
    NONE = "none"  # No authentication (dev/testing only)


# ============================================================================
# Artifact Enums
# ============================================================================


class ArtifactType(str, Enum):
    """
    Type of artifact in the execution flow.

    Artifacts are data inputs, outputs, or intermediate results produced
    during workflow execution.

    Type Meanings:
    - INPUT: Data provided as input to a step
    - OUTPUT: Final output from a step
    - INTERMEDIATE: Temporary data between steps (may be garbage collected)

    Lifecycle Implications:
    - INPUT: Immutable, retained for audit/replay
    - OUTPUT: Immutable, retained for audit/replay, lineage tracking
    - INTERMEDIATE: May be pruned after workflow completion (configurable)

    Used in:
    - ArtifactRef to categorize artifacts
    - Lineage graph to distinguish input/output relationships
    - Storage policies (retention, garbage collection)
    """

    INPUT = "input"  # Input to a step
    OUTPUT = "output"  # Output from a step
    INTERMEDIATE = "intermediate"  # Temporary artifact between steps


# ============================================================================
# Security Enums
# ============================================================================


class SecretSource(str, Enum):
    """
    Source of secret values (API keys, passwords, tokens).

    This records WHERE secrets are stored, not the secrets themselves.
    Actual secret values are NEVER persisted in audit trails.

    Source Types:
    - ENV: Environment variable
    - FILE: File on disk (e.g., ~/.stardive/secrets)
    - VAULT: HashiCorp Vault
    - AWS_SECRETS: AWS Secrets Manager
    - GCP_SECRETS: GCP Secret Manager
    - AZURE_KEYVAULT: Azure Key Vault

    Audit Implications:
    - Records secret provenance for compliance
    - Enables rotation tracking
    - Supports multi-cloud deployments

    Security Note:
        The SecretRef model only stores the secret_id (name) and source,
        never the actual secret value. This provides audit trail without
        compromising security.

    Used in:
    - SecretRef to record where secrets are stored
    - Secret management logic to retrieve values at runtime
    """

    ENV = "env"  # Environment variable
    FILE = "file"  # File on disk
    VAULT = "vault"  # HashiCorp Vault
    AWS_SECRETS = "aws_secrets"  # AWS Secrets Manager
    GCP_SECRETS = "gcp_secrets"  # GCP Secret Manager
    AZURE_KEYVAULT = "azure_keyvault"  # Azure Key Vault


# ============================================================================
# Replay Enums
# ============================================================================


class ReplayStrategy(str, Enum):
    """
    Strategy for replaying non-deterministic steps.

    AI/LLM steps are often non-deterministic (temperature > 0, no seed).
    This enum defines how to handle replay for audit/debugging.

    Strategy Meanings:
    - SNAPSHOT: Use cached output from previous run (exact replay)
    - RE_RUN: Re-execute and accept differences (verify behavior changes)
    - EXPLAIN_DIFF: Re-run and explain why outputs differ (audit analysis)

    Use Cases:
    - SNAPSHOT: Regulatory replay (must show exact same result)
    - RE_RUN: Testing (verify model still behaves reasonably)
    - EXPLAIN_DIFF: Debugging (understand why results changed)

    Example:
        LLM step with temperature=0.7 (non-deterministic):
        - SNAPSHOT: Return cached output from original run
        - RE_RUN: Call LLM again, log differences
        - EXPLAIN_DIFF: Call LLM again, generate diff report

    Used in:
    - NonDeterminismAttestation to declare replay strategy
    - Replay engine to handle non-deterministic steps
    """

    SNAPSHOT = "snapshot"  # Use cached output from previous run
    RE_RUN = "re_run"  # Re-execute and accept differences
    EXPLAIN_DIFF = "explain_diff"  # Re-run and explain why outputs differ


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Execution
    "SourceType",
    "StepStatus",
    "RunStatus",
    # Identity & Auth
    "UserType",
    "AuthMethod",
    # Artifacts
    "ArtifactType",
    # Security
    "SecretSource",
    # Replay
    "ReplayStrategy",
]
