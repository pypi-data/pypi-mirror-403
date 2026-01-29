"""Dependency graph data structure and algorithms."""
from collections import deque
from pathlib import Path
from typing import Dict, Set, List, Optional, Tuple, Any

from .models import Node, Edge, EdgeType, NodeType


class DependencyGraph:
    """Unified dependency graph for all file types."""

    def __init__(self, project_root: Path):
        """Initialize the dependency graph.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root.resolve()
        self._nodes: Dict[Path, Node] = {}  # path -> Node
        self._edges: Set[Edge] = set()
        self._forward_index: Dict[Path, Set[Path]] = {}  # node -> children
        self._reverse_index: Dict[Path, Set[Path]] = {}  # node -> parents

    def add_node(self, node: Node) -> None:
        """Add a node to the graph.

        Args:
            node: The node to add
        """
        self._nodes[node.path] = node
        if node.path not in self._forward_index:
            self._forward_index[node.path] = set()
        if node.path not in self._reverse_index:
            self._reverse_index[node.path] = set()

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph.

        Args:
            edge: The edge to add
        """
        # Ensure nodes exist
        if edge.source.path not in self._nodes:
            self.add_node(edge.source)
        if edge.target.path not in self._nodes:
            self.add_node(edge.target)

        self._edges.add(edge)
        self._forward_index[edge.source.path].add(edge.target.path)
        self._reverse_index[edge.target.path].add(edge.source.path)

    def get_node(self, path: Path) -> Optional[Node]:
        """Get a node by path.

        Args:
            path: Absolute path to the file

        Returns:
            The node, or None if not found
        """
        return self._nodes.get(path.resolve())

    def get_nodes(self) -> List[Node]:
        """Get all nodes in the graph.

        Returns:
            List of all nodes
        """
        return list(self._nodes.values())

    def get_edges(self) -> List[Edge]:
        """Get all edges in the graph.

        Returns:
            List of all edges
        """
        return list(self._edges)

    def get_children(self, node: Node, depth: int = 1) -> List[Node]:
        """Get children of a node up to a certain depth.

        Args:
            node: The parent node
            depth: Maximum depth to traverse (1 = immediate children)

        Returns:
            List of child nodes
        """
        if depth <= 0:
            return []

        children = []
        visited = {node.path}
        current_level = [node.path]

        for _ in range(depth):
            next_level = []
            for path in current_level:
                for child_path in self._forward_index.get(path, set()):
                    if child_path not in visited:
                        visited.add(child_path)
                        child_node = self._nodes.get(child_path)
                        if child_node:
                            children.append(child_node)
                            next_level.append(child_path)
            current_level = next_level
            if not current_level:
                break

        return children

    def get_all_children_recursive(self, node: Node) -> List[Node]:
        """Get all recursive children of a node.

        Args:
            node: The parent node

        Returns:
            List of all descendant nodes
        """
        children = []
        visited = {node.path}
        queue = deque([node.path])

        while queue:
            current_path = queue.popleft()
            for child_path in self._forward_index.get(current_path, set()):
                if child_path not in visited:
                    visited.add(child_path)
                    child_node = self._nodes.get(child_path)
                    if child_node:
                        children.append(child_node)
                        queue.append(child_path)

        return children

    def get_parents(self, node: Node, depth: int = 1) -> List[Node]:
        """Get parents of a node up to a certain depth.

        Args:
            node: The child node
            depth: Maximum depth to traverse (1 = immediate parents)

        Returns:
            List of parent nodes
        """
        if depth <= 0:
            return []

        parents = []
        visited = {node.path}
        current_level = [node.path]

        for _ in range(depth):
            next_level = []
            for path in current_level:
                for parent_path in self._reverse_index.get(path, set()):
                    if parent_path not in visited:
                        visited.add(parent_path)
                        parent_node = self._nodes.get(parent_path)
                        if parent_node:
                            parents.append(parent_node)
                            next_level.append(parent_path)
            current_level = next_level
            if not current_level:
                break

        return parents

    def trace_from_entry_point(
        self,
        entry_point: Node
    ) -> Tuple[Set[Node], Dict[Path, List[str]], Dict[Path, EdgeType]]:
        """Trace all dependencies from an entry point using BFS.

        Args:
            entry_point: The entry point node to start from

        Returns:
            Tuple of (connected_nodes, connection_paths, edge_types)
        """
        connected: Set[Node] = set()
        connection_paths: Dict[Path, List[str]] = {}
        edge_types: Dict[Path, EdgeType] = {}

        ep_short = entry_point.relative_path
        queue = deque([(entry_point.path, [ep_short], EdgeType.IMPORT)])
        visited = set()

        while queue:
            current_path, path_so_far, edge_type = queue.popleft()

            if current_path in visited:
                continue
            visited.add(current_path)

            current_node = self._nodes.get(current_path)
            if current_node:
                connected.add(current_node)
                connection_paths[current_path] = path_so_far.copy()
                edge_types[current_path] = edge_type

                # Traverse children
                for child_path in self._forward_index.get(current_path, set()):
                    if child_path not in visited:
                        child_node = self._nodes.get(child_path)
                        if child_node:
                            # Find the edge type
                            child_edge_type = self._get_edge_type(current_path, child_path)
                            new_path = path_so_far + [child_node.relative_path]
                            queue.append((child_path, new_path, child_edge_type))

        return connected, connection_paths, edge_types

    def find_chain_to_entry_point(
        self,
        target: Node,
        entry_point: Node,
        connection_paths: Dict[Path, List[str]]
    ) -> Optional[List[str]]:
        """Find the dependency chain from entry point to target.

        Args:
            target: The target node
            entry_point: The entry point node
            connection_paths: Precomputed connection paths from trace

        Returns:
            List of relative paths forming the chain, or None if not connected
        """
        return connection_paths.get(target.path)

    def get_orphan_nodes(self, entry_points: List[Node]) -> Set[Node]:
        """Find nodes not connected to any entry point.

        Args:
            entry_points: List of entry point nodes

        Returns:
            Set of orphan nodes
        """
        all_connected = set()

        for ep in entry_points:
            connected, _, _ = self.trace_from_entry_point(ep)
            all_connected.update(connected)

        all_nodes = set(self._nodes.values())
        orphans = all_nodes - all_connected

        return orphans

    def suggest_entry_points(
        self,
        top_n: int = 500,
        include_tests: bool = False
    ) -> List[Tuple[Node, int]]:
        """Suggest potential entry points based on dependency tree size.

        Nodes with the most dependencies are likely entry points.

        Args:
            top_n: Maximum number of suggestions
            include_tests: Whether to include test files

        Returns:
            List of (node, dependency_count) tuples, sorted by count
        """
        candidates = []

        test_patterns = ["/tests/", "/test/", "test_", "_test.py", "conftest.py"]

        for node in self._nodes.values():
            # Skip test files if requested
            if not include_tests:
                rel_lower = node.relative_path.lower()
                if any(pat in rel_lower for pat in test_patterns):
                    continue

            # Only consider nodes with dependencies
            direct_children = self._forward_index.get(node.path, set())
            if not direct_children:
                continue

            # Count recursive dependencies
            all_children = self.get_all_children_recursive(node)
            dep_count = len(all_children)

            if dep_count >= 3:  # Minimum threshold
                candidates.append((node, dep_count))

        # Sort by dependency count (descending)
        candidates.sort(key=lambda x: -x[1])
        return candidates[:top_n]

    def get_children_with_token_limit(
        self,
        node: Node,
        max_tokens: int
    ) -> Tuple[List[Node], int]:
        """Get children up to a token limit, prioritizing by depth.

        Args:
            node: The parent node
            max_tokens: Maximum total tokens

        Returns:
            Tuple of (selected_nodes, total_tokens_used)
        """
        # Get children organized by depth
        children_by_depth: Dict[int, List[Node]] = {}
        visited = {node.path}
        queue = deque([(node.path, 0)])

        while queue:
            current_path, depth = queue.popleft()
            for child_path in self._forward_index.get(current_path, set()):
                if child_path not in visited:
                    visited.add(child_path)
                    child_node = self._nodes.get(child_path)
                    if child_node:
                        if depth + 1 not in children_by_depth:
                            children_by_depth[depth + 1] = []
                        children_by_depth[depth + 1].append(child_node)
                        queue.append((child_path, depth + 1))

        # Select nodes by depth until token limit
        selected = []
        total_tokens = 0

        for depth in sorted(children_by_depth.keys()):
            for child in children_by_depth[depth]:
                if total_tokens + child.tokens <= max_tokens:
                    selected.append(child)
                    total_tokens += child.tokens
                elif max_tokens > 0:
                    break
            if total_tokens >= max_tokens and max_tokens > 0:
                break

        return selected, total_tokens

    def _get_edge_type(self, source_path: Path, target_path: Path) -> EdgeType:
        """Get the edge type between two nodes.

        Args:
            source_path: Source node path
            target_path: Target node path

        Returns:
            The edge type, or IMPORT as default
        """
        for edge in self._edges:
            if edge.source.path == source_path and edge.target.path == target_path:
                return edge.edge_type
        return EdgeType.IMPORT

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for serialization.

        Returns:
            Dictionary representation of the graph
        """
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges],
            "stats": {
                "total_nodes": len(self._nodes),
                "total_edges": len(self._edges),
                "node_types": self._count_node_types(),
            }
        }

    def _count_node_types(self) -> Dict[str, int]:
        """Count nodes by type.

        Returns:
            Dictionary of node_type -> count
        """
        counts: Dict[str, int] = {}
        for node in self._nodes.values():
            type_name = node.node_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
