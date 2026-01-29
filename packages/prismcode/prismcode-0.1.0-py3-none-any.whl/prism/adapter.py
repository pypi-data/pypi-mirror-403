"""Adapter layer to integrate Prism with the existing Flask API.

This module provides a bridge between the old zdeps2 API interface and the new
Prism backend, maintaining backward compatibility while using the clean architecture.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import threading

from .session import PrismSession
from .models import EntryPoint, SnapshotConfig


class PrismSessionManager:
    """Manages Prism sessions with thread-safe current project switching.

    This provides a singleton-like interface for the Flask API while using
    the clean Prism architecture under the hood.
    """

    def __init__(self):
        self._sessions: Dict[str, PrismSession] = {}
        self._current_project: Optional[str] = None
        self._lock = threading.Lock()

    def set_current_project(self, project_root: str) -> None:
        """Set the current project and create/retrieve its session.

        Args:
            project_root: Absolute path to project root
        """
        with self._lock:
            project_root = str(Path(project_root).resolve())
            self._current_project = project_root

            # Create session if it doesn't exist
            if project_root not in self._sessions:
                self._sessions[project_root] = PrismSession(project_root)

    def get_current_session(self) -> PrismSession:
        """Get the current project's session.

        Returns:
            PrismSession for current project

        Raises:
            RuntimeError: If no current project is set
        """
        with self._lock:
            if not self._current_project:
                raise RuntimeError("No current project set")

            if self._current_project not in self._sessions:
                self._sessions[self._current_project] = PrismSession(self._current_project)

            return self._sessions[self._current_project]

    def invalidate_current(self) -> None:
        """Invalidate (clear) the current project's session to force re-scan."""
        with self._lock:
            if self._current_project and self._current_project in self._sessions:
                del self._sessions[self._current_project]
                self._sessions[self._current_project] = PrismSession(self._current_project)

    def get_current_project_root(self) -> Optional[str]:
        """Get the current project root path.

        Returns:
            Current project root or None
        """
        return self._current_project


# Global session manager instance
_session_manager = PrismSessionManager()


def get_session_manager() -> PrismSessionManager:
    """Get the global session manager.

    Returns:
        The singleton session manager instance
    """
    return _session_manager


def run_full_analysis_prism(project_root: str, entry_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run full analysis using Prism backend.

    Args:
        project_root: Root directory of project
        entry_points: List of entry point configurations

    Returns:
        Analysis result compatible with old API format
    """
    manager = get_session_manager()
    manager.set_current_project(project_root)
    session = manager.get_current_session()

    # Scan the project
    scan_stats = session.scan(parallel=True)

    # Build the tree structure and stats for compatibility
    return build_analysis_result_compat(session, entry_points, scan_stats)


def build_analysis_result_compat(
    session: PrismSession,
    entry_points: List[Dict[str, Any]],
    scan_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """Build analysis result in old API format.

    Args:
        session: The Prism session
        entry_points: List of entry point configs
        scan_stats: Scan statistics

    Returns:
        Analysis result dict compatible with old format
    """
    # Convert entry points to Prism format
    ep_objects = [EntryPoint(**ep) for ep in entry_points if ep.get("enabled", True)]

    # Get orphans
    if ep_objects:
        orphan_result = session.get_orphans(ep_objects)
        orphan_paths = {node["relative_path"] for node in orphan_result["orphans"]}
    else:
        orphan_paths = set()

    # Build file tree structure (simplified version for now)
    tree = build_file_tree_compat(session, entry_points, orphan_paths)

    # Get stats
    stats = session.get_stats()

    # Build entry point info
    entry_point_info = {
        ep.label: {
            "path": ep.path,
            "color": ep.color,
            "emoji": ep.emoji,
        }
        for ep in ep_objects
    }

    # Build files list for frontend
    nodes = session.graph.get_nodes()
    files = [
        {
            "path": node.relative_path,
            "name": node.path.name,
            "lines": node.lines,
            "tokens": node.tokens,
        }
        for node in nodes
    ]

    return {
        "tree": tree,
        "files": files,
        "stats": {
            "total": stats["total_files"],
            "connected": stats["total_files"] - len(orphan_paths),
            "orphans": len(orphan_paths),
            "orphan_rate": round(len(orphan_paths) / stats["total_files"] * 100, 1)
            if stats["total_files"] > 0 else 0,
        },
        "entry_points": entry_point_info,
        "config": {
            "entry_points": entry_points,
            "available_colors": [
                {"id": "blue", "emoji": "🔵", "hex": "#58a6ff", "name": "Blue"},
                {"id": "yellow", "emoji": "🟡", "hex": "#d29922", "name": "Yellow"},
                {"id": "green", "emoji": "🟢", "hex": "#3fb950", "name": "Green"},
                {"id": "purple", "emoji": "🟣", "hex": "#a78bfa", "name": "Purple"},
                {"id": "orange", "emoji": "🟠", "hex": "#f0883e", "name": "Orange"},
                {"id": "red", "emoji": "🔴", "hex": "#f85149", "name": "Red"},
                {"id": "brown", "emoji": "🟤", "hex": "#a87058", "name": "Brown"},
            ],
        },
    }


def build_file_tree_compat(
    session: PrismSession,
    entry_points: List[Dict[str, Any]],
    orphan_paths: set
) -> Dict[str, Any]:
    """Build a file tree structure compatible with old format.

    Args:
        session: The Prism session
        entry_points: List of entry point configs
        orphan_paths: Set of orphan file paths

    Returns:
        Tree structure dict
    """
    tree: Dict[str, Any] = {}

    # Get all nodes
    nodes = session.graph.get_nodes()

    # Convert entry points for tracing
    ep_objects = [EntryPoint(**ep) for ep in entry_points if ep.get("enabled", True)]

    # Trace from each entry point to get connections
    ep_traces = {}
    for ep in ep_objects:
        ep_path = Path(session.project_root) / ep.path
        ep_node = session.graph.get_node(ep_path)
        if ep_node:
            trace = session.trace_from_entry_point(ep.path)
            ep_traces[ep.label] = trace

    # Build tree structure
    for node in nodes:
        parts = node.relative_path.split("/")
        current = tree

        # Navigate/create folder structure
        for part in parts[:-1]:
            if part not in current:
                current[part] = {"_type": "folder", "_children": {}}
            current = current[part]["_children"]

        # Add file node
        filename = parts[-1]
        is_orphan = node.relative_path in orphan_paths
        is_entry = any(ep["path"] == node.relative_path for ep in entry_points)

        # Find connections
        connections = []
        connection_paths = {}
        for ep_label, trace in ep_traces.items():
            if node.relative_path in [n["relative_path"] for n in trace["connected_files"]]:
                ep_config = next((e for e in entry_points if e["label"] == ep_label), None)
                if ep_config:
                    connections.append({
                        "entry": ep_config["path"],
                        "color": ep_config["color"],
                        "label": ep_label,
                        "emoji": ep_config.get("emoji", "🔵"),
                    })
                    connection_paths[ep_label] = {
                        "path": trace["connection_paths"].get(node.relative_path, []),
                        "type": trace["edge_types"].get(node.relative_path, "static"),
                    }

        current[filename] = {
            "_type": "file",
            "_path": node.relative_path,
            "_lines": node.lines,
            "_orphan": is_orphan,
            "_entry_point": is_entry,
            "_connections": connections,
            "_connection_paths": connection_paths,
        }

    # Calculate folder contents
    _calculate_folder_contents(tree)

    return tree


def _calculate_folder_contents(node: Dict[str, Any]) -> set:
    """Calculate what labels are contained in each folder (recursive)."""
    if node.get("_type") == "file":
        labels = set()
        if node.get("_orphan"):
            labels.add("ORPHAN")
        for conn in node.get("_connections", []):
            labels.add(conn["label"])
        return labels

    all_labels = set()

    # Get the children dict
    # For explicit folders, children are in _children
    # For root (no _type), children are direct keys in node
    if node.get("_type") == "folder":
        children = node.get("_children", {})
    else:
        # Root level - children are direct keys (excluding _ prefixed)
        children = {k: v for k, v in node.items() if not k.startswith("_")}

    for name, child in children.items():
        child_labels = _calculate_folder_contents(child)
        all_labels.update(child_labels)

    node["_contains"] = sorted(list(all_labels))
    return all_labels


def suggest_entry_points_prism(
    session: PrismSession,
    top_n: int = 500,
    include_tests: bool = False
) -> List[Dict[str, Any]]:
    """Get entry point suggestions using Prism.

    Args:
        session: The Prism session
        top_n: Maximum number of suggestions
        include_tests: Whether to include test files

    Returns:
        List of entry point suggestions
    """
    return session.get_entry_points(top_n=top_n, include_tests=include_tests)


def generate_snapshot_prism(
    session: PrismSession,
    target_path: str,
    options: Dict[str, Any],
    entry_points: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate a snapshot using Prism.

    Args:
        session: The Prism session
        target_path: Relative path to target file
        options: Snapshot options dict
        entry_points: List of entry point configs

    Returns:
        Snapshot result with content and metrics
    """
    # Convert old options format to new SnapshotConfig
    config = SnapshotConfig(
        target_path=target_path,
        parent_depth=options.get("parent_depth", 1),
        include_chain=options.get("include_chain", False),
        chain_length=options.get("chain_length"),
        child_depth=options.get("child_depth", 0),
        child_max_tokens=options.get("child_max_tokens", 0),
        excluded_children=set(options.get("excluded_children", [])),
        include_frontend=options.get("include_frontend", False),
        excluded_frontend=set(options.get("excluded_frontend", [])),
        extra_files=set(options.get("extra_files", [])),
    )

    # Convert entry points
    ep_objects = [EntryPoint(**ep) for ep in entry_points]

    return session.create_snapshot(config, ep_objects)


def get_children_preview_prism(
    session: PrismSession,
    target_path: str,
    entry_points: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Get children preview using Prism.

    Args:
        session: The Prism session
        target_path: Relative path to target file
        entry_points: Optional list of entry point configs for connection info

    Returns:
        Preview with tree and totals
    """
    target_full = Path(session.project_root) / target_path
    target_node = session.graph.get_node(target_full)

    if not target_node:
        return {"error": f"File not found: {target_path}"}

    # Build connection map from entry points
    connections_map = {}
    if entry_points:
        connections_map = _build_connections_map(session, entry_points)

    # Build hierarchical tree matching old format (Python files only)
    tree = _build_children_tree_recursive(
        target_node,
        session.graph,
        session.project_root,
        exclude_frontend=True,
        connections_map=connections_map
    )

    # Flatten for compatibility (Python files only)
    from .models import NodeType
    all_children = session.graph.get_all_children_recursive(target_node)
    python_children = [c for c in all_children if c.node_type == NodeType.PYTHON]
    flat_list = [
        {
            "path": c.relative_path,
            "name": c.path.name,
            "depth": 1,  # Simplified
            "lines": c.lines,
            "tokens": c.tokens,
        }
        for c in python_children
    ]

    # Calculate totals (Python files only)
    totals = {
        "files": len(python_children),
        "lines": sum(c.lines for c in python_children),
        "tokens": sum(c.tokens for c in python_children),
    }

    return {
        "tree": tree,
        "children": flat_list,
        "totals": totals,
    }


def _build_connections_map(
    session: PrismSession,
    entry_points: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, str]]]:
    """Build a map of file paths to their entry point connections.

    Args:
        session: The Prism session
        entry_points: List of entry point configs

    Returns:
        Dict mapping relative paths to list of {label, color, emoji}
    """
    from .models import EntryPoint

    connections_map: Dict[str, List[Dict[str, str]]] = {}

    for ep_config in entry_points:
        if not ep_config.get("enabled", True):
            continue

        ep_path = Path(session.project_root) / ep_config["path"]
        ep_node = session.graph.get_node(ep_path)
        if not ep_node:
            continue

        # Trace from this entry point
        connected, _, _ = session.graph.trace_from_entry_point(ep_node)

        # Add connection info for each connected file
        for node in connected:
            rel_path = node.relative_path
            if rel_path not in connections_map:
                connections_map[rel_path] = []

            # Avoid duplicates
            if not any(c["label"] == ep_config["label"] for c in connections_map[rel_path]):
                connections_map[rel_path].append({
                    "label": ep_config["label"],
                    "color": ep_config.get("color", "#58a6ff"),
                    "emoji": ep_config.get("emoji", "🔵"),
                })

    return connections_map


def get_frontend_preview_prism(
    session: PrismSession,
    target_path: str,
    entry_points: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Get frontend dependencies preview using Prism.

    Matches old behavior: finds templates used by the Python file
    (directly or through imports), then shows their frontend dependencies.

    Args:
        session: The Prism session
        target_path: Relative path to target Python file

    Returns:
        Frontend preview with tree and totals
    """
    from .models import EdgeType

    target_full = Path(session.project_root) / target_path
    target_node = session.graph.get_node(target_full)

    if not target_node:
        return {"error": f"File not found: {target_path}"}

    # Find template files referenced by this Python file or its imports
    template_files: Set[Path] = set()

    # Check direct template references from target file
    direct_children = session.graph._forward_index.get(target_node.path, set())
    for child_path in direct_children:
        # Check edge type
        edge_type = session.graph._get_edge_type(target_node.path, child_path)
        if edge_type == EdgeType.TEMPLATE:
            template_files.add(child_path)

    # If no direct templates, trace through Python imports to find files that use templates
    if not template_files:
        visited: Set[Path] = set()
        to_check = [target_node.path]

        while to_check:
            current_path = to_check.pop()
            if current_path in visited:
                continue
            visited.add(current_path)

            # Check if this file has template references
            children = session.graph._forward_index.get(current_path, set())
            for child_path in children:
                edge_type = session.graph._get_edge_type(current_path, child_path)
                if edge_type == EdgeType.TEMPLATE:
                    template_files.add(child_path)
                # Add Python imports to check recursively
                elif edge_type in (EdgeType.IMPORT, EdgeType.DYNAMIC_IMPORT):
                    child_node = session.graph.get_node(child_path)
                    if child_node and child_node.node_type.value == "python":
                        if child_path not in visited:
                            to_check.append(child_path)

    # If no templates found, return empty
    if not template_files:
        return {
            "tree": {
                "path": target_path,
                "name": target_node.path.name,
                "is_root": True,
                "depth": 0,
                "children": []
            },
            "children": [],
            "totals": {"files": 0, "lines": 0, "tokens": 0},
        }

    # Build frontend dependency tree from template files
    frontend_nodes = []
    visited_frontend: Set[Path] = set()

    def collect_frontend_deps(node_path: Path, depth: int = 0):
        """Recursively collect frontend dependencies."""
        if node_path in visited_frontend or depth > 10:
            return
        visited_frontend.add(node_path)

        node = session.graph.get_node(node_path)
        if not node:
            return

        # Only include frontend types
        if node.node_type.value in ["html", "javascript", "typescript", "css"]:
            frontend_nodes.append((node, depth))

        # Recursively collect children
        children = session.graph._forward_index.get(node_path, set())
        for child_path in children:
            collect_frontend_deps(child_path, depth + 1)

    # Collect all frontend files starting from templates
    for tmpl_path in template_files:
        collect_frontend_deps(tmpl_path, 0)

    # Build connection map from entry points
    connections_map = {}
    if entry_points:
        connections_map = _build_connections_map(session, entry_points)

    # Build hierarchical tree
    tree = {
        "path": target_path,
        "name": target_node.path.name,
        "is_root": True,
        "depth": 0,
        "children": []
    }

    # Sort by depth and add to tree
    frontend_nodes.sort(key=lambda x: x[1])
    for node, depth in frontend_nodes:
        tree["children"].append({
            "path": node.relative_path,
            "name": node.path.name,
            "file_type": node.node_type.value,
            "lines": node.lines,
            "tokens": node.tokens,
            "depth": depth + 1,
            "connections": connections_map.get(node.relative_path, []),
        })

    # Totals
    totals = {
        "files": len(frontend_nodes),
        "lines": sum(n.lines for n, _ in frontend_nodes),
        "tokens": sum(n.tokens for n, _ in frontend_nodes),
    }

    # Flat list
    flat_list = [
        {
            "path": n.relative_path,
            "name": n.path.name,
            "file_type": n.node_type.value,
            "depth": d + 1,
            "lines": n.lines,
            "tokens": n.tokens,
            "connections": connections_map.get(n.relative_path, []),
        }
        for n, d in frontend_nodes
    ]

    return {
        "tree": tree,
        "children": flat_list,
        "totals": totals,
    }


def get_full_dependency_info_prism(
    session: PrismSession,
    target_path: str,
    entry_points: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Get complete dependency info matching old format.

    Returns parents, chains to entry points, and full children tree.
    """
    target_full = Path(session.project_root) / target_path
    target_node = session.graph.get_node(target_full)

    if not target_node:
        return {"error": f"File not found: {target_path}"}

    # Target info
    target_info = {
        "path": target_node.relative_path,
        "name": target_node.path.name,
        "lines": target_node.lines,
        "tokens": target_node.tokens,
        "is_target": True,
    }

    # Get parents
    parent_nodes = session.graph.get_parents(target_node, depth=10)
    parents = []
    for i, p in enumerate(parent_nodes):
        parents.append({
            "path": p.relative_path,
            "name": p.path.name,
            "lines": p.lines,
            "tokens": p.tokens,
            "depth": i + 1,
            "type": "parent",
        })

    # Get chains to entry points
    from .models import EntryPoint
    ep_objects = [EntryPoint(**ep) for ep in entry_points if ep.get("enabled", True)]
    chains = []

    for ep in ep_objects:
        ep_path = Path(session.project_root) / ep.path
        ep_node = session.graph.get_node(ep_path)
        if not ep_node:
            continue

        # Trace from entry point
        connected, connection_paths, edge_types = session.graph.trace_from_entry_point(ep_node)

        # Check if target is connected
        if target_node.path in connection_paths:
            chain_path_list = connection_paths[target_node.path]
            chain_files = []

            # Build chain files (exclude target itself)
            for i, rel_path in enumerate(chain_path_list[:-1]):
                chain_full = Path(session.project_root) / rel_path
                chain_node = session.graph.get_node(chain_full)
                if chain_node:
                    chain_files.append({
                        "path": chain_node.relative_path,
                        "name": chain_node.path.name,
                        "lines": chain_node.lines,
                        "tokens": chain_node.tokens,
                        "depth": i,
                        "type": "chain",
                        "entry_label": ep.label,
                        "entry_color": ep.color,
                        "entry_emoji": ep.emoji,
                    })

            chains.append({
                "label": ep.label,
                "color": ep.color,
                "emoji": ep.emoji,
                "files": chain_files,
            })

    # Build children tree (hierarchical structure matching old format)
    children_tree = _build_children_tree_recursive(
        target_node,
        session.graph,
        session.project_root
    )

    return {
        "target": target_info,
        "parents": parents,
        "chains": chains,
        "children_tree": children_tree,
    }


def _build_children_tree_recursive(
    node,
    graph,
    project_root: Path,
    visited: Optional[Set[Path]] = None,
    depth: int = 0,
    max_depth: int = 10,
    exclude_frontend: bool = False,
    connections_map: Optional[Dict[str, List[Dict[str, str]]]] = None
) -> Dict[str, Any]:
    """Build hierarchical children tree matching old format."""
    from .models import NodeType

    if visited is None:
        visited = set()
    if connections_map is None:
        connections_map = {}

    if depth > max_depth or node.path in visited:
        return {
            "path": node.relative_path,
            "name": node.path.name,
            "lines": node.lines,
            "tokens": node.tokens,
            "depth": depth,
            "children": [],
            "connections": connections_map.get(node.relative_path, []),
        }

    visited.add(node.path)

    tree_node = {
        "path": node.relative_path,
        "name": node.path.name,
        "lines": node.lines,
        "tokens": node.tokens,
        "depth": depth,
        "children": [],
        "connections": connections_map.get(node.relative_path, []),
    }

    # Add root marker
    if depth == 0:
        tree_node["is_root"] = True

    # Get direct children
    child_paths = graph._forward_index.get(node.path, set())
    for child_path in child_paths:
        child_node = graph.get_node(child_path)
        if child_node and child_node.path not in visited:
            # Skip frontend files if requested
            if exclude_frontend and child_node.node_type in (
                NodeType.HTML, NodeType.JAVASCRIPT, NodeType.TYPESCRIPT, NodeType.CSS
            ):
                continue

            child_tree = _build_children_tree_recursive(
                child_node,
                graph,
                project_root,
                visited,
                depth + 1,
                max_depth,
                exclude_frontend,
                connections_map
            )
            tree_node["children"].append(child_tree)

    return tree_node
