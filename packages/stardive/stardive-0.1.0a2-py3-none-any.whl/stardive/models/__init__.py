"""
Stardive Core Models

This package contains the canonical internal representation (IR) for Stardive:
- RunPlan: Normalized execution intent (what should happen)
- RunRecord: Append-only execution truth (what did happen)
- Events: Core events (RunStartEvent, StepStartEvent, etc.)
- Artifacts: Artifact references and specifications
- Identity: Provenance capture (who/where/with what)
- Builders: Incremental construction patterns
"""

# Core IR models
from stardive.models.run_plan import RunPlan
from stardive.models.run_record import RunRecord, IdentityAttestation, TelemetryData

# Events
from stardive.models.events import (
    RunStartEvent,
    StepStartEvent,
    StepEndEvent,
    RunEndEvent,
    ErrorInfo,
)

# Artifacts
from stardive.models.artifacts import ArtifactRef, ArtifactSpec

# Identity & Provenance
from stardive.models.identity import (
    Identity,
    EnvironmentFingerprint,
    ModelIdentity,
    ToolIdentity,
    SecretRef,
)

# Attestations
from stardive.models.attestations import (
    ApprovalAttestation,
    ApprovalDecision,
    NonDeterminismAttestation,
)

# Steps
from stardive.models.steps import StepSpec

# Policy
from stardive.models.policy import PolicySpec

# Enums
from stardive.models.enums import (
    UserType,
    AuthMethod,
    SecretSource,
    StepStatus,
    RunStatus,
    ArtifactType,
    SourceType,
    ReplayStrategy,
)

# Builders
from stardive.models.builders import (
    RunPlanBuilder,
    RunRecordBuilder,
    compute_event_hash,
)

__all__ = [
    # Core IR
    "RunPlan",
    "RunRecord",
    "IdentityAttestation",
    "TelemetryData",
    # Events
    "RunStartEvent",
    "StepStartEvent",
    "StepEndEvent",
    "RunEndEvent",
    "ErrorInfo",
    # Artifacts
    "ArtifactRef",
    "ArtifactSpec",
    # Identity
    "Identity",
    "EnvironmentFingerprint",
    "ModelIdentity",
    "ToolIdentity",
    "SecretRef",
    # Attestations
    "ApprovalAttestation",
    "ApprovalDecision",
    "NonDeterminismAttestation",
    # Steps
    "StepSpec",
    # Policy
    "PolicySpec",
    # Enums
    "UserType",
    "AuthMethod",
    "SecretSource",
    "StepStatus",
    "RunStatus",
    "ArtifactType",
    "SourceType",
    "ReplayStrategy",
    # Builders
    "RunPlanBuilder",
    "RunRecordBuilder",
    "compute_event_hash",
]
