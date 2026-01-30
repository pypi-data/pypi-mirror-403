"""
Lineage Graph Nodes for Stardive Execution Kernel.

This module defines the node types used in the lineage graph:
- **NodeType**: Enum distinguishing step and artifact nodes
- **LineageNode**: Base class for all lineage nodes (frozen/immutable)
- **StepNode**: Node representing a step execution
- **ArtifactNode**: Node representing an artifact (input, output, intermediate)

Key Principles:
1. **Immutable**: All nodes are frozen (cannot be modified after creation)
2. **Canonical IDs**: Node IDs follow a predictable format for determinism
3. **Single-Run Scope**: v0.1 lineage is single-run only (no cross-run lineage)
4. **Declared Dependencies**: Edges are derived from events, never inferred

Canonical Node ID Format:
    - Step node: `step:<run_id>:<step_id>`
    - Artifact node: `artifact:<run_id>:<artifact_id>`

    These IDs are predictable, serializable, and usable as dict keys.

Frozen Models:
    All lineage models use `frozen=True` Pydantic config. This ensures:
    - Immutability after construction
    - Hashability (can be used as dict keys)
    - Thread safety
    - Audit-grade integrity

    Validators use `object.__setattr__()` to set fields on frozen models.

Design Rationale:
    Lineage nodes are immutable snapshots of execution state. Once a step or
    artifact is recorded, its node representation cannot change. This is
    fundamental to Stardive's audit-grade guarantee.

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4.1) - Lineage graph implementation
- docs/canonical-ir.md - Event schema and artifact models
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator

from stardive.artifacts import ArtifactKind
from stardive.models.enums import StepStatus


# ============================================================================
# Node Type Enum
# ============================================================================


class NodeType(str, Enum):
    """
    Type of node in the lineage graph.

    The lineage graph contains two types of nodes:
    - **STEP**: Represents a step execution (transformation)
    - **ARTIFACT**: Represents data (input, output, or intermediate)

    Edges connect these nodes:
    - PRODUCES: step → artifact (step creates artifact)
    - CONSUMES: artifact → step (step uses artifact)

    Examples:
        >>> node_type = NodeType.STEP
        >>> print(node_type.value)
        'step'

        >>> node_type = NodeType.ARTIFACT
        >>> print(node_type.value)
        'artifact'
    """

    STEP = "step"
    ARTIFACT = "artifact"


# ============================================================================
# Base Node Class
# ============================================================================


class LineageNode(BaseModel):
    """
    Base class for all lineage graph nodes.

    All nodes have:
    - A canonical `node_id` for unique identification
    - A `node_type` distinguishing step vs artifact
    - Optional `metadata` for extensibility

    This is a frozen (immutable) model. Once created, nodes cannot be modified.

    Canonical ID Format:
        The `node_id` field is the canonical identifier for this node.
        It follows a predictable format:
        - Step: `step:<run_id>:<step_id>`
        - Artifact: `artifact:<run_id>:<artifact_id>`

        This ensures:
        - Deterministic serialization
        - Stable test assertions
        - Predictable CLI output
        - Usable as dict keys

    Implementation Note:
        `node_id` is a real Pydantic field populated by `@model_validator`,
        NOT a `@property`. This ensures proper serialization and compatibility
        with Pydantic's JSON encoding.

        Validators use `object.__setattr__()` because the model is frozen.

    Examples:
        This is an abstract base class. See StepNode and ArtifactNode for
        concrete implementations.
    """

    model_config = ConfigDict(frozen=True)

    node_id: str = ""  # Populated by validator in subclasses
    node_type: NodeType
    metadata: Dict[str, Any] = {}


# ============================================================================
# Step Node
# ============================================================================


class StepNode(LineageNode):
    """
    Lineage node representing a step execution.

    A step is a unit of computation in a workflow. StepNode captures:
    - What step was executed (step_id, step_type)
    - When it ran (started_at, ended_at)
    - What happened (status)

    Canonical ID:
        `step:<run_id>:<step_id>`

        Example: `step:run_abc123:analyze`

    Immutability:
        StepNode is frozen. All fields are set at construction time and
        cannot be modified afterwards. The `node_id` is computed from
        `run_id` and `step_id` using a model validator.

    Relationship to Events:
        StepNode is derived from StepStartEvent and StepEndEvent:
        - `run_id`: from event.run_id
        - `step_id`: from event.step_id
        - `step_type`: from StepSpec (if available) or inferred
        - `status`: from StepEndEvent.status
        - `started_at`: from StepStartEvent.timestamp
        - `ended_at`: from StepEndEvent.timestamp

    Examples:
        >>> from datetime import datetime
        >>> from stardive.models.enums import StepStatus
        >>> from stardive.lineage.nodes import StepNode
        >>>
        >>> node = StepNode(
        ...     run_id="run_abc123",
        ...     step_id="analyze",
        ...     step_type="llm",
        ...     status=StepStatus.SUCCESS,
        ...     started_at=datetime(2024, 12, 27, 10, 30, 0),
        ...     ended_at=datetime(2024, 12, 27, 10, 32, 30),
        ... )
        >>> print(node.node_id)
        step:run_abc123:analyze
        >>> print(node.node_type)
        NodeType.STEP
    """

    model_config = ConfigDict(frozen=True)

    # Fixed node type
    node_type: Literal[NodeType.STEP] = NodeType.STEP

    # Node ID computed by validator
    node_id: str = ""

    # Step identification
    run_id: str
    step_id: str
    step_type: str  # e.g., "llm", "python", "sql", "http"

    # Execution status
    status: StepStatus

    # Timestamps
    started_at: datetime
    ended_at: Optional[datetime] = None

    @model_validator(mode="after")
    def set_node_id(self) -> "StepNode":
        """Compute canonical node ID from run_id and step_id."""
        # Use object.__setattr__ because model is frozen
        object.__setattr__(self, "node_id", f"step:{self.run_id}:{self.step_id}")
        return self


# ============================================================================
# Artifact Node
# ============================================================================


class ArtifactNode(LineageNode):
    """
    Lineage node representing an artifact (data).

    An artifact is a piece of data in a workflow (input, output, or intermediate).
    ArtifactNode captures:
    - What artifact it is (artifact_id, artifact_kind)
    - Its content hash for integrity verification
    - Which step produced it (producer_step_id, optional for orphans)

    Canonical ID:
        `artifact:<run_id>:<artifact_id>`

        Example: `artifact:run_abc123:credit_score`

    Immutability:
        ArtifactNode is frozen. All fields are set at construction time and
        cannot be modified afterwards. The `node_id` is computed from
        `run_id` and `artifact_id` using a model validator.

    Single-Run Lineage (v0.1):
        In v0.1, lineage is single-run only. The `run_id` field identifies
        which run this artifact belongs to. Cross-run lineage (where artifacts
        from one run are consumed by another) is deferred to v0.2.

        For this reason, `producer_run_id` was dropped in v0.1 — it would
        always equal `run_id` in single-run lineage.

    Orphan Artifacts:
        Some artifacts may not have a producer step (e.g., external inputs
        provided at run start). In this case, `producer_step_id` is None.
        The validation module will flag these as `ORPHAN_ARTIFACT` warnings.

    Relationship to Events:
        ArtifactNode is derived from StepEndEvent.outputs:
        - `run_id`: from event.run_id
        - `artifact_id`: from ArtifactRef.artifact_id
        - `artifact_kind`: from ArtifactRef.artifact_kind
        - `content_hash`: from ArtifactRef.content_hash
        - `producer_step_id`: from event.step_id

    Duplicate Producer Semantics:
        Identity is based on `artifact_id` within a run, NOT on `content_hash`.
        Two PRODUCES edges targeting the same `artifact:<run_id>:<artifact_id>`
        is a validation error (DUPLICATE_PRODUCER), even if they have the
        same `content_hash`.

    Examples:
        Artifact with producer:
            >>> from stardive.artifacts import ArtifactKind
            >>> from stardive.lineage.nodes import ArtifactNode
            >>>
            >>> node = ArtifactNode(
            ...     run_id="run_abc123",
            ...     artifact_id="credit_score",
            ...     artifact_kind=ArtifactKind.JSON,
            ...     content_hash="sha256:abc123def456...",
            ...     producer_step_id="analyze",
            ... )
            >>> print(node.node_id)
            artifact:run_abc123:credit_score
            >>> print(node.node_type)
            NodeType.ARTIFACT

        Orphan artifact (external input):
            >>> node = ArtifactNode(
            ...     run_id="run_abc123",
            ...     artifact_id="user_data",
            ...     artifact_kind=ArtifactKind.JSON,
            ...     content_hash="sha256:789xyz...",
            ...     producer_step_id=None,  # External input
            ... )
    """

    model_config = ConfigDict(frozen=True)

    # Fixed node type
    node_type: Literal[NodeType.ARTIFACT] = NodeType.ARTIFACT

    # Node ID computed by validator
    node_id: str = ""

    # Artifact identification
    artifact_id: str
    artifact_name: Optional[str] = None  # Human-readable name from step outputs/inputs
    artifact_kind: ArtifactKind
    content_hash: str

    # Run context
    run_id: str  # Run this artifact belongs to (canonical ID source)

    # Producer (optional for orphan artifacts)
    producer_step_id: Optional[str] = None

    # NOTE: producer_run_id dropped in v0.1 (redundant in single-run lineage)

    @model_validator(mode="after")
    def set_node_id(self) -> "ArtifactNode":
        """Compute canonical node ID from run_id and artifact_id."""
        # Use object.__setattr__ because model is frozen
        object.__setattr__(self, "node_id", f"artifact:{self.run_id}:{self.artifact_id}")
        return self


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "NodeType",
    "LineageNode",
    "StepNode",
    "ArtifactNode",
]
