"""Main PrismSession controller for dependency analysis."""
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
import tiktoken

from .models import Node, Edge, EdgeType, NodeType, EntryPoint, SnapshotConfig
from .scanner import FileScanner
from .parsers import (
    PythonParser,
    HTMLParser,
    JavaScriptParser,
    CSSParser,
    PathResolver
)
from .graph import DependencyGraph
from .snapshot import SnapshotBuilder


class PrismSession:
    """Main interface for analyzing a project's dependencies.

    This is a stateful session tied to a specific project. It handles scanning,
    parsing, graph building, and snapshot generation for that project only.
    """

    def __init__(
        self,
        project_root: str | Path,
        exclude_patterns: Optional[List[str]] = None,
        exclude_files: Optional[List[str]] = None,
    ):
        """Initialize a Prism analysis session.

        Args:
            project_root: Root directory of the project to analyze
            exclude_patterns: Directory patterns to exclude from scanning
            exclude_files: Specific filenames to exclude from scanning
        """
        self.project_root = Path(project_root).resolve()
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {project_root}")

        # Initialize components
        # include_init=True is critical for correct dependency tracing
        # __init__.py files are loaded when importing packages and may re-export modules
        self.scanner = FileScanner(
            self.project_root,
            exclude_patterns=exclude_patterns,
            exclude_files=exclude_files,
            include_init=True
        )
        self.graph = DependencyGraph(self.project_root)
        self.snapshot_builder = SnapshotBuilder(self.project_root)
        self.path_resolver = PathResolver(self.project_root)

        # Session state
        self._is_scanned = False
        self._project_packages: List[str] = []
        self._template_folder: Optional[Path] = None
        self._static_folder: Optional[Path] = None
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def scan(self, parallel: bool = False) -> Dict[str, Any]:
        """Scan the project and build the dependency graph.

        Args:
            parallel: Whether to use parallel processing

        Returns:
            Dictionary with scan statistics
        """
        # Detect project structure
        self._project_packages = self.scanner.detect_project_packages()
        self._template_folder = self.scanner.find_template_folder()
        self._static_folder = self.scanner.find_static_folder()

        # Scan all files
        all_files = self.scanner.scan_all_files(parallel=parallel)

        # Create nodes
        for file_path in all_files:
            node = self._create_node(file_path)
            self.graph.add_node(node)

        # Parse dependencies and create edges
        if parallel and len(all_files) > 50:
            self._build_edges_parallel(all_files)
        else:
            self._build_edges_sequential(all_files)

        self._is_scanned = True

        return {
            "total_files": len(all_files),
            "project_packages": self._project_packages,
            "template_folder": str(self._template_folder) if self._template_folder else None,
            "static_folder": str(self._static_folder) if self._static_folder else None,
            "node_types": self.graph._count_node_types(),
        }

    def get_entry_points(
        self,
        top_n: int = 500,
        include_tests: bool = False
    ) -> List[Dict[str, Any]]:
        """Get suggested entry points based on dependency tree size.

        Args:
            top_n: Maximum number of suggestions
            include_tests: Whether to include test files

        Returns:
            List of entry point suggestions with metadata
        """
        self._ensure_scanned()

        suggestions = self.graph.suggest_entry_points(top_n, include_tests)

        return [
            {
                "path": node.relative_path,
                "name": node.path.name,
                "deps": count,
                "lines": node.lines,
                "type": node.node_type.value,
            }
            for node, count in suggestions
        ]

    def get_dependency_graph(
        self,
        target_file: str,
        parent_depth: int = 1,
        child_depth: Optional[int] = None,
        include_frontend: bool = False
    ) -> Dict[str, Any]:
        """Get dependency information for a specific file.

        Args:
            target_file: Relative path to target file
            parent_depth: How many levels of parents to include
            child_depth: How many levels of children (None = all)
            include_frontend: Whether to include frontend dependencies

        Returns:
            Dictionary with parents, children, and metadata
        """
        self._ensure_scanned()

        target_path = self.project_root / target_file
        target_node = self.graph.get_node(target_path)

        if not target_node:
            return {"error": f"File not found: {target_file}"}

        # Get parents
        parents = []
        if parent_depth > 0:
            parent_nodes = self.graph.get_parents(target_node, parent_depth)
            parents = [self._node_to_dict(n) for n in parent_nodes]

        # Get children
        children = []
        if child_depth is None:
            child_nodes = self.graph.get_all_children_recursive(target_node)
        elif child_depth > 0:
            child_nodes = self.graph.get_children(target_node, child_depth)
        else:
            child_nodes = []

        # Filter frontend if requested
        if include_frontend:
            children = [self._node_to_dict(n) for n in child_nodes]
        else:
            # Only Python files
            children = [
                self._node_to_dict(n) for n in child_nodes
                if n.node_type == NodeType.PYTHON
            ]

        return {
            "target": self._node_to_dict(target_node),
            "parents": parents,
            "children": children,
            "stats": {
                "total_parents": len(parents),
                "total_children": len(children),
            }
        }

    def create_snapshot(
        self,
        config: SnapshotConfig | Dict[str, Any],
        entry_points: Optional[List[EntryPoint | Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generate a formatted dependency snapshot.

        Args:
            config: Snapshot configuration (object or dict)
            entry_points: Optional entry points for chain tracing

        Returns:
            Dictionary with 'content' and 'metrics' keys
        """
        self._ensure_scanned()

        # Convert dict to SnapshotConfig if needed
        if isinstance(config, dict):
            config = SnapshotConfig(**config)

        # Convert entry point dicts to objects if needed
        ep_objects = []
        if entry_points:
            for ep in entry_points:
                if isinstance(ep, dict):
                    ep_objects.append(EntryPoint(**ep))
                else:
                    ep_objects.append(ep)

        return self.snapshot_builder.build_snapshot(
            self.graph,
            config,
            ep_objects if ep_objects else None
        )

    def trace_from_entry_point(
        self,
        entry_point_path: str
    ) -> Dict[str, Any]:
        """Trace all dependencies from an entry point.

        Args:
            entry_point_path: Relative path to entry point file

        Returns:
            Dictionary with connected files and metadata
        """
        self._ensure_scanned()

        ep_path = self.project_root / entry_point_path
        ep_node = self.graph.get_node(ep_path)

        if not ep_node:
            return {"error": f"Entry point not found: {entry_point_path}"}

        connected, connection_paths, edge_types = self.graph.trace_from_entry_point(ep_node)

        return {
            "entry_point": self._node_to_dict(ep_node),
            "connected_files": [self._node_to_dict(n) for n in connected],
            "total_connected": len(connected),
            "connection_paths": {
                str(k.relative_to(self.project_root)): v
                for k, v in connection_paths.items()
            },
            "edge_types": {
                str(k.relative_to(self.project_root)): v.value
                for k, v in edge_types.items()
            }
        }

    def get_orphans(self, entry_points: List[EntryPoint | Dict[str, Any]]) -> Dict[str, Any]:
        """Find files not connected to any entry point.

        Args:
            entry_points: List of entry points to check against

        Returns:
            Dictionary with orphan files and statistics
        """
        self._ensure_scanned()

        # Convert dicts to EntryPoint objects
        ep_nodes = []
        for ep in entry_points:
            if isinstance(ep, dict):
                ep_path = self.project_root / ep["path"]
            else:
                ep_path = self.project_root / ep.path

            ep_node = self.graph.get_node(ep_path)
            if ep_node:
                ep_nodes.append(ep_node)

        orphan_nodes = self.graph.get_orphan_nodes(ep_nodes)

        return {
            "orphans": [self._node_to_dict(n) for n in orphan_nodes],
            "total_orphans": len(orphan_nodes),
            "orphan_rate": round(len(orphan_nodes) / len(self.graph.get_nodes()) * 100, 1)
            if self.graph.get_nodes() else 0
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get overall statistics about the analyzed project.

        Returns:
            Dictionary with project statistics
        """
        self._ensure_scanned()

        return {
            "project_root": str(self.project_root),
            "total_files": len(self.graph.get_nodes()),
            "total_edges": len(self.graph.get_edges()),
            "project_packages": self._project_packages,
            "node_types": self.graph._count_node_types(),
            "template_folder": str(self._template_folder) if self._template_folder else None,
            "static_folder": str(self._static_folder) if self._static_folder else None,
        }

    def _create_node(self, file_path: Path) -> Node:
        """Create a node from a file path.

        Args:
            file_path: Absolute path to file

        Returns:
            Node object
        """
        node_type = NodeType.from_extension(file_path.suffix)

        try:
            relative_path = str(file_path.relative_to(self.project_root))
        except ValueError:
            relative_path = str(file_path)

        # Count lines and tokens
        lines = self._count_lines(file_path)
        content = self._read_file(file_path)
        tokens = self._count_tokens(content)

        return Node(
            path=file_path.resolve(),
            node_type=node_type,
            relative_path=relative_path,
            lines=lines,
            tokens=tokens
        )

    def _build_edges_sequential(self, files: Set[Path]) -> None:
        """Build edges sequentially.

        Args:
            files: Set of all files in project
        """
        for file_path in files:
            self._parse_and_add_edges(file_path, files)

    def _build_edges_parallel(self, files: Set[Path]) -> None:
        """Build edges using parallel processing.

        Args:
            files: Set of all files in project
        """
        max_workers = min(mp.cpu_count(), 8)
        files_list = list(files)

        # Convert paths to strings for serialization
        template_folder_str = str(self._template_folder) if self._template_folder else None
        static_folder_str = str(self._static_folder) if self._static_folder else None

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            args_list = [
                (str(f), [str(x) for x in files], str(self.project_root), self._project_packages, template_folder_str, static_folder_str)
                for f in files_list
            ]
            results = executor.map(_parse_file_static, args_list)

            for file_str, deps in results:
                source_path = Path(file_str)
                source_node = self.graph.get_node(source_path)
                if not source_node:
                    continue

                for target_str, edge_type_str in deps:
                    target_path = Path(target_str)
                    target_node = self.graph.get_node(target_path)
                    if target_node:
                        edge = Edge(
                            source=source_node,
                            target=target_node,
                            edge_type=EdgeType(edge_type_str)
                        )
                        self.graph.add_edge(edge)

    def _parse_and_add_edges(self, file_path: Path, all_files: Set[Path]) -> None:
        """Parse a file and add its edges to the graph.

        Args:
            file_path: Path to file to parse
            all_files: Set of all files in project
        """
        source_node = self.graph.get_node(file_path)
        if not source_node:
            return

        # Get appropriate parser
        parser = self._get_parser(source_node.node_type)
        if not parser:
            return

        # Parse dependencies
        deps = parser.parse(file_path, self.project_root)

        # Resolve and create edges
        for ref, edge_type in deps:
            target_paths = self._resolve_reference(
                ref, file_path, source_node.node_type, edge_type, all_files
            )

            for target_path in target_paths:
                target_node = self.graph.get_node(target_path)
                if target_node:
                    edge = Edge(
                        source=source_node,
                        target=target_node,
                        edge_type=edge_type
                    )
                    self.graph.add_edge(edge)

    def _get_parser(self, node_type: NodeType):
        """Get the appropriate parser for a node type."""
        if node_type == NodeType.PYTHON:
            return PythonParser(frozenset(self._project_packages))
        elif node_type == NodeType.HTML:
            return HTMLParser()
        elif node_type in (NodeType.JAVASCRIPT, NodeType.TYPESCRIPT):
            return JavaScriptParser()
        elif node_type == NodeType.CSS:
            return CSSParser()
        return None

    def _resolve_reference(
        self,
        ref: str,
        source_file: Path,
        source_type: NodeType,
        edge_type: EdgeType,
        all_files: Set[Path]
    ) -> List[Path]:
        """Resolve a reference string to actual file paths."""
        # Handle template references (from Python render_template calls)
        if edge_type == EdgeType.TEMPLATE:
            resolved = self.path_resolver.resolve_template(
                ref, source_file, self._template_folder, self._static_folder
            )
            return [resolved] if resolved else []

        # Handle other references based on source type
        if source_type == NodeType.PYTHON:
            return self.path_resolver.resolve_python_import(ref, source_file, all_files)
        elif source_type == NodeType.HTML:
            # Could be template or frontend reference
            if ref.endswith(('.html', '.htm', '.jinja', '.jinja2')):
                resolved = self.path_resolver.resolve_template(
                    ref, source_file, self._template_folder, self._static_folder
                )
                return [resolved] if resolved else []
            else:
                resolved = self.path_resolver.resolve_frontend_ref(
                    ref, source_file, self._static_folder
                )
                return [resolved] if resolved else []
        elif source_type in (NodeType.JAVASCRIPT, NodeType.TYPESCRIPT, NodeType.CSS):
            resolved = self.path_resolver.resolve_frontend_ref(
                ref, source_file, self._static_folder
            )
            return [resolved] if resolved else []
        return []

    def _ensure_scanned(self) -> None:
        """Ensure the project has been scanned."""
        if not self._is_scanned:
            raise RuntimeError(
                "Project has not been scanned. Call scan() first."
            )

    def _node_to_dict(self, node: Node) -> Dict[str, Any]:
        """Convert a node to dictionary."""
        return node.to_dict()

    def _read_file(self, path: Path) -> str:
        """Read file content."""
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _count_lines(self, path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(path, "rb") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if not text:
            return 0
        try:
            return len(self._encoding.encode(text))
        except Exception:
            return len(text.split())


def _parse_file_static(args):
    """Static function for parallel file parsing."""
    file_str, all_files_str, project_root_str, project_packages, template_folder_str, static_folder_str = args
    file_path = Path(file_str)
    project_root = Path(project_root_str)
    all_files = {Path(f) for f in all_files_str}
    template_folder = Path(template_folder_str) if template_folder_str else None
    static_folder = Path(static_folder_str) if static_folder_str else None

    node_type = NodeType.from_extension(file_path.suffix)

    # Get parser
    if node_type == NodeType.PYTHON:
        parser = PythonParser(frozenset(project_packages))
    elif node_type == NodeType.HTML:
        parser = HTMLParser()
    elif node_type in (NodeType.JAVASCRIPT, NodeType.TYPESCRIPT):
        parser = JavaScriptParser()
    elif node_type == NodeType.CSS:
        parser = CSSParser()
    else:
        return file_str, []

    # Parse
    deps = parser.parse(file_path, project_root)

    # Resolve references
    resolver = PathResolver(project_root)
    resolved_deps = []

    for ref, edge_type in deps:
        # Handle template references specially
        if edge_type == EdgeType.TEMPLATE:
            target = resolver.resolve_template(ref, file_path, template_folder, static_folder)
            if target:
                resolved_deps.append((str(target), edge_type.value))
        elif node_type == NodeType.PYTHON:
            targets = resolver.resolve_python_import(ref, file_path, all_files)
            for target in targets:
                resolved_deps.append((str(target), edge_type.value))
        elif node_type == NodeType.HTML:
            if ref.endswith(('.html', '.htm', '.jinja', '.jinja2')):
                target = resolver.resolve_template(ref, file_path, template_folder, static_folder)
                if target:
                    resolved_deps.append((str(target), edge_type.value))
            else:
                target = resolver.resolve_frontend_ref(ref, file_path, static_folder)
                if target:
                    resolved_deps.append((str(target), edge_type.value))
        elif node_type in (NodeType.JAVASCRIPT, NodeType.TYPESCRIPT, NodeType.CSS):
            target = resolver.resolve_frontend_ref(ref, file_path, static_folder)
            if target:
                resolved_deps.append((str(target), edge_type.value))

    return file_str, resolved_deps
