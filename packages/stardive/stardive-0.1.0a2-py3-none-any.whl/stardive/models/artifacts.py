"""
Artifact Models for Stardive Execution Kernel.

This module defines models for tracking data artifacts (inputs, outputs, intermediate
data) throughout workflow execution with tamper-evident references and storage abstraction.

Artifacts are the data that flows through a workflow:
- **Inputs**: Data provided to steps
- **Outputs**: Results produced by steps
- **Intermediate**: Temporary data between steps

Key Principles:
1. **Content-Addressed Storage**: Artifacts identified by SHA256 hash of content
2. **Storage Abstraction**: URI-based reference separates logical reference from physical storage
3. **Tamper Detection**: Content hashes enable verification that data hasn't been modified
4. **Size-Based Strategy**: Small artifacts inline in DB, large artifacts in object storage
5. **Security**: Redaction support for PII and secrets

Storage Strategy:
- Small artifacts (<1MB): Stored inline in database for fast access
- Large artifacts (>1MB): Stored in object storage (S3, GCS) with URI reference
- Content hash always computed regardless of storage location
- URI format indicates storage backend (db://, s3://, file://)

Audit Implications:
- Content hashes provide tamper-evident audit trail
- Redaction flags indicate PII/secret removal
- Size tracking enables storage optimization
- Schema hashes enable validation

For detailed specifications, see:
- docs/canonical-ir.md - Artifact reference strategy
- docs/identity-provenance.md - Redaction and security

Security Note:
    Artifacts containing secrets or PII must be redacted before storage.
    The redaction engine (implemented in Phase 5) will automatically detect
    and redact sensitive data, marking artifacts with redacted=True.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from ..artifacts import ArtifactKind
from .enums import ArtifactType


# ============================================================================
# Artifact Models
# ============================================================================


class ArtifactRef(BaseModel):
    """
    Reference to an artifact (input, output, or intermediate data).

    The reference itself is authoritative (stored in RunRecord), but the
    actual artifact content is stored separately based on size.

    Purpose:
        Artifacts represent data flowing through a workflow. This model provides
        a content-addressed, tamper-evident reference to that data while
        abstracting the storage backend.

        By separating the reference from the content, we:
        - Store small data inline in DB (fast access)
        - Store large data in object storage (cost-effective)
        - Maintain tamper detection via content hash
        - Support multiple storage backends

    Storage Strategy:
        The storage location is determined by artifact size:

        | Size      | Storage    | URI Format              | Use Case           |
        |-----------|------------|-------------------------|--------------------|
        | <1MB      | Database   | db://artifacts/{id}     | Fast inline access |
        | >1MB      | S3/GCS     | s3://bucket/path/{id}   | Cost-effective     |
        | Any       | Filesystem | file:///tmp/{id}        | Local development  |

        Content hash is ALWAYS computed, regardless of storage location.

    Tamper Detection:
        The content_hash (SHA256) enables verification that artifact content
        hasn't been modified since creation. This is critical for:
        - Audit integrity (data hasn't been tampered with)
        - Reproducibility (exact same inputs produce same outputs)
        - Compliance (prove data hasn't changed)

    Redaction:
        Artifacts containing secrets or PII are redacted before storage:
        - Redaction engine detects patterns (API keys, SSNs, emails)
        - Content is redacted ([REDACTED] marker)
        - redacted=True flag marks the artifact
        - redaction_reason explains why

        This provides audit trail without exposing sensitive data.

    Examples:
        Small JSON input (stored in database):
            ArtifactRef(
                artifact_id="art_input_001",
                run_id="run_abc123",
                step_id="analyze",
                artifact_type=ArtifactType.INPUT,
                artifact_kind=ArtifactKind.JSON,
                uri="db://artifacts/art_input_001",
                content_hash="sha256:abc123...",
                content_type="application/json",
                size_bytes=1024
            )

        Large PDF output (stored in S3):
            ArtifactRef(
                artifact_id="art_output_002",
                run_id="run_abc123",
                step_id="generate_report",
                artifact_type=ArtifactType.OUTPUT,
                artifact_kind=ArtifactKind.FILE,
                uri="s3://stardive-artifacts/run_abc123/art_output_002",
                content_hash="sha256:def456...",
                content_type="application/pdf",
                size_bytes=5242880  # 5MB
            )

        Redacted artifact (contained PII):
            ArtifactRef(
                artifact_id="art_intermediate_003",
                run_id="run_abc123",
                step_id="process_data",
                artifact_type=ArtifactType.INTERMEDIATE,
                artifact_kind=ArtifactKind.JSON,
                uri="db://artifacts/art_intermediate_003",
                content_hash="sha256:ghi789...",
                content_type="application/json",
                size_bytes=512,
                redacted=True,
                redaction_reason="PII_DETECTED"
            )
    """

    artifact_id: str = Field(
        default_factory=lambda: f"art_{uuid4().hex[:12]}",
        description="Unique artifact identifier",
    )
    run_id: str = Field(..., description="Run that produced this artifact")
    step_id: str = Field(..., description="Step that produced this artifact")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    artifact_kind: ArtifactKind = Field(
        ...,
        description="Content kind for serialization (json, text, bytes, file)",
    )

    # Content Reference
    uri: str = Field(
        ...,
        description="Storage URI (db://, s3://, file://)",
        examples=[
            "db://artifacts/art_abc123",
            "s3://bucket/path/artifact",
            "file:///tmp/artifact.json",
        ],
    )
    content_hash: str = Field(
        ...,
        description="SHA256 hash of artifact content (AUTHORITATIVE)",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )
    content_type: str = Field(
        ...,
        description="MIME type of content",
        examples=["application/json", "text/plain", "application/pdf"],
    )
    size_bytes: int = Field(..., description="Size of artifact in bytes", ge=0)

    # Schema Validation (optional)
    schema_hash: Optional[str] = Field(
        None,
        description="Hash of JSON schema for validation (if applicable)",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )

    # Redaction
    redacted: bool = Field(
        False, description="Whether content was redacted for PII/secrets"
    )
    redaction_reason: Optional[str] = Field(
        None,
        description="Reason for redaction",
        examples=["PII_DETECTED", "SECRET_DETECTED", "POLICY_REQUIRED"],
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When artifact was created",
    )

    model_config = {"frozen": True}


class ArtifactSpec(BaseModel):
    """
    Expected artifact specification in a RunPlan.

    This is a **declaration** of what artifacts a workflow should produce,
    enabling pre-execution validation and post-execution verification.

    Purpose:
        Before executing a workflow, we can declare what artifacts it should
        produce. This enables:
        - **Validation**: Check that workflow produces expected outputs
        - **Lineage**: Pre-declare artifact lineage (which steps produce what)
        - **Schema validation**: Verify outputs match expected schemas
        - **Required checks**: Fail if required artifacts are missing

    Use Cases:
        1. **Workflow Validation**:
           Declare that "analyze" step must produce "credit_score.json"
           If step completes without producing it → validation error

        2. **Schema Enforcement**:
           Declare expected schema hash for output
           If actual output doesn't match schema → validation error

        3. **Audit Requirements**:
           Mark certain artifacts as required for compliance
           System ensures they are produced and retained

    Workflow Definition (YAML):
        ```yaml
        version: "1.0"
        name: credit-analysis

        expected_artifacts:
          - artifact_id: credit_score
            artifact_type: output
            produced_by_step: analyze
            content_type: application/json
            schema_hash: sha256:abc123...  # Validated against actual output
            required: true  # Workflow fails if not produced
        ```

    Examples:
        Required JSON output with schema:
            ArtifactSpec(
                artifact_id="credit_score",
                artifact_type=ArtifactType.OUTPUT,
                produced_by_step="analyze",
                content_type="application/json",
                schema_hash="sha256:abc123...",
                required=True
            )

        Optional intermediate data:
            ArtifactSpec(
                artifact_id="raw_data_cache",
                artifact_type=ArtifactType.INTERMEDIATE,
                produced_by_step="fetch_data",
                content_type="application/octet-stream",
                required=False
            )

        Required PDF report:
            ArtifactSpec(
                artifact_id="audit_report",
                artifact_type=ArtifactType.OUTPUT,
                produced_by_step="generate_report",
                content_type="application/pdf",
                required=True
            )
    """

    artifact_id: str = Field(..., description="Expected artifact identifier")
    artifact_type: ArtifactType = Field(..., description="Type of artifact")
    produced_by_step: str = Field(
        ..., description="Step ID that should produce this artifact"
    )
    content_type: Optional[str] = Field(
        None, description="Expected MIME type (if known)"
    )
    schema_hash: Optional[str] = Field(
        None, description="Expected schema hash for validation"
    )
    required: bool = Field(True, description="Whether this artifact is required")
    
    model_config = {"frozen": True}


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "ArtifactRef",
    "ArtifactSpec",
]
