"""Graph data structures and algorithms for dependency analysis.

This module provides data structures for representing configuration dependency graphs
and algorithms for topological sorting and cycle detection.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class NodeStatus(str, Enum):
    """Processing status for graph nodes."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class GraphNode:
    """Represents a configuration node in the dependency graph."""

    reference_name: str
    config_type: str  # grid, hub, flow, datasource, etc.
    config_id: int
    branch_id: int  # Source branch (may differ from main branch for external configs)
    application_ref_name: str  # Library module name (empty string if owned)
    is_external: bool
    label: str | None = None

    # Processing state
    status: NodeStatus = NodeStatus.PENDING
    output_file: str | None = None
    error_message: str | None = None

    # Graph metadata
    in_cycle: bool = False  # True if this node is part of a cycle
    depth: int = -1  # Distance from root (-1 = not computed)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for YAML output."""
        return {
            "reference_name": self.reference_name,
            "config_type": self.config_type,
            "config_id": self.config_id,
            "branch_id": self.branch_id,
            "application_ref_name": self.application_ref_name,
            "is_external": self.is_external,
            "label": self.label,
            "status": self.status.value,
            "output_file": self.output_file,
            "error_message": self.error_message,
            "in_cycle": self.in_cycle,
            "depth": self.depth,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphNode":
        """Deserialize from YAML."""
        return cls(
            reference_name=data["reference_name"],
            config_type=data["config_type"],
            config_id=data["config_id"],
            branch_id=data["branch_id"],
            application_ref_name=data.get("application_ref_name", ""),
            is_external=data.get("is_external", False),
            label=data.get("label"),
            status=NodeStatus(data.get("status", "pending")),
            output_file=data.get("output_file"),
            error_message=data.get("error_message"),
            in_cycle=data.get("in_cycle", False),
            depth=data.get("depth", -1),
        )


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between configurations."""

    from_node: str  # reference_name of the config that has the dependency
    to_node: str  # reference_name of the config being depended upon
    edge_type: str  # datasource, flow, dialog, hub, grid, etc.

    def to_dict(self) -> dict[str, str]:
        """Serialize for YAML output."""
        return {
            "from": self.from_node,
            "to": self.to_node,
            "type": self.edge_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "DependencyEdge":
        """Deserialize from YAML."""
        return cls(
            from_node=data["from"],
            to_node=data["to"],
            edge_type=data["type"],
        )


@dataclass
class UnreachableConfig:
    """Represents a configuration that was not reached during DFS traversal."""

    reference_name: str
    config_type: str
    config_id: int
    is_external: bool
    application_ref_name: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize for YAML output."""
        return {
            "reference_name": self.reference_name,
            "config_type": self.config_type,
            "config_id": self.config_id,
            "is_external": self.is_external,
            "application_ref_name": self.application_ref_name,
        }


@dataclass
class DependencyGraph:
    """Complete dependency graph for an application."""

    branch_id: int
    app_name: str
    target: str | None = None  # Starting config (None = shell)
    nodes: dict[str, GraphNode] = field(default_factory=dict)  # ref_name_lower -> node
    edges: list[DependencyEdge] = field(default_factory=list)

    # Library branch mapping: app_ref_name -> branch_id
    library_branches: dict[str, int] = field(default_factory=dict)

    # Branch statuses: branch_id -> applicationStatusId (for cache decisions)
    branch_statuses: dict[int, int] = field(default_factory=dict)

    # Unreachable configs: configs in branch but not discovered by DFS
    unreachable: list[UnreachableConfig] = field(default_factory=list)

    # Full config index for unreachable detection
    _full_index: dict[str, tuple[str, int, str, bool]] = field(default_factory=dict)

    def add_node(self, node: GraphNode) -> None:
        """Add or update a node."""
        key = node.reference_name.lower()
        if key not in self.nodes:
            self.nodes[key] = node

    def get_node(self, ref_name: str) -> GraphNode | None:
        """Get node by reference name (case-insensitive)."""
        return self.nodes.get(ref_name.lower())

    def add_edge(self, from_ref: str, to_ref: str, edge_type: str) -> None:
        """Add a dependency edge."""
        self.edges.append(DependencyEdge(from_ref, to_ref, edge_type))

    def get_adjacency_list(self) -> dict[str, list[str]]:
        """Build adjacency list (A -> [B, C] means A depends on B and C)."""
        adj: dict[str, list[str]] = {key: [] for key in self.nodes}
        for edge in self.edges:
            from_key = edge.from_node.lower()
            to_key = edge.to_node.lower()
            if from_key in adj and to_key in self.nodes:
                if to_key not in adj[from_key]:
                    adj[from_key].append(to_key)
        return adj

    def get_reverse_adjacency(self) -> dict[str, list[str]]:
        """Build reverse adjacency (A -> [B, C] means B and C depend on A)."""
        rev: dict[str, list[str]] = {key: [] for key in self.nodes}
        for edge in self.edges:
            from_key = edge.from_node.lower()
            to_key = edge.to_node.lower()
            if to_key in rev and from_key in self.nodes:
                if from_key not in rev[to_key]:
                    rev[to_key].append(from_key)
        return rev

    def compute_unreachable(self) -> None:
        """Compute unreachable configs by comparing nodes against full index."""
        self.unreachable = []
        visited_keys = set(self.nodes.keys())

        for ref_lower, (config_type, config_id, app_ref, is_external) in self._full_index.items():
            if ref_lower not in visited_keys:
                # Extract actual reference name (we only have lowercase key)
                self.unreachable.append(
                    UnreachableConfig(
                        reference_name=ref_lower,  # Will be lowercase, but that's ok
                        config_type=config_type,
                        config_id=config_id,
                        is_external=is_external,
                        application_ref_name=app_ref,
                    )
                )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire graph for YAML output."""
        return {
            "branch_id": self.branch_id,
            "app_name": self.app_name,
            "target": self.target,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "library_branches": self.library_branches,
            "branch_statuses": self.branch_statuses,
            "summary": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "unreachable_count": len(self.unreachable),
            },
            "nodes": {key: node.to_dict() for key, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "unreachable": {
                "count": len(self.unreachable),
                "configs": [cfg.to_dict() for cfg in self.unreachable],
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DependencyGraph":
        """Deserialize from YAML."""
        graph = cls(
            branch_id=data["branch_id"],
            app_name=data["app_name"],
            target=data.get("target"),
        )
        graph.library_branches = data.get("library_branches", {})
        # Convert branch_statuses keys back to int (YAML may serialize as strings)
        raw_statuses = data.get("branch_statuses", {})
        graph.branch_statuses = {int(k): v for k, v in raw_statuses.items()}

        # Load nodes
        for key, node_data in data.get("nodes", {}).items():
            graph.nodes[key] = GraphNode.from_dict(node_data)

        # Load edges
        for edge_data in data.get("edges", []):
            graph.edges.append(DependencyEdge.from_dict(edge_data))

        # Load unreachable
        unreachable_data = data.get("unreachable", {})
        for cfg_data in unreachable_data.get("configs", []):
            graph.unreachable.append(
                UnreachableConfig(
                    reference_name=cfg_data["reference_name"],
                    config_type=cfg_data["config_type"],
                    config_id=cfg_data["config_id"],
                    is_external=cfg_data.get("is_external", False),
                    application_ref_name=cfg_data.get("application_ref_name", ""),
                )
            )

        return graph


@dataclass
class DocumentProgress:
    """Tracks documentation progress for resumability.

    Supports two phases:
    1. Extraction: Extract raw config data from Datex Studio
    2. Analysis: AI-powered analysis of each config (handled by external process)
    """

    total_configs: int
    current_index: int
    status: str  # "in_progress", "completed", "failed"
    started_at: str
    updated_at: str

    # Phase tracking
    extraction_status: str = "pending"  # "pending", "in_progress", "completed"
    analysis_status: str = "pending"  # "pending", "in_progress", "completed"

    # Ordered list of nodes to process (topological order)
    processing_order: list[str] = field(default_factory=list)  # reference_names (lowercase)

    # Per-config status tracking
    # Each entry can contain:
    #   - status: "pending" | "in_progress" | "completed" | "failed"
    #   - output_file: path to extracted config file
    #   - error: error message (on failure)
    #   - analysis: "pending" | "in_progress" | "completed" | "failed" (for Phase 2)
    #   - analysis_file: path to analysis file (for Phase 2)
    config_status: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for YAML output."""
        completed = sum(1 for s in self.config_status.values() if s.get("status") == "completed")
        failed = sum(1 for s in self.config_status.values() if s.get("status") == "failed")
        pending = self.total_configs - completed - failed

        # Analysis summary
        analysis_completed = sum(
            1 for s in self.config_status.values() if s.get("analysis") == "completed"
        )
        analysis_pending = sum(
            1 for s in self.config_status.values() if s.get("analysis") in (None, "pending")
        )

        return {
            "total_configs": self.total_configs,
            "current_index": self.current_index,
            "status": self.status,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "extraction_status": self.extraction_status,
            "analysis_status": self.analysis_status,
            "summary": {
                "extraction": {
                    "completed": completed,
                    "failed": failed,
                    "pending": pending,
                    "percent_complete": round(completed / self.total_configs * 100, 1)
                    if self.total_configs > 0
                    else 0,
                },
                "analysis": {
                    "completed": analysis_completed,
                    "pending": analysis_pending,
                    "percent_complete": round(analysis_completed / self.total_configs * 100, 1)
                    if self.total_configs > 0
                    else 0,
                },
            },
            "processing_order": self.processing_order,
            "config_status": self.config_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentProgress":
        """Deserialize from YAML."""
        progress = cls(
            total_configs=data["total_configs"],
            current_index=data["current_index"],
            status=data["status"],
            started_at=data["started_at"],
            updated_at=data["updated_at"],
        )
        progress.extraction_status = data.get("extraction_status", "pending")
        progress.analysis_status = data.get("analysis_status", "pending")
        progress.processing_order = data.get("processing_order", [])
        progress.config_status = data.get("config_status", {})
        return progress


def topological_sort(graph: DependencyGraph) -> tuple[list[str], list[str]]:
    """Perform topological sort for bottom-up documentation order.

    Uses Kahn's algorithm in reverse to process leaf nodes first:
    1. Build adjacency list (A depends on B means A -> B)
    2. Compute out-degree for each node (count of dependencies)
    3. Queue all nodes with out-degree 0 (leaf nodes - no dependencies)
    4. While queue not empty:
       - Dequeue node, add to sorted list
       - For each node that depends on this one (reverse adjacency):
         - Decrement their "effective" out-degree
         - If becomes 0, enqueue

    Args:
        graph: The dependency graph to sort

    Returns:
        Tuple of (sorted_order, cycle_nodes):
        - sorted_order: Reference names in bottom-up order (leaves first)
        - cycle_nodes: Reference names of nodes that couldn't be sorted (in cycles)
    """
    adj = graph.get_adjacency_list()  # A -> [B, C] means A depends on B and C
    reverse_adj = graph.get_reverse_adjacency()  # A -> [B, C] means B and C depend on A

    # Compute out-degree (number of dependencies)
    out_degree = {key: len(deps) for key, deps in adj.items()}

    # Start with leaf nodes (no dependencies)
    queue: deque[str] = deque([key for key, deg in out_degree.items() if deg == 0])

    sorted_order: list[str] = []
    processed: set[str] = set()

    while queue:
        node = queue.popleft()
        sorted_order.append(node)
        processed.add(node)

        # For each node that depends on this one
        for dependent in reverse_adj.get(node, []):
            if dependent not in processed:
                out_degree[dependent] -= 1
                if out_degree[dependent] == 0:
                    queue.append(dependent)

    # Identify cycle participants (nodes not processed)
    cycle_nodes = [key for key in graph.nodes if key not in processed]

    # Mark cycle nodes in graph
    for key in cycle_nodes:
        graph.nodes[key].in_cycle = True

    # Add cycle nodes at the end (they need special handling)
    sorted_order.extend(cycle_nodes)

    return sorted_order, cycle_nodes


def compute_depths(graph: DependencyGraph, roots: list[str]) -> None:
    """Compute depth for each node from the root nodes (BFS).

    Args:
        graph: The dependency graph
        roots: List of root node reference names (e.g., shells or target)
    """
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()

    # Initialize with roots at depth 0
    for root in roots:
        key = root.lower()
        if key in graph.nodes:
            queue.append((key, 0))
            visited.add(key)
            graph.nodes[key].depth = 0

    adj = graph.get_adjacency_list()

    while queue:
        node_key, depth = queue.popleft()

        for dep_key in adj.get(node_key, []):
            if dep_key not in visited:
                visited.add(dep_key)
                graph.nodes[dep_key].depth = depth + 1
                queue.append((dep_key, depth + 1))
