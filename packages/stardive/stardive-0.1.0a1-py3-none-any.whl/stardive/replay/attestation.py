"""
Attestation Module for Stardive Replay Verification.

This module provides helpers for creating and classifying NonDeterminismAttestation
records when verification re-runs differ from original execution.

Purpose:
    When a step is re-executed during verification and produces different outputs,
    we must create an explicit attestation declaring that the step is non-deterministic.
    This is audit-grade honesty about replay limitations.

Key Principles:
1. **Explicit Declaration**: Non-determinism is declared, not assumed
2. **Best-Effort Classification**: We attempt to classify the reason
3. **Unknown is Acceptable**: If we can't determine the cause, say so
4. **Audit Trail**: Attestations are part of the permanent record

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4.2) - Attestation requirements
- models/attestations.py - NonDeterminismAttestation model
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from ..models.attestations import NonDeterminismAttestation
from ..models.enums import ReplayStrategy
from ..models.identity import ModelIdentity
from .diff import ArtifactDiff, DiffType


# ============================================================================
# Non-Determinism Reason Classification
# ============================================================================


class NonDeterminismReason(str, Enum):
    """
    Reason why a step produced different outputs on replay.

    This enum provides a classification system for non-determinism.
    The classification is best-effort and UNKNOWN is acceptable.

    Reason Meanings:
        - LLM_RESPONSE: LLM gave different answer (temperature > 0, no seed)
        - EXTERNAL_API: External API returned different data
        - TIMESTAMP: Output includes time-dependent values
        - RANDOM: Output includes random or seed-dependent values
        - MISSING_INPUT: Input artifact missing/tombstoned
        - MODEL_UPDATED: Model has been updated since original execution
        - UNKNOWN: Cannot determine the cause

    Classification Strategy (v0.1):
        - LLM steps → LLM_RESPONSE (default for model_identity present)
        - HTTP/API steps → EXTERNAL_API
        - Missing original → MISSING_INPUT
        - Otherwise → UNKNOWN

    Future (v0.2+):
        - Deep content analysis to detect timestamps
        - Random value detection
        - Model version comparison
    """

    LLM_RESPONSE = "llm_response"  # LLM gave different answer
    EXTERNAL_API = "external_api"  # External API changed
    TIMESTAMP = "timestamp"  # Time-dependent output
    RANDOM = "random"  # Random/seed-dependent
    MISSING_INPUT = "missing_input"  # Input artifact missing/tombstoned
    MODEL_UPDATED = "model_updated"  # Model has been updated
    UNKNOWN = "unknown"  # Cannot determine cause


# ============================================================================
# Reason Classification
# ============================================================================


def classify_nondeterminism(
    step_type: Optional[str],
    diffs: List[ArtifactDiff],
    model_identity: Optional[ModelIdentity] = None,
) -> NonDeterminismReason:
    """
    Classify the reason for non-determinism based on step type and diffs.

    This is a best-effort classification. The classification is based on
    simple heuristics in v0.1. More sophisticated analysis is deferred
    to v0.2+.

    Classification Logic:
        1. Check for missing original artifacts → MISSING_INPUT
        2. Check if step has model_identity → LLM_RESPONSE
        3. Check step type:
           - "llm" → LLM_RESPONSE
           - "http", "api" → EXTERNAL_API
        4. Default → UNKNOWN

    Args:
        step_type: Type of step (e.g., "llm", "python", "http")
        diffs: List of artifact diffs from verification
        model_identity: Model identity if step uses LLM

    Returns:
        NonDeterminismReason classification

    Examples:
        LLM step with temperature > 0:
            >>> reason = classify_nondeterminism(
            ...     step_type="llm",
            ...     diffs=[diff],
            ...     model_identity=ModelIdentity(temperature=0.7, ...)
            ... )
            >>> reason
            NonDeterminismReason.LLM_RESPONSE

        HTTP step:
            >>> reason = classify_nondeterminism(
            ...     step_type="http",
            ...     diffs=[diff],
            ... )
            >>> reason
            NonDeterminismReason.EXTERNAL_API

        Missing input:
            >>> diff = ArtifactDiff(diff_type=DiffType.MISSING_ORIGINAL, ...)
            >>> reason = classify_nondeterminism("python", [diff])
            >>> reason
            NonDeterminismReason.MISSING_INPUT
    """
    # Check for missing original artifacts first
    for diff in diffs:
        if diff.diff_type == DiffType.MISSING_ORIGINAL:
            return NonDeterminismReason.MISSING_INPUT

    # Check if step has model identity (LLM step)
    if model_identity is not None:
        # Check if model is non-deterministic
        if model_identity.temperature and model_identity.temperature > 0:
            return NonDeterminismReason.LLM_RESPONSE
        if model_identity.seed is None:
            return NonDeterminismReason.LLM_RESPONSE
        # Even with temperature=0 and seed, LLMs can be non-deterministic
        return NonDeterminismReason.LLM_RESPONSE

    # Check step type
    if step_type:
        step_type_lower = step_type.lower()
        if step_type_lower in ("llm", "ai", "model", "inference"):
            return NonDeterminismReason.LLM_RESPONSE
        if step_type_lower in ("http", "api", "rest", "graphql", "grpc"):
            return NonDeterminismReason.EXTERNAL_API

    # Default to unknown
    return NonDeterminismReason.UNKNOWN


def classify_nondeterminism_from_model(
    model_identity: ModelIdentity,
) -> NonDeterminismReason:
    """
    Classify non-determinism reason specifically for LLM steps.

    This function analyzes the model identity to determine why
    the LLM might produce different outputs.

    Args:
        model_identity: Model identity from step

    Returns:
        NonDeterminismReason (always LLM_RESPONSE for LLM steps)

    Example:
        >>> reason = classify_nondeterminism_from_model(
        ...     ModelIdentity(temperature=0.7, seed=None, ...)
        ... )
        >>> reason
        NonDeterminismReason.LLM_RESPONSE
    """
    return NonDeterminismReason.LLM_RESPONSE


# ============================================================================
# Attestation Creation
# ============================================================================


def create_nondeterminism_attestation(
    step_id: str,
    diffs: List[ArtifactDiff],
    reason: NonDeterminismReason,
    model_identity: Optional[ModelIdentity] = None,
    replay_strategy: ReplayStrategy = ReplayStrategy.SNAPSHOT,
    metadata: Optional[dict] = None,
) -> NonDeterminismAttestation:
    """
    Create a NonDeterminismAttestation for a step with differing outputs.

    This function creates an attestation that explicitly declares a step
    is non-deterministic and explains why. The attestation becomes part
    of the audit trail.

    Args:
        step_id: ID of the step that produced different outputs
        diffs: List of artifact diffs showing the differences
        reason: Classified reason for non-determinism
        model_identity: Model identity if step uses LLM
        replay_strategy: Strategy for handling replay
        metadata: Additional context (optional)

    Returns:
        NonDeterminismAttestation ready for storage

    Example:
        >>> attestation = create_nondeterminism_attestation(
        ...     step_id="analyze",
        ...     diffs=[diff1, diff2],
        ...     reason=NonDeterminismReason.LLM_RESPONSE,
        ...     model_identity=model_id,
        ... )
        >>> attestation.step_id
        'analyze'
        >>> attestation.reasons
        ['llm_response', 'Output differed on re-execution']
    """
    # Build reasons list
    reasons = [reason.value]

    # Add diff information to reasons
    mismatched_artifacts = [
        diff.artifact_name
        for diff in diffs
        if diff.diff_type == DiffType.HASH_MISMATCH
    ]
    if mismatched_artifacts:
        reasons.append(f"Outputs differed: {', '.join(mismatched_artifacts)}")

    # Add temperature info if available
    if model_identity and model_identity.temperature:
        if model_identity.temperature > 0:
            reasons.append(f"temperature={model_identity.temperature}")
        if model_identity.seed is None:
            reasons.append("no seed provided")

    # Build model state string
    model_state: Optional[str] = None
    if model_identity:
        parts = []
        if model_identity.model_name:
            parts.append(model_identity.model_name)
        if model_identity.model_version:
            parts.append(f"version={model_identity.model_version}")
        if parts:
            model_state = ", ".join(parts)

    # Build metadata
    full_metadata = metadata.copy() if metadata else {}
    full_metadata["diff_count"] = len(diffs)
    full_metadata["mismatched_artifacts"] = mismatched_artifacts

    return NonDeterminismAttestation(
        step_id=step_id,
        model_identity=model_identity,
        reasons=reasons,
        timestamp=datetime.utcnow(),
        model_state=model_state,
        replay_strategy=replay_strategy,
        metadata=full_metadata,
    )


def create_attestation_from_diffs(
    step_id: str,
    step_type: Optional[str],
    diffs: List[ArtifactDiff],
    model_identity: Optional[ModelIdentity] = None,
    replay_strategy: ReplayStrategy = ReplayStrategy.SNAPSHOT,
) -> Optional[NonDeterminismAttestation]:
    """
    Create attestation from diffs, or None if all outputs matched.

    This is a convenience function that:
    1. Checks if any diffs indicate mismatches
    2. Classifies the non-determinism reason
    3. Creates an attestation (or returns None if all matched)

    Args:
        step_id: ID of the step
        step_type: Type of step (e.g., "llm", "python")
        diffs: List of artifact diffs from verification
        model_identity: Model identity if step uses LLM
        replay_strategy: Strategy for handling replay

    Returns:
        NonDeterminismAttestation if any outputs differed, None otherwise

    Example:
        >>> attestation = create_attestation_from_diffs(
        ...     step_id="analyze",
        ...     step_type="llm",
        ...     diffs=[diff1, diff2],
        ...     model_identity=model_id,
        ... )
        >>> if attestation:
        ...     print("Step is non-deterministic")
    """
    # Check if all outputs matched
    all_matched = all(diff.diff_type == DiffType.MATCH for diff in diffs)
    if all_matched:
        return None

    # Classify the reason
    reason = classify_nondeterminism(
        step_type=step_type,
        diffs=diffs,
        model_identity=model_identity,
    )

    # Create attestation
    return create_nondeterminism_attestation(
        step_id=step_id,
        diffs=diffs,
        reason=reason,
        model_identity=model_identity,
        replay_strategy=replay_strategy,
    )


# ============================================================================
# Reason Explanation
# ============================================================================


def explain_nondeterminism_reason(reason: NonDeterminismReason) -> str:
    """
    Generate a human-readable explanation for a non-determinism reason.

    Args:
        reason: NonDeterminismReason to explain

    Returns:
        Human-readable explanation string

    Example:
        >>> print(explain_nondeterminism_reason(NonDeterminismReason.LLM_RESPONSE))
        The LLM produced a different response. This is expected when using
        temperature > 0 or when no seed is provided. LLM outputs are inherently
        non-deterministic unless special precautions are taken.
    """
    explanations = {
        NonDeterminismReason.LLM_RESPONSE: (
            "The LLM produced a different response. This is expected when using "
            "temperature > 0 or when no seed is provided. LLM outputs are inherently "
            "non-deterministic unless special precautions are taken."
        ),
        NonDeterminismReason.EXTERNAL_API: (
            "An external API returned different data. This is expected for APIs "
            "that return real-time or frequently updated data (stock prices, "
            "weather, live feeds, etc.)."
        ),
        NonDeterminismReason.TIMESTAMP: (
            "The output includes time-dependent values (timestamps, dates, etc.). "
            "These values naturally change between executions."
        ),
        NonDeterminismReason.RANDOM: (
            "The output includes random or seed-dependent values. If the random "
            "seed was not captured or differs, outputs will vary."
        ),
        NonDeterminismReason.MISSING_INPUT: (
            "One or more input artifacts are missing or have been tombstoned "
            "(deleted for GDPR/compliance reasons). Verification cannot proceed "
            "without the original inputs."
        ),
        NonDeterminismReason.MODEL_UPDATED: (
            "The AI model has been updated since the original execution. "
            "Model providers frequently update their models, which can cause "
            "different outputs even with identical inputs."
        ),
        NonDeterminismReason.UNKNOWN: (
            "The exact cause of non-determinism could not be determined. "
            "The step may have multiple sources of non-determinism or use "
            "an unknown pattern."
        ),
    }
    return explanations.get(reason, f"Unknown reason: {reason.value}")


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "NonDeterminismReason",
    "classify_nondeterminism",
    "classify_nondeterminism_from_model",
    "create_nondeterminism_attestation",
    "create_attestation_from_diffs",
    "explain_nondeterminism_reason",
]
