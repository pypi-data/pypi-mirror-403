"""
Lineage Graph Construction for Stardive Execution Kernel.

This module defines the edge types and graph structure for the lineage graph:
- **EdgeType**: Enum distinguishing produces and consumes edges
- **EdgeProvenance**: Audit trail for how an edge was derived
- **LineageEdge**: A directed edge in the lineage graph
- **LineageGraph**: The complete lineage graph for a run

Key Principles:
1. **Edge Source of Truth (NON-NEGOTIABLE)**:
   - PRODUCES edges come from: `StepEndEvent.outputs`
   - CONSUMES edges come from: `StepStartEvent.inputs`
   - NO DEPENDENCY INFERENCE IS PERFORMED
   - If it's not declared in events, it's not in the graph

2. **Immutable**: All edge and graph models are frozen (cannot be modified)
3. **Provenance Tracking**: Every edge tracks its source event for audit
4. **Single-Run Scope**: v0.1 lineage is single-run only
5. **Deterministic Serialization**: Edges sorted by canonical key

Canonical Edge Sort Key:
    (edge_type, source_id, target_id, source_event_index)

    This ensures:
    - Deterministic JSON serialization
    - Stable test assertions
    - Predictable CLI output

Design Rationale:
    Lineage edges represent data flow relationships:
    - PRODUCES: A step created an artifact (step → artifact)
    - CONSUMES: A step used an artifact as input (artifact → step)

    Every edge is verifiably traceable to an immutable stored event.
    This is fundamental to Stardive's audit-grade guarantee.

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4.1) - Lineage graph implementation
- docs/canonical-ir.md - Event schema and artifact models
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from stardive.lineage.nodes import ArtifactNode, LineageNode, NodeType, StepNode
from stardive.models.enums import StepStatus
from stardive.models.events import (
    Event,
    RunEndEvent,
    RunStartEvent,
    StepEndEvent,
    StepStartEvent,
)
from stardive.models.run_record import RunRecord


# ============================================================================
# Edge Type Enum
# ============================================================================


class EdgeType(str, Enum):
    """
    Type of edge in the lineage graph.

    The lineage graph has two types of directed edges:
    - **PRODUCES**: step → artifact (step creates artifact)
    - **CONSUMES**: artifact → step (step uses artifact as input)

    Edge Direction:
        The direction represents data flow:
        - Data flows OUT of steps via PRODUCES edges
        - Data flows INTO steps via CONSUMES edges

    Source of Truth (NON-NEGOTIABLE):
        - PRODUCES edges come ONLY from `StepEndEvent.outputs`
        - CONSUMES edges come ONLY from `StepStartEvent.inputs`
        - NO DEPENDENCY INFERENCE IS PERFORMED

    Examples:
        >>> edge_type = EdgeType.PRODUCES
        >>> print(edge_type.value)
        'produces'

        >>> edge_type = EdgeType.CONSUMES
        >>> print(edge_type.value)
        'consumes'
    """

    PRODUCES = "produces"  # step → artifact
    CONSUMES = "consumes"  # artifact → step


# ============================================================================
# Edge Provenance
# ============================================================================


class EdgeProvenance(BaseModel):
    """
    Audit trail for how a lineage edge was derived.

    Every edge must be verifiably traceable to immutable stored events.
    This is fundamental to Stardive's audit-grade guarantee.

    Purpose:
        EdgeProvenance answers "where did this edge come from?" with:
        - Which event type declared this relationship
        - Which event in the sequence (by index)
        - Which field in the event (inputs or outputs)
        - Optionally, the event's hash for cryptographic verification

    Stable Anchor:
        The `source_event_index` is the primary stable anchor. It identifies
        the event by its position in the event sequence, which is immutable
        once the run is complete.

        `source_event_hash` is optional but enables cryptographic verification
        against the hash chain.

    Derivation:
        The `derivation` field is always "declared" in v0.1. This explicitly
        documents that edges are derived from declared relationships, never
        inferred from data flow patterns or heuristics.

    Examples:
        PRODUCES edge from StepEndEvent.outputs:
            EdgeProvenance(
                source_event_type="StepEndEvent",
                source_event_index=3,
                source_event_hash="sha256:abc123...",
                source_field="outputs",
                derivation="declared"
            )

        CONSUMES edge from StepStartEvent.inputs:
            EdgeProvenance(
                source_event_type="StepStartEvent",
                source_event_index=2,
                source_event_hash="sha256:def456...",
                source_field="inputs",
                derivation="declared"
            )
    """

    model_config = ConfigDict(frozen=True)

    source_event_type: str = Field(
        ...,
        description="Event type that declared this edge (e.g., 'StepStartEvent', 'StepEndEvent')",
    )
    source_event_index: int = Field(
        ...,
        description="Index of the source event in the event sequence (stable anchor)",
        ge=0,
    )
    source_event_hash: Optional[str] = Field(
        None,
        description="Hash of the source event (optional, for cryptographic verification)",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )
    source_field: str = Field(
        ...,
        description="Field in the event that declared this edge (e.g., 'inputs', 'outputs')",
    )
    derivation: Literal["declared"] = Field(
        "declared",
        description="How this edge was derived (always 'declared', never inferred)",
    )


# ============================================================================
# Lineage Edge
# ============================================================================


class LineageEdge(BaseModel):
    """
    A directed edge in the lineage graph.

    Edges connect nodes in the lineage graph:
    - PRODUCES: source=step, target=artifact
    - CONSUMES: source=artifact, target=step

    Immutability:
        LineageEdge is frozen. Once created, edges cannot be modified.
        This ensures audit-grade integrity.

    Provenance:
        Every edge has an `EdgeProvenance` that traces back to the source
        event. This is not optional — it's required for audit compliance.

    Sort Key:
        Edges are sorted by canonical key for deterministic serialization:
        `(edge_type, source_id, target_id, source_event_index)`

        This ensures stable JSON output, test assertions, and CLI display.

    Examples:
        PRODUCES edge (step created artifact):
            LineageEdge(
                source_id="step:run_abc123:analyze",
                target_id="artifact:run_abc123:credit_score",
                edge_type=EdgeType.PRODUCES,
                provenance=EdgeProvenance(
                    source_event_type="StepEndEvent",
                    source_event_index=3,
                    source_field="outputs",
                )
            )

        CONSUMES edge (step used artifact):
            LineageEdge(
                source_id="artifact:run_abc123:user_data",
                target_id="step:run_abc123:analyze",
                edge_type=EdgeType.CONSUMES,
                provenance=EdgeProvenance(
                    source_event_type="StepStartEvent",
                    source_event_index=2,
                    source_field="inputs",
                )
            )
    """

    model_config = ConfigDict(frozen=True)

    source_id: str = Field(
        ...,
        description="Canonical node ID of the source node",
    )
    target_id: str = Field(
        ...,
        description="Canonical node ID of the target node",
    )
    edge_type: EdgeType = Field(
        ...,
        description="Type of edge (produces or consumes)",
    )
    provenance: EdgeProvenance = Field(
        ...,
        description="Audit trail for how this edge was derived",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for extensibility",
    )

    def sort_key(self) -> tuple:
        """
        Canonical sort key for deterministic ordering.

        Returns:
            Tuple of (edge_type, source_id, target_id, source_event_index)

        This ensures:
        - Deterministic JSON serialization
        - Stable test assertions
        - Predictable CLI output

        Example:
            >>> edge = LineageEdge(
            ...     source_id="step:run_abc:analyze",
            ...     target_id="artifact:run_abc:result",
            ...     edge_type=EdgeType.PRODUCES,
            ...     provenance=EdgeProvenance(
            ...         source_event_type="StepEndEvent",
            ...         source_event_index=3,
            ...         source_field="outputs"
            ...     )
            ... )
            >>> edge.sort_key()
            ('produces', 'step:run_abc:analyze', 'artifact:run_abc:result', 3)
        """
        return (
            self.edge_type.value,
            self.source_id,
            self.target_id,
            self.provenance.source_event_index,
        )


# ============================================================================
# Lineage Graph
# ============================================================================


class LineageGraph(BaseModel):
    """
    Complete lineage graph for a single run.

    The lineage graph represents the data flow within a run:
    - Nodes are steps and artifacts
    - Edges show which steps produced and consumed which artifacts

    Single-Run Scope (v0.1):
        This lineage graph is scoped to a single run. Cross-run lineage
        (where artifacts from one run are consumed by another) is deferred
        to v0.2.

    Construction:
        LineageGraph is built from a RunRecord using `build_from_run_record()`:
        1. Extract step nodes from StepStartEvent/StepEndEvent pairs
        2. Extract artifact nodes from StepEndEvent.outputs
        3. Build PRODUCES edges from StepEndEvent.outputs
        4. Build CONSUMES edges from StepStartEvent.inputs
        5. Populate EdgeProvenance for each edge

    Deterministic Serialization:
        - Nodes are stored in a dict keyed by canonical node_id
        - Edges are sorted by canonical sort key before serialization
        - This ensures stable JSON output

    Validation:
        After construction, use `validate_graph()` from the validation module
        to check for issues like orphan artifacts, missing inputs, etc.
        The graph builder is best-effort and does not throw exceptions.

    Examples:
        Simple linear workflow:
            >>> # run: step_a → artifact_x → step_b → artifact_y
            >>> graph = LineageGraph(
            ...     run_id="run_abc123",
            ...     nodes={
            ...         "step:run_abc123:step_a": StepNode(...),
            ...         "artifact:run_abc123:artifact_x": ArtifactNode(...),
            ...         "step:run_abc123:step_b": StepNode(...),
            ...         "artifact:run_abc123:artifact_y": ArtifactNode(...),
            ...     },
            ...     edges=[
            ...         LineageEdge(source_id="step:...:step_a", target_id="artifact:...:artifact_x", ...),
            ...         LineageEdge(source_id="artifact:...:artifact_x", target_id="step:...:step_b", ...),
            ...         LineageEdge(source_id="step:...:step_b", target_id="artifact:...:artifact_y", ...),
            ...     ],
            ...     created_at=datetime.utcnow()
            ... )
    """

    model_config = ConfigDict(frozen=True)

    run_id: str = Field(
        ...,
        description="Run this graph represents",
    )
    nodes: Dict[str, LineageNode] = Field(
        default_factory=dict,
        description="All nodes in the graph, keyed by canonical node_id",
    )
    edges: List[LineageEdge] = Field(
        default_factory=list,
        description="All edges in the graph, sorted by canonical sort key",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this graph was created",
    )

    def get_node(self, node_id: str) -> Optional[LineageNode]:
        """
        Get a node by its canonical ID.

        Args:
            node_id: Canonical node ID (e.g., "step:run_abc:analyze")

        Returns:
            The node if found, None otherwise
        """
        return self.nodes.get(node_id)

    def get_step_node(self, step_id: str) -> Optional[StepNode]:
        """
        Get a step node by step_id.

        Args:
            step_id: The step identifier (not the full canonical node_id)

        Returns:
            The StepNode if found, None otherwise
        """
        node_id = f"step:{self.run_id}:{step_id}"
        node = self.nodes.get(node_id)
        if isinstance(node, StepNode):
            return node
        return None

    def get_artifact_node(self, artifact_id: str) -> Optional[ArtifactNode]:
        """
        Get an artifact node by artifact_id.

        Args:
            artifact_id: The artifact identifier (not the full canonical node_id)

        Returns:
            The ArtifactNode if found, None otherwise
        """
        node_id = f"artifact:{self.run_id}:{artifact_id}"
        node = self.nodes.get(node_id)
        if isinstance(node, ArtifactNode):
            return node
        return None

    def get_edges_from(self, node_id: str) -> List[LineageEdge]:
        """
        Get all edges originating from a node.

        Args:
            node_id: Canonical node ID

        Returns:
            List of edges where source_id == node_id
        """
        return [e for e in self.edges if e.source_id == node_id]

    def get_edges_to(self, node_id: str) -> List[LineageEdge]:
        """
        Get all edges targeting a node.

        Args:
            node_id: Canonical node ID

        Returns:
            List of edges where target_id == node_id
        """
        return [e for e in self.edges if e.target_id == node_id]

    @property
    def step_nodes(self) -> List[StepNode]:
        """Get all step nodes in the graph."""
        return [n for n in self.nodes.values() if isinstance(n, StepNode)]

    @property
    def artifact_nodes(self) -> List[ArtifactNode]:
        """Get all artifact nodes in the graph."""
        return [n for n in self.nodes.values() if isinstance(n, ArtifactNode)]

    @property
    def produces_edges(self) -> List[LineageEdge]:
        """Get all PRODUCES edges (step → artifact)."""
        return [e for e in self.edges if e.edge_type == EdgeType.PRODUCES]

    @property
    def consumes_edges(self) -> List[LineageEdge]:
        """Get all CONSUMES edges (artifact → step)."""
        return [e for e in self.edges if e.edge_type == EdgeType.CONSUMES]


# ============================================================================
# Graph Construction
# ============================================================================


def build_from_run_record(run_record: RunRecord) -> LineageGraph:
    """
    Build a lineage graph from a RunRecord.

    This is the primary graph construction function. It extracts nodes and
    edges from the RunRecord's event sequence.

    Source of Truth (NON-NEGOTIABLE):
        - PRODUCES edges come ONLY from `StepEndEvent.outputs`
        - CONSUMES edges come ONLY from `StepStartEvent.inputs`
        - NO DEPENDENCY INFERENCE IS PERFORMED

    Best-Effort Construction:
        This function is best-effort and does NOT throw exceptions on
        malformed input. Instead, it builds what it can and returns
        the graph. Use `validate_graph()` to check for issues.

    Args:
        run_record: The RunRecord to build the graph from

    Returns:
        LineageGraph with nodes and edges extracted from events

    Algorithm:
        1. Walk through events in order
        2. For StepStartEvent:
           - Collect step start info (for later)
           - Build CONSUMES edges from inputs
        3. For StepEndEvent:
           - Create StepNode from start+end info
           - Create ArtifactNodes from outputs
           - Build PRODUCES edges from outputs
        4. Sort edges by canonical sort key
        5. Return frozen LineageGraph

    Examples:
        >>> from stardive.models.run_record import RunRecord
        >>> from stardive.lineage.graph import build_from_run_record
        >>>
        >>> run_record = RunRecord(...)
        >>> graph = build_from_run_record(run_record)
        >>> print(f"Graph has {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    """
    run_id = run_record.run_id
    nodes: Dict[str, LineageNode] = {}
    edges: List[LineageEdge] = []

    # Track step start events for pairing with end events
    step_starts: Dict[str, tuple[StepStartEvent, int]] = {}  # step_id → (event, index)

    # Track artifacts created from inputs (for CONSUMES edges)
    # These are artifacts referenced in StepStartEvent.inputs but not yet in nodes
    input_artifacts: Dict[str, ArtifactNode] = {}  # artifact_id → ArtifactNode

    for event_index, event in enumerate(run_record.events):
        if isinstance(event, StepStartEvent):
            # Track start event for later pairing
            step_starts[event.step_id] = (event, event_index)

            # Build CONSUMES edges from inputs
            for input_name, artifact_ref in event.inputs.items():
                artifact_node_id = f"artifact:{run_id}:{artifact_ref.artifact_id}"

                # Create artifact node if not already present
                # (input artifacts may not have been produced by a step in this run)
                if artifact_node_id not in nodes:
                    artifact_node = ArtifactNode(
                        run_id=run_id,
                        artifact_id=artifact_ref.artifact_id,
                        artifact_name=input_name,  # Human-readable name from inputs dict key
                        artifact_kind=artifact_ref.artifact_kind,
                        content_hash=artifact_ref.content_hash,
                        producer_step_id=None,  # Unknown/external producer
                    )
                    nodes[artifact_node_id] = artifact_node

                # Create CONSUMES edge (artifact → step)
                step_node_id = f"step:{run_id}:{event.step_id}"
                consumes_edge = LineageEdge(
                    source_id=artifact_node_id,
                    target_id=step_node_id,
                    edge_type=EdgeType.CONSUMES,
                    provenance=EdgeProvenance(
                        source_event_type="StepStartEvent",
                        source_event_index=event_index,
                        source_event_hash=event.event_hash,
                        source_field="inputs",
                    ),
                    metadata={"input_name": input_name},
                )
                edges.append(consumes_edge)

        elif isinstance(event, StepEndEvent):
            # Get paired start event
            start_info = step_starts.get(event.step_id)
            if start_info is not None:
                start_event, start_index = start_info

                # Create StepNode
                step_node = StepNode(
                    run_id=run_id,
                    step_id=event.step_id,
                    step_type=_get_step_type(start_event),
                    status=event.status,
                    started_at=start_event.timestamp,
                    ended_at=event.timestamp,
                )
                nodes[step_node.node_id] = step_node
            else:
                # Orphan end event (no matching start) - create step node with limited info
                step_node = StepNode(
                    run_id=run_id,
                    step_id=event.step_id,
                    step_type="unknown",
                    status=event.status,
                    started_at=event.timestamp,
                    ended_at=event.timestamp,
                )
                nodes[step_node.node_id] = step_node

            # Build PRODUCES edges and artifact nodes from outputs
            for output_name, artifact_ref in event.outputs.items():
                # Create ArtifactNode
                artifact_node = ArtifactNode(
                    run_id=run_id,
                    artifact_id=artifact_ref.artifact_id,
                    artifact_name=output_name,  # Human-readable name from outputs dict key
                    artifact_kind=artifact_ref.artifact_kind,
                    content_hash=artifact_ref.content_hash,
                    producer_step_id=event.step_id,
                )
                artifact_node_id = artifact_node.node_id

                # Update or add to nodes
                # (may already exist as an input to a later step)
                nodes[artifact_node_id] = artifact_node

                # Create PRODUCES edge (step → artifact)
                step_node_id = f"step:{run_id}:{event.step_id}"
                produces_edge = LineageEdge(
                    source_id=step_node_id,
                    target_id=artifact_node_id,
                    edge_type=EdgeType.PRODUCES,
                    provenance=EdgeProvenance(
                        source_event_type="StepEndEvent",
                        source_event_index=event_index,
                        source_event_hash=event.event_hash,
                        source_field="outputs",
                    ),
                    metadata={"output_name": output_name},
                )
                edges.append(produces_edge)

    # Sort edges by canonical sort key for deterministic output
    sorted_edges = sorted(edges, key=lambda e: e.sort_key())

    return LineageGraph(
        run_id=run_id,
        nodes=nodes,
        edges=sorted_edges,
        created_at=datetime.utcnow(),
    )


def _get_step_type(start_event: StepStartEvent) -> str:
    """
    Determine step type from StepStartEvent.

    Heuristic based on identity fields:
    - If model_identity is present → "llm"
    - If tool_identity is present → use tool_name or "tool"
    - Otherwise → "unknown"

    Args:
        start_event: The StepStartEvent to analyze

    Returns:
        Step type string
    """
    if start_event.model_identity is not None:
        return "llm"
    if start_event.tool_identity is not None:
        tool_name = start_event.tool_identity.tool_name
        return tool_name if tool_name else "tool"
    return "unknown"


def build_from_storage(
    storage: Any,  # StorageBackend type from storage module
    run_id: str,
) -> LineageGraph:
    """
    Build a lineage graph from stored RunRecord.

    This is a convenience function that retrieves the RunRecord from
    storage and delegates to `build_from_run_record()`.

    Args:
        storage: StorageBackend instance
        run_id: Run ID to retrieve

    Returns:
        LineageGraph built from the stored RunRecord

    Raises:
        ValueError: If run_id is not found in storage

    Note:
        This function is a thin wrapper. The actual storage retrieval
        is handled by the storage module (Phase 3).
    """
    # Import here to avoid circular imports
    from stardive.storage import StorageBackend

    if not isinstance(storage, StorageBackend):
        raise TypeError(f"Expected StorageBackend, got {type(storage)}")

    run_record = storage.get_run_record(run_id)
    if run_record is None:
        raise ValueError(f"RunRecord not found for run_id: {run_id}")

    return build_from_run_record(run_record)


# ============================================================================
# Serialization Helpers
# ============================================================================


def graph_to_dict(graph: LineageGraph) -> Dict[str, Any]:
    """
    Serialize a LineageGraph to a JSON-compatible dict.

    This produces deterministic output suitable for:
    - JSON serialization
    - Hash computation
    - Test assertions

    Args:
        graph: The LineageGraph to serialize

    Returns:
        Dict with nodes, edges, and metadata
    """
    return {
        "run_id": graph.run_id,
        "nodes": {
            node_id: node.model_dump(mode="json")
            for node_id, node in sorted(graph.nodes.items())
        },
        "edges": [
            edge.model_dump(mode="json")
            for edge in sorted(graph.edges, key=lambda e: e.sort_key())
        ],
        "created_at": graph.created_at.isoformat(),
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
    }


def graph_from_dict(data: Dict[str, Any]) -> LineageGraph:
    """
    Deserialize a LineageGraph from a JSON-compatible dict.

    Args:
        data: Dict with nodes, edges, and metadata

    Returns:
        LineageGraph instance

    Raises:
        ValueError: If data is malformed
    """
    nodes: Dict[str, LineageNode] = {}

    for node_id, node_data in data.get("nodes", {}).items():
        node_type = node_data.get("node_type")
        if node_type == NodeType.STEP.value:
            nodes[node_id] = StepNode.model_validate(node_data)
        elif node_type == NodeType.ARTIFACT.value:
            nodes[node_id] = ArtifactNode.model_validate(node_data)
        else:
            raise ValueError(f"Unknown node type: {node_type}")

    edges = [
        LineageEdge.model_validate(edge_data)
        for edge_data in data.get("edges", [])
    ]

    return LineageGraph(
        run_id=data["run_id"],
        nodes=nodes,
        edges=edges,
        created_at=datetime.fromisoformat(data["created_at"]),
    )


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Edge Types
    "EdgeType",
    "EdgeProvenance",
    "LineageEdge",
    # Graph
    "LineageGraph",
    # Builders
    "build_from_run_record",
    "build_from_storage",
    # Serialization
    "graph_to_dict",
    "graph_from_dict",
]
