"""
Diff Module for Stardive Replay Verification.

This module provides artifact diff computation for verification re-runs.
When a step is re-executed, we compare the new outputs against the original
outputs to detect differences.

v0.1 Conservative Diff Semantics:
- Hash equality = MATCH
- Hash mismatch = HASH_MISMATCH
- Content diff = best-effort only (NOT guaranteed)

Deep semantic diffs are deferred to v0.2+.

Key Principles:
1. **Hash-Based Comparison**: Primary comparison is content hash
2. **Explicit Diff Types**: Clear categorization of differences
3. **Human-Readable Explanations**: Every diff has an explanation
4. **No Deep Content Analysis**: v0.1 uses hash only, v0.2+ adds semantic diff

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4.2) - Diff requirements
- docs/replay-design.md - Replay architecture
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from ..models.artifacts import ArtifactRef


# ============================================================================
# Diff Types
# ============================================================================


class DiffType(str, Enum):
    """
    Type of difference between original and verified artifacts.

    v0.1 uses hash-based comparison only:
    - MATCH: Content hashes are identical
    - HASH_MISMATCH: Content hashes differ (content unknown)
    - MISSING_ORIGINAL: Original artifact not found or tombstoned
    - MISSING_VERIFIED: Verification didn't produce this output
    - TYPE_MISMATCH: Different artifact kinds

    Future (v0.2+):
    - SEMANTIC_DIFF: Deep content analysis
    - STRUCTURAL_DIFF: Schema/structure differences
    """

    MATCH = "match"  # Hashes are identical
    HASH_MISMATCH = "hash_mismatch"  # Hashes differ (content unknown)
    MISSING_ORIGINAL = "missing_original"  # Original artifact missing/tombstoned
    MISSING_VERIFIED = "missing_verified"  # Verification didn't produce output
    TYPE_MISMATCH = "type_mismatch"  # Different artifact kinds


# ============================================================================
# Artifact Diff
# ============================================================================


class ArtifactDiff(BaseModel):
    """
    Detailed diff between original and verified artifacts.

    This model captures the comparison result between an artifact from
    the original execution and the artifact from a verification re-run.

    Purpose:
        Provides a complete record of the comparison:
        - What was compared (artifact_name)
        - What the original was (original_ref, original_hash)
        - What the verified was (verified_ref, verified_hash)
        - What the result is (diff_type)
        - Why they differ (explanation)

    Audit Trail:
        ArtifactDiff is part of the verification audit trail. It proves
        that we performed the comparison and recorded the result, even
        if the content differs.

    Examples:
        Perfect match:
            ArtifactDiff(
                artifact_name="credit_score",
                original_ref=ArtifactRef(...),
                verified_ref=ArtifactRef(...),
                diff_type=DiffType.MATCH,
                original_hash="sha256:abc123...",
                verified_hash="sha256:abc123...",
                explanation="Content hashes match exactly"
            )

        Hash mismatch (non-deterministic):
            ArtifactDiff(
                artifact_name="summary",
                original_ref=ArtifactRef(...),
                verified_ref=ArtifactRef(...),
                diff_type=DiffType.HASH_MISMATCH,
                original_hash="sha256:abc123...",
                verified_hash="sha256:def456...",
                explanation="Output content differs. This may be due to "
                           "non-deterministic execution (LLM temperature > 0)."
            )

        Missing original (tombstoned):
            ArtifactDiff(
                artifact_name="pii_data",
                original_ref=None,
                verified_ref=ArtifactRef(...),
                diff_type=DiffType.MISSING_ORIGINAL,
                original_hash=None,
                verified_hash="sha256:def456...",
                explanation="Original artifact was tombstoned (GDPR deletion)"
            )
    """

    artifact_name: str = Field(
        ...,
        description="Name of artifact in step outputs (key in outputs dict)",
    )

    # Original artifact (from original execution)
    original_ref: Optional[ArtifactRef] = Field(
        None,
        description="Reference to original artifact (None if missing)",
    )

    # Verified artifact (from re-execution)
    verified_ref: Optional[ArtifactRef] = Field(
        None,
        description="Reference to verified artifact (None if missing)",
    )

    # Comparison result
    diff_type: DiffType = Field(
        ...,
        description="Type of difference detected",
    )

    # Hash comparison
    original_hash: Optional[str] = Field(
        None,
        description="Content hash of original artifact",
    )
    verified_hash: Optional[str] = Field(
        None,
        description="Content hash of verified artifact",
    )

    # Human-readable explanation
    explanation: str = Field(
        ...,
        description="Human-readable explanation of the difference",
    )

    model_config = {"frozen": True}


# ============================================================================
# Diff Computation
# ============================================================================


def compute_artifact_diff(
    name: str,
    original: Optional[ArtifactRef],
    verified: Optional[ArtifactRef],
) -> ArtifactDiff:
    """
    Compute diff between original and verified artifacts.

    This is the core diff computation function. It compares two artifacts
    (original from stored execution, verified from re-execution) and
    produces a detailed diff result.

    v0.1 Comparison Strategy:
        1. If both missing → MISSING_ORIGINAL (unusual case)
        2. If original missing → MISSING_ORIGINAL
        3. If verified missing → MISSING_VERIFIED
        4. If different kinds → TYPE_MISMATCH
        5. If hashes match → MATCH
        6. If hashes differ → HASH_MISMATCH

    No deep content analysis in v0.1. That's deferred to v0.2+.

    Args:
        name: Name of artifact in outputs dict
        original: Original artifact reference (None if missing/tombstoned)
        verified: Verified artifact reference (None if not produced)

    Returns:
        ArtifactDiff with comparison result and explanation

    Examples:
        Matching artifacts:
            >>> diff = compute_artifact_diff(
            ...     "result",
            ...     original_ref,  # hash=sha256:abc...
            ...     verified_ref,  # hash=sha256:abc...
            ... )
            >>> diff.diff_type
            DiffType.MATCH

        Mismatched artifacts:
            >>> diff = compute_artifact_diff(
            ...     "result",
            ...     original_ref,  # hash=sha256:abc...
            ...     verified_ref,  # hash=sha256:def...
            ... )
            >>> diff.diff_type
            DiffType.HASH_MISMATCH
    """
    # Extract hashes
    original_hash = original.content_hash if original else None
    verified_hash = verified.content_hash if verified else None

    # Case 1: Both missing (unusual)
    if original is None and verified is None:
        return ArtifactDiff(
            artifact_name=name,
            original_ref=None,
            verified_ref=None,
            diff_type=DiffType.MISSING_ORIGINAL,
            original_hash=None,
            verified_hash=None,
            explanation=(
                f"Artifact '{name}' is missing from both original and verified "
                "execution. This is an unexpected state."
            ),
        )

    # Case 2: Original missing
    if original is None:
        return ArtifactDiff(
            artifact_name=name,
            original_ref=None,
            verified_ref=verified,
            diff_type=DiffType.MISSING_ORIGINAL,
            original_hash=None,
            verified_hash=verified_hash,
            explanation=(
                f"Original artifact '{name}' is missing or was tombstoned. "
                "Cannot compare against verified output."
            ),
        )

    # Case 3: Verified missing
    if verified is None:
        return ArtifactDiff(
            artifact_name=name,
            original_ref=original,
            verified_ref=None,
            diff_type=DiffType.MISSING_VERIFIED,
            original_hash=original_hash,
            verified_hash=None,
            explanation=(
                f"Verification did not produce artifact '{name}'. "
                "The executor may have failed or returned different outputs."
            ),
        )

    # Case 4: Type mismatch
    if original.artifact_kind != verified.artifact_kind:
        return ArtifactDiff(
            artifact_name=name,
            original_ref=original,
            verified_ref=verified,
            diff_type=DiffType.TYPE_MISMATCH,
            original_hash=original_hash,
            verified_hash=verified_hash,
            explanation=(
                f"Artifact '{name}' has different types: "
                f"original={original.artifact_kind.value}, "
                f"verified={verified.artifact_kind.value}. "
                "The executor produced a different artifact type."
            ),
        )

    # Case 5: Hash match
    if original_hash == verified_hash:
        return ArtifactDiff(
            artifact_name=name,
            original_ref=original,
            verified_ref=verified,
            diff_type=DiffType.MATCH,
            original_hash=original_hash,
            verified_hash=verified_hash,
            explanation=(
                f"Artifact '{name}' matches exactly. "
                f"Content hash: {original_hash}"
            ),
        )

    # Case 6: Hash mismatch
    return ArtifactDiff(
        artifact_name=name,
        original_ref=original,
        verified_ref=verified,
        diff_type=DiffType.HASH_MISMATCH,
        original_hash=original_hash,
        verified_hash=verified_hash,
        explanation=(
            f"Artifact '{name}' content differs. "
            f"Original hash: {original_hash}, "
            f"Verified hash: {verified_hash}. "
            "This may be due to non-deterministic execution "
            "(LLM temperature > 0, external API, timestamp, etc.)."
        ),
    )


def explain_diff(diff: ArtifactDiff) -> str:
    """
    Generate a user-friendly explanation of an artifact diff.

    This function produces a human-readable explanation suitable for
    CLI output or reports. It includes the diff type, artifact name,
    and possible causes.

    Args:
        diff: ArtifactDiff to explain

    Returns:
        Multi-line string explanation

    Example:
        >>> diff = compute_artifact_diff("result", original, verified)
        >>> print(explain_diff(diff))
        Artifact: result
        Status: HASH_MISMATCH
        Original hash: sha256:abc123...
        Verified hash: sha256:def456...

        Possible causes:
        - Non-deterministic LLM (temperature > 0)
        - External API returned different data
        - Timestamp or random values in output
        - Model has been updated since original execution
    """
    lines = [
        f"Artifact: {diff.artifact_name}",
        f"Status: {diff.diff_type.value.upper()}",
    ]

    if diff.original_hash:
        lines.append(f"Original hash: {diff.original_hash}")
    else:
        lines.append("Original hash: (missing)")

    if diff.verified_hash:
        lines.append(f"Verified hash: {diff.verified_hash}")
    else:
        lines.append("Verified hash: (missing)")

    lines.append("")
    lines.append(diff.explanation)

    # Add possible causes for mismatches
    if diff.diff_type == DiffType.HASH_MISMATCH:
        lines.append("")
        lines.append("Possible causes:")
        lines.append("- Non-deterministic LLM (temperature > 0, no seed)")
        lines.append("- External API returned different data")
        lines.append("- Timestamp or random values in output")
        lines.append("- Model has been updated since original execution")

    elif diff.diff_type == DiffType.MISSING_ORIGINAL:
        lines.append("")
        lines.append("Possible causes:")
        lines.append("- Artifact was tombstoned (GDPR deletion request)")
        lines.append("- Artifact storage corruption")
        lines.append("- Run record incomplete or corrupted")

    elif diff.diff_type == DiffType.MISSING_VERIFIED:
        lines.append("")
        lines.append("Possible causes:")
        lines.append("- Executor threw an exception")
        lines.append("- Executor returned different output keys")
        lines.append("- Step logic has changed since original execution")

    elif diff.diff_type == DiffType.TYPE_MISMATCH:
        lines.append("")
        lines.append("Possible causes:")
        lines.append("- Step logic has changed output type")
        lines.append("- Serialization configuration differs")

    return "\n".join(lines)


def summarize_diffs(diffs: list[ArtifactDiff]) -> str:
    """
    Generate a summary of multiple artifact diffs.

    This function produces a concise summary suitable for reports
    or CLI output.

    Args:
        diffs: List of ArtifactDiff objects

    Returns:
        Summary string with counts by diff type

    Example:
        >>> diffs = [diff1, diff2, diff3]
        >>> print(summarize_diffs(diffs))
        Diff Summary: 3 artifacts compared
        - MATCH: 2
        - HASH_MISMATCH: 1
    """
    if not diffs:
        return "Diff Summary: No artifacts to compare"

    # Count by diff type
    counts: dict[DiffType, int] = {}
    for diff in diffs:
        counts[diff.diff_type] = counts.get(diff.diff_type, 0) + 1

    lines = [f"Diff Summary: {len(diffs)} artifacts compared"]
    for diff_type in DiffType:
        if diff_type in counts:
            lines.append(f"- {diff_type.value.upper()}: {counts[diff_type]}")

    return "\n".join(lines)


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "DiffType",
    "ArtifactDiff",
    "compute_artifact_diff",
    "explain_diff",
    "summarize_diffs",
]
