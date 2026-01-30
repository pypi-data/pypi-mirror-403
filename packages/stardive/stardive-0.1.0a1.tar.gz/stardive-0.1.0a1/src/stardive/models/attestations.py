"""
Attestation Models for Stardive Execution Kernel.

This module defines attestation models that provide cryptographic or human-verified
proof of specific conditions during execution. Attestations are authoritative records
that certain actions occurred or conditions were met.

Attestations Provided:
- **ApprovalAttestation**: Human approval with optional digital signature
- **NonDeterminismAttestation**: Declaration that step cannot be replayed deterministically

Key Principles:
1. **Cryptographic Verification**: Attestations can be digitally signed
2. **Audit Trail**: Every attestation is evidence for compliance
3. **Explicit Declaration**: Non-determinism must be declared, not assumed
4. **Human Accountability**: Approvals link to verified identities
5. **Immutability**: All attestations are frozen after creation

For detailed specifications, see:
- docs/identity-provenance.md - Identity and attestation model
- docs/canonical-ir.md - How attestations fit into IR
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from .enums import ReplayStrategy
from .identity import Identity, ModelIdentity


# ============================================================================
# Approval Attestations
# ============================================================================


class ApprovalAttestation(BaseModel):
    """
    Cryptographic proof of human approval.

    Purpose:
        For regulated environments, certain steps require human approval
        before execution. This model provides authoritative proof that:
        - A specific human reviewed the step
        - They made an explicit approve/deny decision
        - They acknowledged relevant risks
        - The approval can be cryptographically verified

    Use Cases:
        - Financial transactions requiring manager approval
        - Healthcare decisions requiring doctor sign-off
        - Legal actions requiring counsel approval
        - Production deployments requiring security review

    Digital Signatures:
        Approvals can be digitally signed for non-repudiation:
        - signature: Digital signature of approval (ECDSA, RSA, etc.)
        - signature_method: Algorithm used for signing
        - Signature covers: step_id, decision, approved_at, approver identity

        Without signature, approval is still recorded but less legally binding.

    Audit Trail:
        ApprovalAttestations are stored in RunRecord.identities as
        authoritative evidence of human approval. They answer:
        - WHO approved? (approver Identity)
        - WHAT did they approve? (step_id)
        - WHEN did they approve? (approved_at timestamp)
        - WHY did they approve? (approval_reason)
        - DID they see risks? (risk_acknowledged)

    Examples:
        Manager approves financial transaction:
            ApprovalAttestation(
                step_id="wire_transfer",
                approver=Identity(
                    user_id="manager@company.com",
                    user_type=UserType.HUMAN,
                    auth_method=AuthMethod.OAUTH,
                    verified=True
                ),
                decision=ApprovalDecision.APPROVE,
                approved_at=datetime(2024, 12, 27, 10, 30, 0),
                approval_reason="Transaction approved after review of documentation",
                risk_acknowledged=True,
                signature="3045022100...",  # ECDSA signature
                signature_method="ecdsa-sha256"
            )

        Doctor denies medical procedure:
            ApprovalAttestation(
                step_id="prescribe_medication",
                approver=Identity(
                    user_id="dr.smith@hospital.com",
                    user_type=UserType.HUMAN,
                    auth_method=AuthMethod.CERT,
                    verified=True
                ),
                decision=ApprovalDecision.DENY,
                approved_at=datetime(2024, 12, 27, 11, 0, 0),
                approval_reason="Patient has documented allergy to this medication",
                risk_acknowledged=True
            )

        Escalated approval:
            ApprovalAttestation(
                step_id="deploy_to_production",
                approver=Identity(
                    user_id="ops@company.com",
                    user_type=UserType.HUMAN,
                    auth_method=AuthMethod.OAUTH,
                    verified=True
                ),
                decision=ApprovalDecision.ESCALATE,
                approved_at=datetime(2024, 12, 27, 12, 0, 0),
                approval_reason="Escalating to CTO for final approval",
                risk_acknowledged=True
            )
    """

    step_id: str = Field(..., description="Step requiring approval")
    approver: Identity = Field(..., description="Who approved (verified identity)")
    decision: "ApprovalDecision" = Field(..., description="Approval decision")
    approved_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When approval was granted/denied",
    )

    # Optional digital signature for non-repudiation
    signature: Optional[str] = Field(
        None,
        description="Digital signature of approval (hex-encoded)",
    )
    signature_method: Optional[str] = Field(
        None,
        description="Signature algorithm",
        examples=["ecdsa-sha256", "rsa-sha256", "ed25519"],
    )

    # Context
    approval_reason: Optional[str] = Field(
        None, description="Free text explanation for decision"
    )
    risk_acknowledged: bool = Field(
        False, description="Did approver see and acknowledge risk warnings?"
    )

    # Additional metadata
    approval_metadata: dict = Field(
        default_factory=dict,
        description="Additional approval context (compliance IDs, etc.)",
    )

    model_config = {"frozen": True, "protected_namespaces": ()}


class ApprovalDecision(str, Enum):
    """Decision made by approver."""

    APPROVE = "approve"  # Approved, execution may proceed
    DENY = "deny"  # Denied, execution must stop
    ESCALATE = "escalate"  # Escalate to higher authority


# ============================================================================
# Non-Determinism Attestations
# ============================================================================


class NonDeterminismAttestation(BaseModel):
    """
    Declaration that a step cannot be replayed deterministically.

    Purpose:
        AI/LLM steps are often non-deterministic (temperature > 0, no seed).
        For audit and compliance, we must EXPLICITLY declare when a step
        cannot produce identical results on replay.

        This attestation:
        - Declares which step is non-deterministic
        - Explains WHY it's non-deterministic
        - Specifies how to handle replay
        - Records model state for best-effort reproduction

    Rationale:
        Audit systems must be honest about limitations. Rather than pretending
        non-deterministic steps can be perfectly replayed, we:
        1. Explicitly declare non-determinism
        2. Explain the reasons (temperature, real-time data, etc.)
        3. Provide replay strategy (snapshot, re-run, explain diff)
        4. Capture enough context for best-effort reproduction

    Reasons for Non-Determinism:
        Common reasons why steps cannot be replayed identically:
        - **temperature > 0**: LLM sampling introduces randomness
        - **no seed support**: Provider doesn't support deterministic seeds
        - **real-time data**: Step depends on current time or external state
        - **external API**: Third-party API may return different results
        - **model updates**: Provider updated model since original run

    Replay Strategies:
        - **SNAPSHOT**: Use cached output from original run (exact replay)
        - **RE_RUN**: Re-execute and accept differences (verify behavior)
        - **EXPLAIN_DIFF**: Re-run and generate diff report (audit analysis)

    Use Cases:
        - LLM calls with temperature > 0
        - Real-time data fetching (stock prices, weather)
        - External API calls (third-party services)
        - Time-dependent computations
        - Random sampling or Monte Carlo methods

    Examples:
        LLM with temperature > 0:
            NonDeterminismAttestation(
                step_id="analyze_credit",
                model_identity=ModelIdentity(
                    provider="openai",
                    model_name="gpt-4",
                    temperature=0.7,  # Non-deterministic!
                    seed=None,
                    ...
                ),
                reasons=["temperature > 0", "no seed provided"],
                timestamp=datetime(2024, 12, 27, 10, 30, 0),
                replay_strategy=ReplayStrategy.SNAPSHOT
            )

        Real-time data:
            NonDeterminismAttestation(
                step_id="fetch_stock_price",
                model_identity=None,  # Not an LLM step
                reasons=["real-time data source", "stock price changes continuously"],
                timestamp=datetime(2024, 12, 27, 10, 30, 0),
                replay_strategy=ReplayStrategy.EXPLAIN_DIFF
            )

        External API:
            NonDeterminismAttestation(
                step_id="check_credit_bureau",
                model_identity=None,
                reasons=["external API", "bureau data may have updated"],
                timestamp=datetime(2024, 12, 27, 10, 30, 0),
                model_state="credit_bureau_version=2024.12",
                replay_strategy=ReplayStrategy.RE_RUN
            )

        LLM with seed (deterministic):
            # No attestation needed!
            # Step can be replayed deterministically with same seed.
    """

    step_id: str = Field(..., description="Step that is non-deterministic")
    model_identity: Optional[ModelIdentity] = Field(
        None, description="Model identity (for LLM steps)"
    )

    # Why non-deterministic?
    reasons: List[str] = Field(
        ...,
        description="Reasons why replay might differ",
        examples=[
            ["temperature > 0", "no seed support"],
            ["real-time data", "external API"],
        ],
    )

    # When was this captured?
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this step executed (for context)",
    )

    # Model state for best-effort replay
    model_state: Optional[str] = Field(
        None,
        description="Provider-specific model state (if available)",
        examples=["gpt-4-turbo-2024-04-09", "credit_bureau_version=2024.12"],
    )

    # How to handle replay?
    replay_strategy: ReplayStrategy = Field(
        ..., description="Strategy for replaying this step"
    )

    # Additional context
    metadata: dict = Field(
        default_factory=dict,
        description="Additional context for replay",
    )

    model_config = {"frozen": True, "protected_namespaces": ()}


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "ApprovalAttestation",
    "ApprovalDecision",
    "NonDeterminismAttestation",
]
