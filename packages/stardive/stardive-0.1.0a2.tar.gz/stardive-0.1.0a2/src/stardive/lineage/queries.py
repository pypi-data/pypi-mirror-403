"""
Lineage Graph Query API for Stardive Execution Kernel.

This module provides query functions for traversing lineage graphs:
- **LineageTrace**: A subgraph representing the lineage of a target node
- **get_artifact_lineage()**: Trace artifact back to its origins
- **get_step_inputs()**: Get all input artifacts for a step
- **get_step_outputs()**: Get all output artifacts from a step
- **get_artifact_producer()**: Get the step that produced an artifact
- **get_artifact_consumers()**: Get all steps that consume an artifact
- **get_downstream_artifacts()**: Get all transitively derived artifacts
- **get_upstream_artifacts()**: Get all transitively required artifacts

Key Principles:
1. **LineageTrace is a DAG**: Traces are subgraphs, not linear paths
2. **Deterministic Output**: All functions return sorted Lists for JSON determinism
3. **Uses List, Not Set**: Set is not JSON-friendly; use sorted List with internal dedup

Canonical Node ID Format:
    - Step node: `step:<run_id>:<step_id>`
    - Artifact node: `artifact:<run_id>:<artifact_id>`

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4.1) - Lineage query API
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

from stardive.lineage.graph import EdgeType, LineageEdge, LineageGraph
from stardive.lineage.nodes import ArtifactNode, StepNode


# ============================================================================
# Lineage Trace
# ============================================================================


class LineageTrace(BaseModel):
    """
    A subgraph representing the lineage of a target node.

    LineageTrace captures the DAG of all nodes and edges that contribute
    to a target node (artifact or step). This is NOT a linear path —
    it correctly represents branching dependencies (diamond patterns).

    Deterministic Output:
        All lists are sorted for JSON determinism and stable test assertions:
        - `nodes`: Sorted by node_id
        - `edges`: Sorted by edge sort key (type, source, target, event_index)
        - `topological_order`: From origins to target (for display)

    Why List, Not Set:
        `Set[...]` is not JSON-friendly and non-deterministically ordered.
        We use sorted `List[...]` for audit-grade reproducibility.

    Example Use Cases:
        1. "What contributed to this artifact?" → get_artifact_lineage()
        2. "What does this step depend on?" → trace from step node
        3. "Show me the full provenance chain" → display topological_order

    Examples:
        Simple linear trace:
            >>> trace = get_artifact_lineage(graph, "result")
            >>> trace.target_id
            'artifact:run_abc:result'
            >>> trace.nodes  # All contributing nodes
            ['artifact:run_abc:input', 'artifact:run_abc:result', 'step:run_abc:analyze']
            >>> trace.topological_order  # From origins to target
            ['artifact:run_abc:input', 'step:run_abc:analyze', 'artifact:run_abc:result']

        Diamond pattern (A→B, A→C, B+C→D):
            >>> trace = get_artifact_lineage(graph, "D")
            >>> len(trace.nodes)  # A, B, C, D and their steps
            6
    """

    model_config = ConfigDict(frozen=True)

    target_id: str = Field(
        ...,
        description="Canonical node ID of the target node",
    )
    nodes: List[str] = Field(
        default_factory=list,
        description="Sorted list of node_ids in the trace (deterministic)",
    )
    edges: List[LineageEdge] = Field(
        default_factory=list,
        description="Sorted list of edges in the trace (deterministic)",
    )
    topological_order: List[str] = Field(
        default_factory=list,
        description="Nodes ordered from origins to target (for display)",
    )


# ============================================================================
# Basic Query Functions
# ============================================================================


def get_artifact_producer(
    graph: LineageGraph, artifact_id: str
) -> Optional[StepNode]:
    """
    Get the step that produced an artifact.

    Finds the PRODUCES edge that targets this artifact and returns
    the source step node.

    Args:
        graph: The lineage graph to query
        artifact_id: The artifact identifier (not full canonical node_id)

    Returns:
        The StepNode that produced the artifact, or None if orphan

    Examples:
        >>> producer = get_artifact_producer(graph, "result")
        >>> if producer:
        ...     print(f"Produced by step: {producer.step_id}")
        >>> else:
        ...     print("No producer (external input)")
    """
    artifact_node_id = f"artifact:{graph.run_id}:{artifact_id}"

    for edge in graph.produces_edges:
        if edge.target_id == artifact_node_id:
            step_node = graph.nodes.get(edge.source_id)
            if isinstance(step_node, StepNode):
                return step_node

    return None


def get_artifact_consumers(
    graph: LineageGraph, artifact_id: str
) -> List[StepNode]:
    """
    Get all steps that consume an artifact.

    Finds all CONSUMES edges that source from this artifact and returns
    the target step nodes.

    Args:
        graph: The lineage graph to query
        artifact_id: The artifact identifier (not full canonical node_id)

    Returns:
        Sorted list of StepNodes that consume the artifact

    Examples:
        >>> consumers = get_artifact_consumers(graph, "input_data")
        >>> for step in consumers:
        ...     print(f"Consumed by: {step.step_id}")
    """
    artifact_node_id = f"artifact:{graph.run_id}:{artifact_id}"
    consumers: List[StepNode] = []

    for edge in graph.consumes_edges:
        if edge.source_id == artifact_node_id:
            step_node = graph.nodes.get(edge.target_id)
            if isinstance(step_node, StepNode):
                consumers.append(step_node)

    # Sort by node_id for deterministic output
    return sorted(consumers, key=lambda n: n.node_id)


def get_step_inputs(
    graph: LineageGraph, step_id: str
) -> List[ArtifactNode]:
    """
    Get all input artifacts for a step.

    Finds all CONSUMES edges that target this step and returns
    the source artifact nodes.

    Args:
        graph: The lineage graph to query
        step_id: The step identifier (not full canonical node_id)

    Returns:
        Sorted list of ArtifactNodes that are inputs to the step

    Examples:
        >>> inputs = get_step_inputs(graph, "analyze")
        >>> for artifact in inputs:
        ...     print(f"Input: {artifact.artifact_id}")
    """
    step_node_id = f"step:{graph.run_id}:{step_id}"
    inputs: List[ArtifactNode] = []

    for edge in graph.consumes_edges:
        if edge.target_id == step_node_id:
            artifact_node = graph.nodes.get(edge.source_id)
            if isinstance(artifact_node, ArtifactNode):
                inputs.append(artifact_node)

    # Sort by node_id for deterministic output
    return sorted(inputs, key=lambda n: n.node_id)


def get_step_outputs(
    graph: LineageGraph, step_id: str
) -> List[ArtifactNode]:
    """
    Get all output artifacts from a step.

    Finds all PRODUCES edges that source from this step and returns
    the target artifact nodes.

    Args:
        graph: The lineage graph to query
        step_id: The step identifier (not full canonical node_id)

    Returns:
        Sorted list of ArtifactNodes that are outputs from the step

    Examples:
        >>> outputs = get_step_outputs(graph, "analyze")
        >>> for artifact in outputs:
        ...     print(f"Output: {artifact.artifact_id}")
    """
    step_node_id = f"step:{graph.run_id}:{step_id}"
    outputs: List[ArtifactNode] = []

    for edge in graph.produces_edges:
        if edge.source_id == step_node_id:
            artifact_node = graph.nodes.get(edge.target_id)
            if isinstance(artifact_node, ArtifactNode):
                outputs.append(artifact_node)

    # Sort by node_id for deterministic output
    return sorted(outputs, key=lambda n: n.node_id)


# ============================================================================
# Transitive Query Functions
# ============================================================================


def get_upstream_artifacts(
    graph: LineageGraph, artifact_id: str
) -> List[ArtifactNode]:
    """
    Get all artifacts that this artifact transitively depends on.

    Traverses the graph backwards (PRODUCES → step → CONSUMES) to find
    all artifacts that contributed to producing this artifact.

    Algorithm:
        BFS/DFS from artifact → find producer step → find step inputs →
        recurse until reaching roots (orphan artifacts or external inputs)

    Args:
        graph: The lineage graph to query
        artifact_id: The artifact identifier (not full canonical node_id)

    Returns:
        Sorted list of ArtifactNodes that are upstream (dependencies)

    Note:
        The result does NOT include the target artifact itself.
        Uses internal Set for dedup, returns sorted List for determinism.

    Examples:
        >>> # If result depends on intermediate, which depends on input:
        >>> upstream = get_upstream_artifacts(graph, "result")
        >>> [a.artifact_id for a in upstream]
        ['input', 'intermediate']
    """
    artifact_node_id = f"artifact:{graph.run_id}:{artifact_id}"

    if artifact_node_id not in graph.nodes:
        return []

    # BFS traversal backwards through the graph
    visited: Set[str] = set()
    upstream_artifacts: Set[str] = set()
    queue: deque[str] = deque()

    # Start with the producer step of our target artifact
    for edge in graph.produces_edges:
        if edge.target_id == artifact_node_id:
            queue.append(edge.source_id)  # Producer step

    while queue:
        current_id = queue.popleft()

        if current_id in visited:
            continue
        visited.add(current_id)

        current_node = graph.nodes.get(current_id)

        if isinstance(current_node, StepNode):
            # Find all inputs to this step
            for edge in graph.consumes_edges:
                if edge.target_id == current_id:
                    input_artifact_id = edge.source_id
                    if input_artifact_id != artifact_node_id:  # Don't include target
                        upstream_artifacts.add(input_artifact_id)
                        # Find producer of this input
                        for prod_edge in graph.produces_edges:
                            if prod_edge.target_id == input_artifact_id:
                                queue.append(prod_edge.source_id)

    # Convert to sorted list of ArtifactNodes
    result: List[ArtifactNode] = []
    for node_id in sorted(upstream_artifacts):
        node = graph.nodes.get(node_id)
        if isinstance(node, ArtifactNode):
            result.append(node)

    return result


def get_downstream_artifacts(
    graph: LineageGraph, artifact_id: str
) -> List[ArtifactNode]:
    """
    Get all artifacts that are transitively derived from this artifact.

    Traverses the graph forwards (CONSUMES → step → PRODUCES) to find
    all artifacts that were produced using this artifact.

    Algorithm:
        BFS/DFS from artifact → find consumer steps → find step outputs →
        recurse until reaching leaves (artifacts with no consumers)

    Args:
        graph: The lineage graph to query
        artifact_id: The artifact identifier (not full canonical node_id)

    Returns:
        Sorted list of ArtifactNodes that are downstream (derived)

    Note:
        The result does NOT include the source artifact itself.
        Uses internal Set for dedup, returns sorted List for determinism.

    Examples:
        >>> # If input is used to produce intermediate, then result:
        >>> downstream = get_downstream_artifacts(graph, "input")
        >>> [a.artifact_id for a in downstream]
        ['intermediate', 'result']
    """
    artifact_node_id = f"artifact:{graph.run_id}:{artifact_id}"

    if artifact_node_id not in graph.nodes:
        return []

    # BFS traversal forwards through the graph
    visited: Set[str] = set()
    downstream_artifacts: Set[str] = set()
    queue: deque[str] = deque()

    # Start with all consumer steps of our source artifact
    for edge in graph.consumes_edges:
        if edge.source_id == artifact_node_id:
            queue.append(edge.target_id)  # Consumer step

    while queue:
        current_id = queue.popleft()

        if current_id in visited:
            continue
        visited.add(current_id)

        current_node = graph.nodes.get(current_id)

        if isinstance(current_node, StepNode):
            # Find all outputs from this step
            for edge in graph.produces_edges:
                if edge.source_id == current_id:
                    output_artifact_id = edge.target_id
                    if output_artifact_id != artifact_node_id:  # Don't include source
                        downstream_artifacts.add(output_artifact_id)
                        # Find consumers of this output
                        for cons_edge in graph.consumes_edges:
                            if cons_edge.source_id == output_artifact_id:
                                queue.append(cons_edge.target_id)

    # Convert to sorted list of ArtifactNodes
    result: List[ArtifactNode] = []
    for node_id in sorted(downstream_artifacts):
        node = graph.nodes.get(node_id)
        if isinstance(node, ArtifactNode):
            result.append(node)

    return result


# ============================================================================
# Lineage Trace Function
# ============================================================================


def get_artifact_lineage(
    graph: LineageGraph, artifact_id: str
) -> LineageTrace:
    """
    Trace an artifact back to its origins.

    Returns a LineageTrace containing all nodes and edges that contributed
    to producing this artifact. This is a DAG, not a linear path.

    The trace includes:
        - The target artifact
        - All producer steps (transitively)
        - All input artifacts (transitively)
        - All edges connecting these nodes

    Topological Order:
        The `topological_order` field provides nodes ordered from origins
        (external inputs, orphan artifacts) to the target artifact. This
        is useful for display and understanding causality.

    Args:
        graph: The lineage graph to query
        artifact_id: The artifact identifier (not full canonical node_id)

    Returns:
        LineageTrace with nodes, edges, and topological order

    Examples:
        Simple linear workflow (input → step → result):
            >>> trace = get_artifact_lineage(graph, "result")
            >>> trace.target_id
            'artifact:run_abc:result'
            >>> trace.topological_order
            ['artifact:run_abc:input', 'step:run_abc:analyze', 'artifact:run_abc:result']

        Diamond pattern (input → step_a → mid_a, input → step_b → mid_b, mid_a+mid_b → final):
            >>> trace = get_artifact_lineage(graph, "final")
            >>> len(trace.nodes)  # input + 4 steps + 4 artifacts
            7
    """
    artifact_node_id = f"artifact:{graph.run_id}:{artifact_id}"

    if artifact_node_id not in graph.nodes:
        return LineageTrace(
            target_id=artifact_node_id,
            nodes=[],
            edges=[],
            topological_order=[],
        )

    # Collect all nodes and edges in the trace using BFS backwards
    trace_nodes: Set[str] = {artifact_node_id}
    trace_edges: List[LineageEdge] = []
    queue: deque[str] = deque([artifact_node_id])

    while queue:
        current_id = queue.popleft()
        current_node = graph.nodes.get(current_id)

        if isinstance(current_node, ArtifactNode):
            # Find producer step
            for edge in graph.produces_edges:
                if edge.target_id == current_id:
                    if edge not in trace_edges:
                        trace_edges.append(edge)
                    if edge.source_id not in trace_nodes:
                        trace_nodes.add(edge.source_id)
                        queue.append(edge.source_id)

        elif isinstance(current_node, StepNode):
            # Find input artifacts
            for edge in graph.consumes_edges:
                if edge.target_id == current_id:
                    if edge not in trace_edges:
                        trace_edges.append(edge)
                    if edge.source_id not in trace_nodes:
                        trace_nodes.add(edge.source_id)
                        queue.append(edge.source_id)

    # Compute topological order for the trace subgraph
    topological_order = _compute_topological_order(graph, trace_nodes, trace_edges)

    # Sort nodes and edges for determinism
    sorted_nodes = sorted(trace_nodes)
    sorted_edges = sorted(trace_edges, key=lambda e: e.sort_key())

    return LineageTrace(
        target_id=artifact_node_id,
        nodes=sorted_nodes,
        edges=sorted_edges,
        topological_order=topological_order,
    )


def _compute_topological_order(
    graph: LineageGraph,
    trace_nodes: Set[str],
    trace_edges: List[LineageEdge],
) -> List[str]:
    """
    Compute topological order for a trace subgraph.

    Orders nodes from origins (no incoming edges) to the target.
    Uses Kahn's algorithm.

    Args:
        graph: The full lineage graph
        trace_nodes: Set of node IDs in the trace
        trace_edges: List of edges in the trace

    Returns:
        List of node IDs in topological order
    """
    if not trace_nodes:
        return []

    # Build adjacency list and in-degree for trace subgraph
    adj: Dict[str, List[str]] = defaultdict(list)
    in_degree: Dict[str, int] = {node_id: 0 for node_id in trace_nodes}

    for edge in trace_edges:
        if edge.source_id in trace_nodes and edge.target_id in trace_nodes:
            adj[edge.source_id].append(edge.target_id)
            in_degree[edge.target_id] += 1

    # Kahn's algorithm
    # Use sorted for deterministic starting order
    queue = sorted([node_id for node_id, degree in in_degree.items() if degree == 0])
    result: List[str] = []

    while queue:
        # Sort queue for deterministic processing order
        queue = sorted(queue)
        node_id = queue.pop(0)
        result.append(node_id)

        for neighbor in sorted(adj[node_id]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Lineage Trace
    "LineageTrace",
    # Basic Queries
    "get_artifact_producer",
    "get_artifact_consumers",
    "get_step_inputs",
    "get_step_outputs",
    # Transitive Queries
    "get_upstream_artifacts",
    "get_downstream_artifacts",
    # Full Lineage Trace
    "get_artifact_lineage",
]
