"""
Verification Module for Stardive Replay.

This module provides optional verification re-runs (Mode B) where steps can be
re-executed with user-provided executors to verify they produce matching outputs.

Mode B: Verification Re-run (Optional API)
- Input: run_id, executor_map
- Output: VerificationReport
- Re-executes steps and compares outputs
- Generates NonDeterminismAttestation if mismatches occur

Key Principles:
1. **User-Provided Executors**: Stardive doesn't execute; users provide executors
2. **Hash-Based Comparison**: Outputs compared by content hash
3. **Explicit Attestation**: Mismatches generate NonDeterminismAttestation
4. **Graceful Failure**: Executor errors are captured, not propagated

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4.2) - Verification requirements
- docs/replay-design.md - Replay architecture
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from ..artifacts import ArtifactKind
from ..artifacts.serializer import compute_hash, compute_text_hash
from ..artifacts.storage import ArtifactStorage
from ..models.artifacts import ArtifactRef
from ..models.attestations import NonDeterminismAttestation
from ..models.enums import ArtifactType, ReplayStrategy
from ..models.identity import ModelIdentity
from ..storage.base import StorageBackend
from .attestation import (
    NonDeterminismReason,
    classify_nondeterminism,
    create_nondeterminism_attestation,
)
from .diff import ArtifactDiff, DiffType, compute_artifact_diff
from .snapshot_view import RunSnapshotView, StepSnapshotView, reconstruct_run


# ============================================================================
# Step Executor Protocol
# ============================================================================


class StepExecutor(Protocol):
    """
    User-provided executor for re-running a step.

    The executor protocol defines the contract between Stardive and user code
    for verification re-runs. Users must implement this protocol for each
    step type they want to verify.

    Input/Output Key Mapping Contract:
    ---------------------------------
    - **inputs**: Dict keyed by artifact names from StepStartEvent.inputs
      Values are the actual content (deserialized), NOT ArtifactRef objects.

    - **return**: Dict keyed by ORIGINAL output names from StepEndEvent.outputs
      Keys must match the original output names exactly.

    Stardive will:
    1. Retrieve input artifact content from storage
    2. Call execute() with deserialized content
    3. Hash each returned output using artifact serializer
    4. Compare output hashes against original ArtifactRefs
    5. Generate attestation if outputs differ

    Example Implementation:
        class MyLLMExecutor:
            def __init__(self, client):
                self.client = client

            def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
                # inputs = {"prompt": "Analyze this data", "data": {...}}
                prompt = inputs["prompt"]
                data = inputs["data"]

                response = self.client.complete(prompt=prompt, context=data)

                # Return dict with SAME KEYS as original outputs
                return {
                    "response": response.text,
                    "confidence": response.confidence,
                }

    Error Handling:
        If execute() raises an exception, Stardive captures it and marks
        the step verification as failed with the error message.
    """

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-execute a step with the given inputs.

        Args:
            inputs: Dict of input name → deserialized content.
                    Keys match StepStartEvent.inputs keys.
                    Values are actual content, not ArtifactRef.

        Returns:
            Dict of output name → content.
            Keys MUST match original StepEndEvent.outputs keys.
            Values should be serializable content.

        Raises:
            Any exception will be captured as a verification error.
        """
        ...


# ============================================================================
# Step Verification Result
# ============================================================================


class StepVerificationResult(BaseModel):
    """
    Result of verifying a single step.

    This model captures the complete result of re-executing a step
    and comparing its outputs against the original execution.

    Purpose:
        Provides a detailed record of verification:
        - What step was verified (step_id)
        - What outputs were expected (original_outputs)
        - What outputs were produced (verified_outputs)
        - Whether they matched (matches)
        - Detailed diffs (diffs)
        - Attestation if needed (attestation)

    Examples:
        Step matched:
            StepVerificationResult(
                step_id="analyze",
                original_outputs={"result": ArtifactRef(...)},
                verified_outputs={"result": ArtifactRef(...)},
                matches=True,
                diffs=[ArtifactDiff(diff_type=DiffType.MATCH, ...)],
                attestation=None,
                error=None
            )

        Step differed:
            StepVerificationResult(
                step_id="analyze",
                original_outputs={"result": ArtifactRef(...)},
                verified_outputs={"result": ArtifactRef(...)},
                matches=False,
                diffs=[ArtifactDiff(diff_type=DiffType.HASH_MISMATCH, ...)],
                attestation=NonDeterminismAttestation(...),
                error=None
            )

        Executor failed:
            StepVerificationResult(
                step_id="analyze",
                original_outputs={"result": ArtifactRef(...)},
                verified_outputs={},
                matches=False,
                diffs=[],
                attestation=None,
                error="TimeoutError: Executor timed out after 30s"
            )
    """

    step_id: str = Field(..., description="Step that was verified")

    # Original outputs (from stored execution)
    original_outputs: Dict[str, ArtifactRef] = Field(
        default_factory=dict,
        description="Original output artifacts",
    )

    # Verified outputs (from re-execution)
    verified_outputs: Dict[str, ArtifactRef] = Field(
        default_factory=dict,
        description="Verified output artifacts",
    )

    # Match result
    matches: bool = Field(
        ...,
        description="Do all output hashes match?",
    )

    # Detailed diffs
    diffs: List[ArtifactDiff] = Field(
        default_factory=list,
        description="Detailed comparison of each output",
    )

    # Attestation (if outputs differed)
    attestation: Optional[NonDeterminismAttestation] = Field(
        None,
        description="Non-determinism attestation if outputs differed",
    )

    # Error (if executor failed)
    error: Optional[str] = Field(
        None,
        description="Error message if executor failed",
    )

    model_config = {"frozen": True}


# ============================================================================
# Verification Context
# ============================================================================


class VerificationContext(BaseModel):
    """
    Context for a verification session.

    This model tracks the state of a verification re-run, including
    all step results and attestations generated.

    Purpose:
        Provides a container for verification state:
        - Original snapshot being verified
        - Unique verification run ID
        - Results for each verified step
        - Collected attestations

    Usage:
        context = VerificationContext(
            original_snapshot=snapshot,
            verification_run_id=f"verify_{uuid4().hex[:12]}",
        )

        result = verify_step(context, "analyze", executor, ...)
        context.step_results["analyze"] = result
    """

    original_snapshot: RunSnapshotView = Field(
        ...,
        description="Original run snapshot being verified",
    )

    verification_run_id: str = Field(
        default_factory=lambda: f"verify_{uuid4().hex[:12]}",
        description="Unique ID for this verification session",
    )

    step_results: Dict[str, StepVerificationResult] = Field(
        default_factory=dict,
        description="Results for each verified step",
    )

    attestations: List[NonDeterminismAttestation] = Field(
        default_factory=list,
        description="All non-determinism attestations generated",
    )

    model_config = {"frozen": False}  # Mutable during verification


# ============================================================================
# Verification Report
# ============================================================================


class VerificationReport(BaseModel):
    """
    Complete report of a verification re-run.

    This is the final output of verification (Mode B). It provides
    a comprehensive summary of the verification process and results.

    Purpose:
        Provides audit-grade documentation of verification:
        - What was verified (original_run_id)
        - When it was verified (verification_run_id, created_at)
        - Overall result (overall_match)
        - Detailed results (step_results)
        - All attestations (attestations)
        - Human-readable summary

    Examples:
        All steps matched:
            VerificationReport(
                original_run_id="run_abc123",
                verification_run_id="verify_xyz789",
                overall_match=True,
                steps_verified=3,
                steps_matched=3,
                step_results={...},
                attestations=[],
                summary="All 3 verified steps produced matching outputs.",
                created_at=datetime(...)
            )

        Some steps differed:
            VerificationReport(
                original_run_id="run_abc123",
                verification_run_id="verify_xyz789",
                overall_match=False,
                steps_verified=3,
                steps_matched=2,
                step_results={...},
                attestations=[NonDeterminismAttestation(...)],
                summary="2 of 3 steps matched. 1 step produced different outputs.",
                created_at=datetime(...)
            )
    """

    original_run_id: str = Field(
        ...,
        description="ID of the original run being verified",
    )

    verification_run_id: str = Field(
        ...,
        description="ID of this verification session",
    )

    # Overall result
    overall_match: bool = Field(
        ...,
        description="Did all verified steps match?",
    )

    # Counts
    steps_verified: int = Field(
        ...,
        description="Number of steps verified",
    )

    steps_matched: int = Field(
        ...,
        description="Number of steps that matched",
    )

    # Detailed results
    step_results: Dict[str, StepVerificationResult] = Field(
        default_factory=dict,
        description="Results for each verified step",
    )

    # Attestations
    attestations: List[NonDeterminismAttestation] = Field(
        default_factory=list,
        description="All non-determinism attestations",
    )

    # Summary
    summary: str = Field(
        ...,
        description="Human-readable summary of verification",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When verification was performed",
    )

    model_config = {"frozen": True}


# ============================================================================
# Verification Functions
# ============================================================================


def verify_step(
    context: VerificationContext,
    step_id: str,
    executor: StepExecutor,
    artifact_storage: ArtifactStorage,
    run_id: str,
) -> StepVerificationResult:
    """
    Verify a single step by re-executing with provided executor.

    This function:
    1. Loads original inputs from storage
    2. Calls executor with deserialized inputs
    3. Hashes each returned output
    4. Compares hashes against original outputs
    5. Creates attestation if outputs differ

    Args:
        context: Verification context
        step_id: Step to verify
        executor: User-provided executor implementing StepExecutor protocol
        artifact_storage: Storage for retrieving input artifacts
        run_id: Run ID for creating new artifact references

    Returns:
        StepVerificationResult with comparison details

    Example:
        >>> result = verify_step(
        ...     context=context,
        ...     step_id="analyze",
        ...     executor=my_executor,
        ...     artifact_storage=storage,
        ...     run_id="run_abc123"
        ... )
        >>> if result.matches:
        ...     print("Step verified successfully")
    """
    # Get step snapshot
    step_snapshot = context.original_snapshot.get_step(step_id)
    if step_snapshot is None:
        return StepVerificationResult(
            step_id=step_id,
            original_outputs={},
            verified_outputs={},
            matches=False,
            diffs=[],
            attestation=None,
            error=f"Step '{step_id}' not found in original run",
        )

    # Load input content from storage
    inputs: Dict[str, Any] = {}
    try:
        for name, artifact_ref in step_snapshot.inputs.items():
            content = artifact_storage.retrieve_artifact(artifact_ref)
            inputs[name] = content
    except Exception as e:
        return StepVerificationResult(
            step_id=step_id,
            original_outputs=dict(step_snapshot.outputs),
            verified_outputs={},
            matches=False,
            diffs=[],
            attestation=None,
            error=f"Failed to load inputs: {e}",
        )

    # Execute step
    try:
        outputs = executor.execute(inputs)
    except Exception as e:
        return StepVerificationResult(
            step_id=step_id,
            original_outputs=dict(step_snapshot.outputs),
            verified_outputs={},
            matches=False,
            diffs=[],
            attestation=None,
            error=f"Executor failed: {type(e).__name__}: {e}",
        )

    # Create artifact refs for verified outputs
    verified_outputs: Dict[str, ArtifactRef] = {}
    for name, content in outputs.items():
        # Determine artifact kind from original (or default to JSON)
        original_ref = step_snapshot.outputs.get(name)
        kind = original_ref.artifact_kind if original_ref else ArtifactKind.JSON

        # Compute hash for verified output
        if kind == ArtifactKind.TEXT and isinstance(content, str):
            content_hash = compute_text_hash(content)
        elif kind in (ArtifactKind.BYTES, ArtifactKind.FILE) and isinstance(
            content, (bytes, bytearray)
        ):
            import hashlib

            digest = hashlib.sha256(bytes(content)).hexdigest()
            content_hash = f"sha256:{digest}"
        else:
            content_hash = compute_hash(content)

        # Create artifact ref (note: we don't store, just compute hash)
        verified_ref = ArtifactRef(
            artifact_id=f"verified_{uuid4().hex[:12]}",
            run_id=run_id,
            step_id=step_id,
            artifact_type=ArtifactType.OUTPUT,
            artifact_kind=kind,
            uri=f"memory://{step_id}/{name}",  # Not actually stored
            content_hash=content_hash,
            content_type="application/json",
            size_bytes=0,  # Not computed for verification
        )
        verified_outputs[name] = verified_ref

    # Compute diffs for all outputs
    all_output_names = set(step_snapshot.outputs.keys()) | set(outputs.keys())
    diffs: List[ArtifactDiff] = []

    for name in sorted(all_output_names):
        original_ref = step_snapshot.outputs.get(name)
        verified_ref = verified_outputs.get(name)
        diff = compute_artifact_diff(name, original_ref, verified_ref)
        diffs.append(diff)

    # Check if all matched
    matches = all(diff.diff_type == DiffType.MATCH for diff in diffs)

    # Create attestation if needed
    attestation: Optional[NonDeterminismAttestation] = None
    if not matches:
        # Get model identity from step snapshot if available
        model_identity: Optional[ModelIdentity] = None
        # Note: ModelIdentity not directly available in snapshot; would need
        # to be passed separately or retrieved from RunRecord

        reason = classify_nondeterminism(
            step_type=step_snapshot.step_type,
            diffs=diffs,
            model_identity=model_identity,
        )

        attestation = create_nondeterminism_attestation(
            step_id=step_id,
            diffs=diffs,
            reason=reason,
            model_identity=model_identity,
            replay_strategy=ReplayStrategy.RE_RUN,
        )

        # Add to context
        context.attestations.append(attestation)

    return StepVerificationResult(
        step_id=step_id,
        original_outputs=dict(step_snapshot.outputs),
        verified_outputs=verified_outputs,
        matches=matches,
        diffs=diffs,
        attestation=attestation,
        error=None,
    )


def create_verification_report(context: VerificationContext) -> VerificationReport:
    """
    Create a verification report from a completed verification context.

    This function compiles all step results into a final report with
    summary statistics and human-readable summary.

    Args:
        context: Completed verification context

    Returns:
        VerificationReport with complete results

    Example:
        >>> report = create_verification_report(context)
        >>> print(report.summary)
        All 3 verified steps produced matching outputs.
    """
    step_results = context.step_results
    attestations = context.attestations

    # Compute statistics
    steps_verified = len(step_results)
    steps_matched = sum(1 for r in step_results.values() if r.matches)
    steps_failed = sum(1 for r in step_results.values() if r.error)
    steps_differed = steps_verified - steps_matched - steps_failed

    overall_match = steps_verified > 0 and steps_matched == steps_verified

    # Generate summary
    if steps_verified == 0:
        summary = "No steps were verified."
    elif overall_match:
        summary = f"All {steps_verified} verified steps produced matching outputs."
    elif steps_failed > 0 and steps_differed == 0:
        summary = (
            f"{steps_matched} of {steps_verified} steps matched. "
            f"{steps_failed} steps failed to execute."
        )
    elif steps_failed == 0:
        summary = (
            f"{steps_matched} of {steps_verified} steps matched. "
            f"{steps_differed} steps produced different outputs."
        )
    else:
        summary = (
            f"{steps_matched} of {steps_verified} steps matched. "
            f"{steps_differed} steps produced different outputs. "
            f"{steps_failed} steps failed to execute."
        )

    return VerificationReport(
        original_run_id=context.original_snapshot.run_id,
        verification_run_id=context.verification_run_id,
        overall_match=overall_match,
        steps_verified=steps_verified,
        steps_matched=steps_matched,
        step_results=dict(step_results),
        attestations=list(attestations),
        summary=summary,
        created_at=datetime.utcnow(),
    )


def verify_run(
    storage: StorageBackend,
    artifact_storage: ArtifactStorage,
    run_id: str,
    executors: Dict[str, StepExecutor],
) -> VerificationReport:
    """
    Verify an entire run by re-executing steps with provided executors.

    This is the primary API for verification (Mode B). It:
    1. Reconstructs the original run snapshot
    2. Verifies each step that has an executor
    3. Generates a complete verification report

    Steps without executors are skipped (not verified).

    Args:
        storage: Storage backend for retrieving run
        artifact_storage: Storage for retrieving artifacts
        run_id: Run to verify
        executors: Dict of step_id → executor

    Returns:
        VerificationReport with complete results

    Example:
        >>> executors = {
        ...     "analyze": MyLLMExecutor(client),
        ...     "validate": MyValidatorExecutor(),
        ... }
        >>> report = verify_run(storage, artifact_storage, run_id, executors)
        >>> print(report.summary)
    """
    # Reconstruct original snapshot
    snapshot = reconstruct_run(storage, run_id)

    # Create verification context
    context = VerificationContext(original_snapshot=snapshot)

    # Verify each step that has an executor
    for step_id, executor in executors.items():
        result = verify_step(
            context=context,
            step_id=step_id,
            executor=executor,
            artifact_storage=artifact_storage,
            run_id=run_id,
        )
        context.step_results[step_id] = result

    # Create report
    return create_verification_report(context)


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "StepExecutor",
    "StepVerificationResult",
    "VerificationContext",
    "VerificationReport",
    "verify_step",
    "verify_run",
    "create_verification_report",
]
