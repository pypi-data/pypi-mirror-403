"""
Remote Prism session for SSH projects with caching.

Provides dependency analysis for remote projects by:
1. Batch discovering files with a single `find` command
2. Batch reading files using `tar` + `base64` for efficiency
3. Caching the dependency graph locally to avoid repeated SSH calls
"""
import base64
import io
import json
import tarfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.project import Project
from core.filesystem import SSHFileSystem
from prism.models import Node, NodeType
import ast
import re


def parse_python_imports(content: str) -> List[str]:
    """
    Parse Python imports from content string.
    
    Returns list of module paths (e.g., ['core.agent', '.utils', 'os'])
    """
    imports = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return imports
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Handle relative imports
                if node.level > 0:
                    imports.append('.' * node.level + node.module)
                else:
                    imports.append(node.module)
            elif node.level > 0:
                # from . import x
                imports.append('.' * node.level)
    
    return imports


class SimpleGraph:
    """Simple dependency graph for remote projects."""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}  # path -> Node
        self.edges: Dict[str, set] = {}   # from_path -> set of to_paths
    
    def add_node(self, node: Node) -> None:
        self.nodes[node.path] = node
        if node.path not in self.edges:
            self.edges[node.path] = set()
    
    def add_edge(self, from_path: str, to_path: str) -> None:
        if from_path not in self.edges:
            self.edges[from_path] = set()
        self.edges[from_path].add(to_path)


def get_cache_dir() -> Path:
    """Get or create ~/.prism/prism_cache directory."""
    cache_dir = Path.home() / ".prism" / "prism_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


class RemotePrismSession:
    """
    Prism session for remote (SSH) projects with caching.
    
    Unlike local PrismSession which scans files directly, this class:
    - Uses batch SSH commands to minimize round-trips
    - Caches results locally for fast repeated access
    - Rebuilds cache only when explicitly requested or expired
    """
    
    CACHE_MAX_AGE = 3600  # Cache valid for 1 hour
    
    def __init__(self, project: Project):
        """
        Initialize remote Prism session.
        
        Args:
            project: SSH project to analyze
        """
        if project.type != "ssh":
            raise ValueError(f"RemotePrismSession requires SSH project, got: {project.type}")
        
        self.project = project
        self.project_root = project.path
        self.fs: SSHFileSystem = project.get_filesystem()
        
        # Cache path
        self.cache_path = get_cache_dir() / f"{project.id}.json"
        
        # Graph and file contents (populated by scan)
        self._graph: Optional[SimpleGraph] = None
        self._file_contents: Dict[str, str] = {}
        self._scan_stats: Dict[str, Any] = {}
        

    
    def scan(self, force: bool = False) -> Dict[str, Any]:
        """
        Scan the remote project, using cache if available.
        
        Args:
            force: If True, ignore cache and rescan
            
        Returns:
            Scan statistics dict
        """
        # Check cache
        if not force and self._load_cache():
            return self._scan_stats
        
        # Full scan
        print(f"Scanning remote project: {self.project.name}...")
        
        # 1. Discover files
        files = self._discover_files()
        print(f"  Found {len(files)} files")
        
        # 2. Batch read contents
        self._file_contents = self._batch_read(files)
        print(f"  Read {len(self._file_contents)} files")
        
        # 3. Build graph
        self._graph = self._build_graph(files)
        print(f"  Built graph with {len(self._graph.nodes)} nodes")
        
        # 4. Compute stats
        self._scan_stats = self._compute_stats()
        
        # 5. Save cache
        self._save_cache()
        
        return self._scan_stats
    
    def _discover_files(self) -> List[str]:
        """
        Find all relevant files using single SSH command.
        
        Returns:
            List of relative file paths
        """
        # Find Python, HTML, JS, CSS files, excluding common junk directories
        cmd = """find . -type f \\( -name "*.py" -o -name "*.html" -o -name "*.js" -o -name "*.css" \\) \
            -not -path "*/.venv/*" \
            -not -path "*/.git/*" \
            -not -path "*/__pycache__/*" \
            -not -path "*/node_modules/*" \
            -not -path "*/.mypy_cache/*" \
            -not -path "*/dist/*" \
            -not -path "*/build/*" \
            -not -path "*/.tox/*" \
            -not -path "*/.eggs/*" \
            -not -path "*/.cache/*" \
            -not -path "*/.local/*" \
            -not -path "*/.config/*" \
            -not -path "*/.cursor-server/*" \
            -not -path "*/site-packages/*" \
            2>/dev/null | head -2000"""
        
        output, code = self.fs.exec(cmd)
        
        if code != 0:
            return []
        
        files = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if line and line.startswith("./"):
                # Remove leading ./
                files.append(line[2:])
            elif line:
                files.append(line)
        
        return files
    
    def _batch_read(self, files: List[str]) -> Dict[str, str]:
        """
        Read multiple files in batched SSH commands using tar.
        
        Args:
            files: List of relative file paths
            
        Returns:
            Dict mapping path -> content
        """
        contents = {}
        
        if not files:
            return contents
        
        # Process in batches to avoid command line length limits
        batch_size = 100
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            batch_contents = self._read_batch_tar(batch)
            contents.update(batch_contents)
        
        return contents
    
    def _read_batch_tar(self, files: List[str]) -> Dict[str, str]:
        """
        Read a batch of files using tar + base64.
        
        Args:
            files: List of file paths to read
            
        Returns:
            Dict mapping path -> content
        """
        contents = {}
        
        if not files:
            return contents
        
        # Build file list for tar, filtering out any problematic paths
        safe_files = [f for f in files if not any(c in f for c in ["'", '"', '\n', '\r'])]
        
        if not safe_files:
            return contents
        
        # Create tar archive and encode as base64
        file_list = " ".join(f"'{f}'" for f in safe_files)
        cmd = f"tar -cf - {file_list} 2>/dev/null | base64"
        
        output, code = self.fs.exec(cmd, timeout=60)
        
        if code != 0 or not output.strip():
            # Fallback: read files individually
            return self._read_files_individually(safe_files)
        
        try:
            # Decode base64
            tar_data = base64.b64decode(output.strip())
            
            # Extract from tar
            tar_buffer = io.BytesIO(tar_data)
            with tarfile.open(fileobj=tar_buffer, mode='r:') as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        try:
                            f = tar.extractfile(member)
                            if f:
                                content = f.read().decode('utf-8', errors='ignore')
                                # Normalize path (remove leading ./)
                                path = member.name
                                if path.startswith("./"):
                                    path = path[2:]
                                contents[path] = content
                        except Exception:
                            pass
        except Exception as e:
            # Fallback on any tar error
            print(f"  Tar extraction failed: {e}, falling back to individual reads")
            return self._read_files_individually(safe_files)
        
        return contents
    
    def _read_files_individually(self, files: List[str]) -> Dict[str, str]:
        """
        Fallback: read files one by one.
        
        Args:
            files: List of file paths
            
        Returns:
            Dict mapping path -> content
        """
        contents = {}
        for f in files[:50]:  # Limit to avoid too many SSH calls
            try:
                content = self.fs.read(f)
                contents[f] = content
            except Exception:
                pass
        return contents
    
    def _build_graph(self, files: List[str]) -> SimpleGraph:
        """
        Build dependency graph from file contents.
        
        Args:
            files: List of file paths
            
        Returns:
            Populated SimpleGraph
        """
        graph = SimpleGraph()
        
        # Create nodes for all files
        for file_path in files:
            content = self._file_contents.get(file_path, "")
            
            # Determine node type
            ext = Path(file_path).suffix.lower()
            if ext == '.py':
                node_type = NodeType.PYTHON
            elif ext == '.html':
                node_type = NodeType.HTML
            elif ext == '.js':
                node_type = NodeType.JAVASCRIPT
            elif ext == '.css':
                node_type = NodeType.CSS
            else:
                continue
            
            # Count lines and estimate tokens
            lines = content.count('\n') + 1 if content else 0
            tokens = len(content) // 4  # Rough estimate
            
            node = Node(
                path=file_path,
                node_type=node_type,
                lines=lines,
                tokens=tokens,
            )
            graph.add_node(node)
        
        # Build a set for fast lookup
        files_set = set(files)
        
        # Parse imports and build edges (Python files only for now)
        for file_path in files:
            content = self._file_contents.get(file_path, "")
            if not content:
                continue
            
            ext = Path(file_path).suffix.lower()
            
            if ext == '.py':
                try:
                    imports = parse_python_imports(content)
                    for imp in imports:
                        # Try to resolve import to a file in our graph
                        resolved = self._resolve_import(imp, file_path, files_set)
                        if resolved and resolved in graph.nodes:
                            graph.add_edge(file_path, resolved)
                except Exception:
                    pass
        
        return graph
    
    def _resolve_import(self, import_path: str, from_file: str, all_files: set) -> Optional[str]:
        """
        Try to resolve an import to a file path.
        
        Args:
            import_path: The import string (e.g., 'core.agent' or './utils')
            from_file: The file containing the import
            all_files: List of all known files
            
        Returns:
            Resolved file path or None
        """
        # Handle Python imports
        if not import_path.startswith('.') and not import_path.startswith('/'):
            # Convert module path to file path
            module_path = import_path.replace('.', '/')
            
            # Try various resolutions
            candidates = [
                f"{module_path}.py",
                f"{module_path}/__init__.py",
            ]
            
            for candidate in candidates:
                if candidate in all_files:
                    return candidate
        
        # Handle relative imports
        if import_path.startswith('.'):
            from_dir = str(Path(from_file).parent)
            
            # Count leading dots
            dots = len(import_path) - len(import_path.lstrip('.'))
            remainder = import_path[dots:]
            
            # Go up directories
            base = Path(from_dir)
            for _ in range(dots - 1):
                base = base.parent
            
            if remainder:
                rel_path = str(base / remainder.replace('.', '/'))
            else:
                rel_path = str(base)
            
            candidates = [
                f"{rel_path}.py",
                f"{rel_path}/__init__.py",
            ]
            
            for candidate in candidates:
                # Normalize path
                try:
                    normalized = str(Path(candidate))
                    if normalized in all_files:
                        return normalized
                except Exception:
                    pass
        
        return None
    
    def _compute_stats(self) -> Dict[str, Any]:
        """Compute scan statistics."""
        stats = {
            "total_files": len(self._graph.nodes) if self._graph else 0,
            "project_packages": [],
            "node_types": {},
            "cached": False,
            "cache_time": time.time(),
        }
        
        if self._graph:
            # Count by type
            for node in self._graph.nodes.values():
                type_name = node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type)
                stats["node_types"][type_name] = stats["node_types"].get(type_name, 0) + 1
            
            # Find top-level packages
            packages = set()
            for path in self._graph.nodes.keys():
                parts = Path(path).parts
                if len(parts) > 1 and parts[0] not in ('.', '..'):
                    if (Path(parts[0]) / '__init__.py').as_posix() in self._graph.nodes:
                        packages.add(parts[0])
            stats["project_packages"] = sorted(packages)
        
        return stats
    
    def _save_cache(self) -> None:
        """Save graph and stats to cache file."""
        try:
            cache_data = {
                "version": 1,
                "project_id": self.project.id,
                "project_path": self.project.path,
                "timestamp": time.time(),
                "stats": self._scan_stats,
                "nodes": {},
                "edges": [],
            }
            
            if self._graph:
                # Serialize nodes
                for path, node in self._graph.nodes.items():
                    cache_data["nodes"][path] = {
                        "path": node.path,
                        "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                        "lines": node.lines,
                        "tokens": node.tokens,
                    }
                
                # Serialize edges
                for from_path, to_paths in self._graph.edges.items():
                    for to_path in to_paths:
                        cache_data["edges"].append([from_path, to_path])
            
            self.cache_path.write_text(json.dumps(cache_data, indent=2))
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")
    
    def _load_cache(self) -> bool:
        """
        Load graph from cache if valid.
        
        Returns:
            True if cache was loaded, False if cache invalid/missing
        """
        if not self.cache_path.exists():
            return False
        
        try:
            cache_data = json.loads(self.cache_path.read_text())
            
            # Check cache validity
            if cache_data.get("project_id") != self.project.id:
                return False
            if cache_data.get("project_path") != self.project.path:
                return False
            
            # Check age
            cache_age = time.time() - cache_data.get("timestamp", 0)
            if cache_age > self.CACHE_MAX_AGE:
                return False
            
            # Rebuild graph from cache
            self._graph = SimpleGraph()
            
            for path, node_data in cache_data.get("nodes", {}).items():
                node_type = NodeType(node_data["type"]) if node_data["type"] in [t.value for t in NodeType] else NodeType.PYTHON
                node = Node(
                    path=node_data["path"],
                    node_type=node_type,
                    lines=node_data.get("lines", 0),
                    tokens=node_data.get("tokens", 0),
                )
                self._graph.add_node(node)
            
            for from_path, to_path in cache_data.get("edges", []):
                if from_path in self._graph.nodes and to_path in self._graph.nodes:
                    self._graph.add_edge(from_path, to_path)
            
            self._scan_stats = cache_data.get("stats", {})
            self._scan_stats["cached"] = True
            
            return True
            
        except Exception as e:
            print(f"Warning: Failed to load cache: {e}")
            return False
    
    # ========== Query Methods (match PrismSession interface) ==========
    
    def get_entry_points(self, top_n: int = 20, include_tests: bool = False) -> List[Dict[str, Any]]:
        """
        Get potential entry points ranked by dependency count.
        
        Args:
            top_n: Maximum number to return
            include_tests: Whether to include test files
            
        Returns:
            List of entry point dicts
        """
        if not self._graph:
            self.scan()
        
        results = []
        
        for path, node in self._graph.nodes.items():
            # Skip tests if not wanted
            if not include_tests and ('test' in path.lower() or path.startswith('tests/')):
                continue
            
            # Count dependencies (files this file imports)
            dep_count = len(self._graph.edges.get(path, set()))
            
            results.append({
                "path": path,
                "deps": dep_count,
                "lines": node.lines,
                "tokens": node.tokens,
                "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
            })
        
        # Sort by dependency count descending
        results.sort(key=lambda x: x["deps"], reverse=True)
        
        return results[:top_n]
    
    def get_dependency_graph(
        self,
        target_file: str,
        parent_depth: int = 1,
        child_depth: Optional[int] = None,
        include_frontend: bool = False,
    ) -> Dict[str, Any]:
        """
        Get dependency information for a file.
        
        Args:
            target_file: Path to the target file
            parent_depth: How many levels of parents to include
            child_depth: How many levels of children (None = all)
            include_frontend: Whether to include HTML/JS/CSS
            
        Returns:
            Dict with target, parents, children info
        """
        if not self._graph:
            self.scan()
        
        if target_file not in self._graph.nodes:
            return {"error": f"File not found: {target_file}"}
        
        target_node = self._graph.nodes[target_file]
        
        def node_to_dict(node: Node) -> Dict[str, Any]:
            return {
                "path": node.path,
                "relative_path": node.path,
                "lines": node.lines,
                "tokens": node.tokens,
                "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
            }
        
        # Get children (files this file imports)
        children = []
        visited = set()
        
        def collect_children(path: str, depth: int):
            if child_depth is not None and depth > child_depth:
                return
            if path in visited:
                return
            visited.add(path)
            
            for child_path in self._graph.edges.get(path, set()):
                if child_path not in self._graph.nodes:
                    continue
                child_node = self._graph.nodes[child_path]
                
                # Filter frontend if needed
                if not include_frontend and child_node.node_type in (NodeType.HTML, NodeType.JAVASCRIPT, NodeType.CSS):
                    continue
                
                if child_path != target_file:
                    children.append(node_to_dict(child_node))
                collect_children(child_path, depth + 1)
        
        collect_children(target_file, 1)
        
        # Get parents (files that import this file)
        parents = []
        
        if parent_depth > 0:
            # Build reverse edges
            reverse_edges: Dict[str, set] = {}
            for from_path, to_paths in self._graph.edges.items():
                for to_path in to_paths:
                    if to_path not in reverse_edges:
                        reverse_edges[to_path] = set()
                    reverse_edges[to_path].add(from_path)
            
            visited_parents = set()
            
            def collect_parents(path: str, depth: int):
                if depth > parent_depth:
                    return
                if path in visited_parents:
                    return
                visited_parents.add(path)
                
                for parent_path in reverse_edges.get(path, set()):
                    if parent_path not in self._graph.nodes:
                        continue
                    parent_node = self._graph.nodes[parent_path]
                    
                    if parent_path != target_file:
                        parents.append(node_to_dict(parent_node))
                    collect_parents(parent_path, depth + 1)
            
            collect_parents(target_file, 1)
        
        return {
            "target": node_to_dict(target_node),
            "parents": parents,
            "children": children,
        }
    
    def trace_from_entry_point(self, entry_point: str) -> Dict[str, Any]:
        """
        Trace all files connected to an entry point.
        
        Args:
            entry_point: Path to the entry point file
            
        Returns:
            Dict with connected files info
        """
        if not self._graph:
            self.scan()
        
        if entry_point not in self._graph.nodes:
            return {"error": f"Entry point not found: {entry_point}"}
        
        # BFS from entry point
        connected = []
        visited = {entry_point}
        queue = [entry_point]
        
        while queue:
            current = queue.pop(0)
            node = self._graph.nodes.get(current)
            
            if node:
                connected.append({
                    "path": node.path,
                    "relative_path": node.path,
                    "lines": node.lines,
                    "tokens": node.tokens,
                    "type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                })
            
            for child in self._graph.edges.get(current, set()):
                if child not in visited:
                    visited.add(child)
                    queue.append(child)
        
        return {"connected_files": connected}
    
    def stats(self) -> Dict[str, Any]:
        """Get scan statistics."""
        return self._scan_stats
