"""
Stardive Replay Module - Snapshot Replay and Verification.

This module provides two distinct replay capabilities:

Mode A: Snapshot Reconstruction (Always Available)
-------------------------------------------------
Reconstruct read-only views of past executions using stored artifacts and events.
No re-execution required.

    from stardive.replay import reconstruct_run, reconstruct_step

    # Reconstruct entire run
    snapshot = reconstruct_run(storage, "run_abc123")
    print(snapshot.status)  # RunStatus.COMPLETED

    # Access step details
    step = snapshot.get_step("analyze")
    print(step.inputs)  # {"data": ArtifactRef(...)}
    print(step.outputs)  # {"result": ArtifactRef(...)}

Mode B: Verification Re-run (Optional, Executor-Dependent)
---------------------------------------------------------
Re-execute steps with user-provided executors and compare outputs.
Generates NonDeterminismAttestation when outputs differ.

    from stardive.replay import verify_run, StepExecutor

    class MyExecutor:
        def execute(self, inputs: dict) -> dict:
            # Re-run the step logic
            return {"result": process(inputs["data"])}

    executors = {"analyze": MyExecutor()}
    report = verify_run(storage, artifact_storage, "run_abc123", executors)

    if report.overall_match:
        print("All steps verified successfully!")
    else:
        print(f"Summary: {report.summary}")
        for attestation in report.attestations:
            print(f"Non-deterministic: {attestation.step_id}")

Key Components:
- **StepSnapshotView**: Read-only view of a step's execution
- **RunSnapshotView**: Read-only view of an entire run
- **DiffType**: Classification of artifact differences
- **ArtifactDiff**: Detailed diff between original and verified artifacts
- **NonDeterminismReason**: Classification of why outputs differ
- **StepVerificationResult**: Result of verifying a single step
- **VerificationReport**: Complete verification report

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4.2) - Replay requirements
- docs/replay-design.md - Replay architecture
"""

# Snapshot View (Mode A)
from .snapshot_view import (
    StepSnapshotView,
    RunSnapshotView,
    reconstruct_run,
    reconstruct_run_from_record,
    reconstruct_step,
    reconstruct_step_from_record,
)

# Diff Computation
from .diff import (
    DiffType,
    ArtifactDiff,
    compute_artifact_diff,
    explain_diff,
    summarize_diffs,
)

# Non-Determinism Attestation
from .attestation import (
    NonDeterminismReason,
    classify_nondeterminism,
    classify_nondeterminism_from_model,
    create_nondeterminism_attestation,
    create_attestation_from_diffs,
    explain_nondeterminism_reason,
)

# Verification (Mode B)
from .verification import (
    StepExecutor,
    StepVerificationResult,
    VerificationContext,
    VerificationReport,
    verify_step,
    verify_run,
    create_verification_report,
)

__all__ = [
    # Snapshot View (Mode A)
    "StepSnapshotView",
    "RunSnapshotView",
    "reconstruct_run",
    "reconstruct_run_from_record",
    "reconstruct_step",
    "reconstruct_step_from_record",
    # Diff Computation
    "DiffType",
    "ArtifactDiff",
    "compute_artifact_diff",
    "explain_diff",
    "summarize_diffs",
    # Non-Determinism Attestation
    "NonDeterminismReason",
    "classify_nondeterminism",
    "classify_nondeterminism_from_model",
    "create_nondeterminism_attestation",
    "create_attestation_from_diffs",
    "explain_nondeterminism_reason",
    # Verification (Mode B)
    "StepExecutor",
    "StepVerificationResult",
    "VerificationContext",
    "VerificationReport",
    "verify_step",
    "verify_run",
    "create_verification_report",
]
