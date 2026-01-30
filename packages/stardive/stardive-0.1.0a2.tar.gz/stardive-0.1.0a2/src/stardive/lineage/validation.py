"""
Lineage Graph Validation for Stardive Execution Kernel.

This module provides validation for lineage graphs:
- **ValidationIssueType**: Enum for different types of validation issues
- **LineageValidationIssue**: A single validation issue with context
- **LineageValidationReport**: Complete validation report for a graph
- **validate_graph()**: Main validation function

Key Principles:
1. **Never Throws**: `validate_graph()` NEVER raises exceptions; always returns report
2. **Best-Effort**: Reports all issues found, doesn't stop at first issue
3. **Severity Levels**: Issues are classified as "error" or "warning"
4. **Caller Controls Strictness**: Strictness is controlled by caller (CLI `--strict` flag)

Issue Types:
    - ORPHAN_ARTIFACT: Artifact with no producer (producer_step_id is None)
    - MISSING_INPUT: CONSUMES edge references artifact not in graph
    - DUPLICATE_PRODUCER: Multiple PRODUCES edges target same artifact_id
    - DANGLING_EDGE: Edge references non-existent node
    - CYCLE_DETECTED: Graph has cycle (should be DAG)

Duplicate Producer Semantics:
    Two PRODUCES edges targeting the same `artifact:<run_id>:<artifact_id>` is a
    duplicate. Identity is based on `artifact_id` within run, NOT on `content_hash`.

For detailed specifications, see:
- CURRENT_JOB.md (Phase 4.1) - Lineage graph validation
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field

from stardive.lineage.graph import EdgeType, LineageGraph


# ============================================================================
# Validation Issue Type Enum
# ============================================================================


class ValidationIssueType(str, Enum):
    """
    Type of validation issue found in a lineage graph.

    Each issue type has an associated severity (error or warning):
    - **Errors**: Represent data integrity issues
    - **Warnings**: Represent potential issues or anomalies

    Issue Types:
        ORPHAN_ARTIFACT: Artifact with no producer step (warning)
            - May be intentional (external input) or a bug
            - `producer_step_id` is None

        MISSING_INPUT: CONSUMES edge references missing artifact (error)
            - A step declares dependency on artifact not in graph
            - Indicates incomplete event capture or malformed data

        DUPLICATE_PRODUCER: Multiple PRODUCES edges target same artifact_id (error)
            - Two steps claim to produce the same artifact
            - Identity based on `artifact_id`, not `content_hash`

        DANGLING_EDGE: Edge references non-existent node (error)
            - Edge source_id or target_id not in graph.nodes
            - Indicates graph construction bug

        CYCLE_DETECTED: Graph contains a cycle (error)
            - Lineage graphs should be DAGs (directed acyclic graphs)
            - Cycle indicates temporal impossibility

    Examples:
        >>> issue_type = ValidationIssueType.ORPHAN_ARTIFACT
        >>> print(issue_type.value)
        'orphan_artifact'
    """

    ORPHAN_ARTIFACT = "orphan_artifact"
    MISSING_INPUT = "missing_input"
    DUPLICATE_PRODUCER = "duplicate_producer"
    DANGLING_EDGE = "dangling_edge"
    CYCLE_DETECTED = "cycle_detected"


# ============================================================================
# Severity Mapping
# ============================================================================


_ISSUE_SEVERITIES: Dict[ValidationIssueType, str] = {
    ValidationIssueType.ORPHAN_ARTIFACT: "warning",
    ValidationIssueType.MISSING_INPUT: "error",
    ValidationIssueType.DUPLICATE_PRODUCER: "error",
    ValidationIssueType.DANGLING_EDGE: "error",
    ValidationIssueType.CYCLE_DETECTED: "error",
}


def get_issue_severity(issue_type: ValidationIssueType) -> str:
    """Get severity level for an issue type."""
    return _ISSUE_SEVERITIES.get(issue_type, "error")


# ============================================================================
# Lineage Validation Issue
# ============================================================================


class LineageValidationIssue(BaseModel):
    """
    A single validation issue found in a lineage graph.

    Provides context about where and what the issue is:
    - `issue_type`: What kind of issue
    - `severity`: "error" or "warning"
    - `message`: Human-readable description
    - `node_id`: Related node (if applicable)
    - `edge_index`: Related edge position (if applicable)

    Immutability:
        Issues are frozen once created. This ensures they can be
        safely stored and compared.

    Examples:
        Orphan artifact:
            LineageValidationIssue(
                issue_type=ValidationIssueType.ORPHAN_ARTIFACT,
                node_id="artifact:run_abc:input_data",
                message="Artifact has no producer step",
                severity="warning"
            )

        Duplicate producer:
            LineageValidationIssue(
                issue_type=ValidationIssueType.DUPLICATE_PRODUCER,
                node_id="artifact:run_abc:result",
                message="Artifact produced by multiple steps: step_a, step_b",
                severity="error"
            )
    """

    model_config = ConfigDict(frozen=True)

    issue_type: ValidationIssueType = Field(
        ...,
        description="Type of validation issue",
    )
    node_id: Optional[str] = Field(
        None,
        description="Canonical node ID related to this issue (if applicable)",
    )
    edge_index: Optional[int] = Field(
        None,
        description="Index of edge in graph.edges related to this issue (if applicable)",
    )
    message: str = Field(
        ...,
        description="Human-readable description of the issue",
    )
    severity: str = Field(
        ...,
        description="Issue severity: 'error' or 'warning'",
        pattern=r"^(error|warning)$",
    )


# ============================================================================
# Lineage Validation Report
# ============================================================================


class LineageValidationReport(BaseModel):
    """
    Complete validation report for a lineage graph.

    Aggregates all validation issues found during graph validation.

    Properties:
        is_valid: True if no errors (warnings allowed)
        has_errors: True if any error-level issues exist
        has_warnings: True if any warning-level issues exist
        error_count: Number of error-level issues
        warning_count: Number of warning-level issues

    Usage:
        The caller controls how strictly to interpret the report:
        - Default: Print report, continue if only warnings
        - Strict mode (`--strict` flag): Fail on any issue including warnings
        - Audit mode: Fail on any error

    Examples:
        Valid graph (no issues):
            >>> report = validate_graph(graph)
            >>> report.is_valid
            True
            >>> report.issues
            []

        Graph with warnings only:
            >>> report = validate_graph(graph)
            >>> report.is_valid  # True, warnings don't fail validation
            True
            >>> report.has_warnings
            True

        Graph with errors:
            >>> report = validate_graph(graph)
            >>> report.is_valid  # False, errors fail validation
            False
            >>> report.has_errors
            True
    """

    model_config = ConfigDict(frozen=True)

    run_id: str = Field(
        ...,
        description="Run ID of the validated graph",
    )
    is_valid: bool = Field(
        ...,
        description="True if no error-level issues (warnings allowed)",
    )
    issues: List[LineageValidationIssue] = Field(
        default_factory=list,
        description="All validation issues found",
    )
    node_count: int = Field(
        ...,
        description="Number of nodes in the graph",
        ge=0,
    )
    edge_count: int = Field(
        ...,
        description="Number of edges in the graph",
        ge=0,
    )
    validated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When validation was performed",
    )

    @property
    def has_errors(self) -> bool:
        """True if any error-level issues exist."""
        return any(issue.severity == "error" for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """True if any warning-level issues exist."""
        return any(issue.severity == "warning" for issue in self.issues)

    @property
    def error_count(self) -> int:
        """Number of error-level issues."""
        return sum(1 for issue in self.issues if issue.severity == "error")

    @property
    def warning_count(self) -> int:
        """Number of warning-level issues."""
        return sum(1 for issue in self.issues if issue.severity == "warning")

    def get_issues_by_type(
        self, issue_type: ValidationIssueType
    ) -> List[LineageValidationIssue]:
        """Get all issues of a specific type."""
        return [i for i in self.issues if i.issue_type == issue_type]

    def get_issues_by_severity(self, severity: str) -> List[LineageValidationIssue]:
        """Get all issues of a specific severity."""
        return [i for i in self.issues if i.severity == severity]


# ============================================================================
# Validation Functions
# ============================================================================


def validate_graph(graph: LineageGraph) -> LineageValidationReport:
    """
    Validate a lineage graph and return a comprehensive report.

    This function NEVER throws exceptions. It always returns a
    LineageValidationReport, even for malformed graphs.

    Validation Checks:
        1. Orphan artifacts (no producer step)
        2. Missing input artifacts (CONSUMES edge to missing artifact)
        3. Duplicate producers (multiple steps produce same artifact)
        4. Dangling edges (edge references non-existent node)
        5. Cycle detection (graph should be DAG)

    Strictness:
        This function does NOT determine what to do about issues.
        It reports them. The caller decides:
        - CLI can use `--strict` to fail on any issue
        - Default can warn on warnings, fail on errors
        - Tests can assert specific issues are present/absent

    Args:
        graph: The LineageGraph to validate

    Returns:
        LineageValidationReport with all issues found

    Examples:
        >>> from stardive.lineage import build_from_run_record
        >>> from stardive.lineage.validation import validate_graph
        >>>
        >>> graph = build_from_run_record(run_record)
        >>> report = validate_graph(graph)
        >>>
        >>> if report.is_valid:
        ...     print("Graph is valid")
        >>> else:
        ...     for issue in report.issues:
        ...         print(f"{issue.severity}: {issue.message}")
    """
    issues: List[LineageValidationIssue] = []

    # Check 1: Orphan artifacts
    issues.extend(_check_orphan_artifacts(graph))

    # Check 2: Dangling edges (before checking missing inputs)
    issues.extend(_check_dangling_edges(graph))

    # Check 3: Missing input artifacts
    issues.extend(_check_missing_inputs(graph))

    # Check 4: Duplicate producers
    issues.extend(_check_duplicate_producers(graph))

    # Check 5: Cycle detection
    issues.extend(_check_cycles(graph))

    # Determine validity (no errors = valid)
    is_valid = not any(issue.severity == "error" for issue in issues)

    return LineageValidationReport(
        run_id=graph.run_id,
        is_valid=is_valid,
        issues=issues,
        node_count=len(graph.nodes),
        edge_count=len(graph.edges),
        validated_at=datetime.utcnow(),
    )


def _check_orphan_artifacts(graph: LineageGraph) -> List[LineageValidationIssue]:
    """
    Check for artifacts with no producer step.

    An orphan artifact has `producer_step_id = None`. This may be intentional
    (external input) or indicate missing event capture.

    Severity: WARNING (orphans are often valid external inputs)
    """
    issues = []

    for node in graph.artifact_nodes:
        if node.producer_step_id is None:
            issues.append(
                LineageValidationIssue(
                    issue_type=ValidationIssueType.ORPHAN_ARTIFACT,
                    node_id=node.node_id,
                    message=f"Artifact '{node.artifact_id}' has no producer step (may be external input)",
                    severity="warning",
                )
            )

    return issues


def _check_dangling_edges(graph: LineageGraph) -> List[LineageValidationIssue]:
    """
    Check for edges that reference non-existent nodes.

    A dangling edge has a source_id or target_id that doesn't exist in graph.nodes.

    Severity: ERROR (indicates graph construction bug)
    """
    issues = []
    node_ids = set(graph.nodes.keys())

    for edge_index, edge in enumerate(graph.edges):
        if edge.source_id not in node_ids:
            issues.append(
                LineageValidationIssue(
                    issue_type=ValidationIssueType.DANGLING_EDGE,
                    edge_index=edge_index,
                    message=f"Edge source '{edge.source_id}' not found in graph nodes",
                    severity="error",
                )
            )
        if edge.target_id not in node_ids:
            issues.append(
                LineageValidationIssue(
                    issue_type=ValidationIssueType.DANGLING_EDGE,
                    edge_index=edge_index,
                    message=f"Edge target '{edge.target_id}' not found in graph nodes",
                    severity="error",
                )
            )

    return issues


def _check_missing_inputs(graph: LineageGraph) -> List[LineageValidationIssue]:
    """
    Check for CONSUMES edges referencing missing artifacts.

    If a step declares an input artifact that is not present in the graph,
    report a MISSING_INPUT issue. Dangling edges are also reported separately.

    Severity: ERROR (indicates missing event capture)
    """
    issues = []

    # Check CONSUMES edges for missing artifact nodes
    for edge in graph.consumes_edges:
        artifact_node_id = edge.source_id
        # If artifact node is missing, report issue
        if artifact_node_id not in graph.nodes:
            parts = artifact_node_id.split(":", 2)
            artifact_id = parts[2] if len(parts) == 3 else artifact_node_id
            issues.append(
                LineageValidationIssue(
                    issue_type=ValidationIssueType.MISSING_INPUT,
                    node_id=artifact_node_id,
                    message=f"Input artifact '{artifact_id}' not found in graph nodes",
                    severity="error",
                )
            )

    return issues


def _check_duplicate_producers(graph: LineageGraph) -> List[LineageValidationIssue]:
    """
    Check for artifacts with multiple producer steps.

    If two PRODUCES edges target the same artifact_id, this is an error.
    Identity is based on artifact_id within run, NOT content_hash.

    Severity: ERROR (same artifact cannot be produced twice)
    """
    issues = []

    # Map artifact_node_id to list of producer step IDs
    producers: Dict[str, List[str]] = defaultdict(list)

    for edge in graph.produces_edges:
        artifact_node_id = edge.target_id
        step_node_id = edge.source_id
        # Extract step_id from canonical node_id
        # Format: step:<run_id>:<step_id>
        parts = step_node_id.split(":", 2)
        step_id = parts[2] if len(parts) == 3 else step_node_id
        producers[artifact_node_id].append(step_id)

    for artifact_node_id, step_ids in producers.items():
        if len(step_ids) > 1:
            # Extract artifact_id from canonical node_id
            # Format: artifact:<run_id>:<artifact_id>
            parts = artifact_node_id.split(":", 2)
            artifact_id = parts[2] if len(parts) == 3 else artifact_node_id

            issues.append(
                LineageValidationIssue(
                    issue_type=ValidationIssueType.DUPLICATE_PRODUCER,
                    node_id=artifact_node_id,
                    message=f"Artifact '{artifact_id}' produced by multiple steps: {', '.join(step_ids)}",
                    severity="error",
                )
            )

    return issues


def _check_cycles(graph: LineageGraph) -> List[LineageValidationIssue]:
    """
    Check for cycles in the lineage graph.

    Lineage graphs should be DAGs (directed acyclic graphs). A cycle indicates
    a temporal impossibility (A depends on B which depends on A).

    Uses Kahn's algorithm for cycle detection.

    Severity: ERROR (cycles are impossible in valid lineage)
    """
    issues = []

    if len(graph.nodes) == 0:
        return issues

    # Build adjacency list and in-degree count
    adj: Dict[str, List[str]] = defaultdict(list)
    in_degree: Dict[str, int] = {node_id: 0 for node_id in graph.nodes}

    for edge in graph.edges:
        adj[edge.source_id].append(edge.target_id)
        if edge.target_id in in_degree:
            in_degree[edge.target_id] += 1

    # Kahn's algorithm
    queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
    visited_count = 0

    while queue:
        node_id = queue.pop(0)
        visited_count += 1

        for neighbor in adj[node_id]:
            if neighbor in in_degree:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

    # If we didn't visit all nodes, there's a cycle
    if visited_count < len(graph.nodes):
        # Find nodes in the cycle (those still with in_degree > 0)
        cycle_nodes = [
            node_id for node_id, degree in in_degree.items() if degree > 0
        ]

        issues.append(
            LineageValidationIssue(
                issue_type=ValidationIssueType.CYCLE_DETECTED,
                message=f"Graph contains cycle involving {len(cycle_nodes)} nodes",
                severity="error",
            )
        )

    return issues


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "ValidationIssueType",
    "LineageValidationIssue",
    "LineageValidationReport",
    "validate_graph",
    "get_issue_severity",
]
