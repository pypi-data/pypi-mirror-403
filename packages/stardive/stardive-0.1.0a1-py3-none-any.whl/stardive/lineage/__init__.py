"""
Lineage Graph Module for Stardive Execution Kernel.

This module provides the lineage graph implementation for tracking data
provenance and dependencies in AI workflows.

Key Components:
- **Node Types** (nodes.py): NodeType, LineageNode, StepNode, ArtifactNode
- **Edge Types** (graph.py): EdgeType, EdgeProvenance, LineageEdge, LineageGraph
- **Query API** (queries.py): LineageTrace, query functions
- **Validation** (validation.py): ValidationIssueType, LineageValidationReport

Design Principles:
1. **Mechanical Derivation**: Graph is built from declared events, never inferred
2. **Single-Run Scope**: v0.1 lineage is single-run only (no cross-run lineage)
3. **Immutable Nodes**: All nodes are frozen (cannot be modified after creation)
4. **Edge Provenance**: Every edge tracks its source event for audit

Edge Source of Truth (NON-NEGOTIABLE):
    - PRODUCES edges come from: StepEndEvent.outputs
    - CONSUMES edges come from: StepStartEvent.inputs

    NO DEPENDENCY INFERENCE IS PERFORMED.
    If it's not declared in events, it's not in the graph.

Canonical Node ID Format:
    - Step node: `step:<run_id>:<step_id>`
    - Artifact node: `artifact:<run_id>:<artifact_id>`

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4) - Lineage + Replay implementation plan
- docs/canonical-ir.md - Event schema and artifact models

Example:
    >>> from stardive.lineage import NodeType, StepNode, ArtifactNode
    >>> from stardive.models.enums import StepStatus
    >>> from stardive.artifacts import ArtifactKind
    >>> from datetime import datetime
    >>>
    >>> # Create a step node
    >>> step_node = StepNode(
    ...     run_id="run_abc123",
    ...     step_id="analyze",
    ...     step_type="llm",
    ...     status=StepStatus.SUCCESS,
    ...     started_at=datetime.now(),
    ... )
    >>> print(step_node.node_id)
    step:run_abc123:analyze
    >>>
    >>> # Create an artifact node
    >>> artifact_node = ArtifactNode(
    ...     run_id="run_abc123",
    ...     artifact_id="result",
    ...     artifact_kind=ArtifactKind.JSON,
    ...     content_hash="sha256:abc123...",
    ...     producer_step_id="analyze",
    ... )
    >>> print(artifact_node.node_id)
    artifact:run_abc123:result
    >>>
    >>> # Query the lineage graph
    >>> from stardive.lineage import get_artifact_lineage, validate_graph
    >>> graph = build_from_run_record(run_record)
    >>> trace = get_artifact_lineage(graph, "result")
    >>> report = validate_graph(graph)
"""

from stardive.lineage.nodes import (
    NodeType,
    LineageNode,
    StepNode,
    ArtifactNode,
)
from stardive.lineage.graph import (
    EdgeType,
    EdgeProvenance,
    LineageEdge,
    LineageGraph,
    build_from_run_record,
    build_from_storage,
    graph_to_dict,
    graph_from_dict,
)
from stardive.lineage.queries import (
    LineageTrace,
    get_artifact_lineage,
    get_artifact_producer,
    get_artifact_consumers,
    get_step_inputs,
    get_step_outputs,
    get_upstream_artifacts,
    get_downstream_artifacts,
)
from stardive.lineage.validation import (
    ValidationIssueType,
    LineageValidationIssue,
    LineageValidationReport,
    validate_graph,
    get_issue_severity,
)

__all__ = [
    # Node Types
    "NodeType",
    "LineageNode",
    "StepNode",
    "ArtifactNode",
    # Edge Types
    "EdgeType",
    "EdgeProvenance",
    "LineageEdge",
    "LineageGraph",
    # Builders
    "build_from_run_record",
    "build_from_storage",
    # Serialization
    "graph_to_dict",
    "graph_from_dict",
    # Query API
    "LineageTrace",
    "get_artifact_lineage",
    "get_artifact_producer",
    "get_artifact_consumers",
    "get_step_inputs",
    "get_step_outputs",
    "get_upstream_artifacts",
    "get_downstream_artifacts",
    # Validation
    "ValidationIssueType",
    "LineageValidationIssue",
    "LineageValidationReport",
    "validate_graph",
    "get_issue_severity",
]
