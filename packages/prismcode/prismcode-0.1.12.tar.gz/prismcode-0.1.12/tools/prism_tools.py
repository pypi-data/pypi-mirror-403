"""Prism dependency analysis tools for the Prism agent.

These tools provide dependency graph analysis, entry point discovery,
and smart dependency-aware focus management.
"""
from pathlib import Path
from typing import Optional, Dict, Any, List, Set
from core.signella import Signella
from core.filesystem import get_current_filesystem, get_project_root

# Lazy import to avoid circular dependencies
_session = None
_store = Signella()


def _get_fs():
    """Get the current filesystem (convenience wrapper)."""
    return get_current_filesystem()


def _get_current_project():
    """Get the current project, or None if using default local."""
    session_id = _store.get('session', 'current', default='default')
    project_id = _store.get('session', session_id, 'project_id', default='local')
    
    if project_id == 'local':
        return None
    
    try:
        from core.project_manager import ProjectManager
        pm = ProjectManager()
        return pm.get(project_id)
    except Exception:
        return None


def _is_ssh_project() -> bool:
    """Check if current project is SSH type."""
    project = _get_current_project()
    return project is not None and project.type == 'ssh'


# Cache for remote sessions
_remote_session = None
_remote_session_project_id = None


def _get_current_session_id() -> str:
    """Get current session ID from Signella."""
    return _store.get('session', 'current', default='default')


def _get_focused_files() -> set:
    """Get focused files for current session from Signella."""
    session_id = _get_current_session_id()
    files = _store.get('focus', session_id, 'files', default=[])
    return set(files) if files else set()


def _get_available_context_budget() -> int:
    """Get available context budget in tokens before compaction would trigger.
    
    Returns the number of tokens we can safely add to focus.
    """
    try:
        from core.context_management.tokens import ModelProfile
        from core.context_management.ground_truth import HistoryManager
        from core.agent import _get_history_path
        
        # Get model profile from config
        from config import AGENT_CONFIG
        model = AGENT_CONFIG.get('model', 'anthropic/claude-sonnet-4')
        profile = ModelProfile.from_name(model)
        
        # Get accurate counter using LiteLLM
        counter = profile.counter(use_litellm=True)
        
        # Get max_tokens from config (default 8192)
        max_tokens = AGENT_CONFIG.get('litellm_params', {}).get('max_tokens', 8192)
        
        # Budget = 85% of (context_window - max_tokens)
        available_window = profile.context_window - max_tokens
        total_budget = int(available_window * 0.85)
        
        # Get current session's working tokens
        session_id = _get_current_session_id()
        history_path = _get_history_path(session_id)
        
        if history_path.exists():
            hm = HistoryManager.load(history_path)
            
            # Count current working history
            working_tokens = 0
            for entry in hm.working.entries:
                working_tokens += counter.count_message(entry.message)
            
            # Count currently focused files using filesystem abstraction
            focused_files = _get_focused_files()
            focus_tokens = 0
            fs = _get_fs()
            for abs_path in focused_files:
                try:
                    content = fs.read(abs_path)
                    focus_tokens += counter.count(content)
                except:
                    pass
            
            # Available = budget - working - focused - system prompt buffer (~2000)
            available = total_budget - working_tokens - focus_tokens - 2000
            return max(0, available)
        else:
            # New session, most of budget available
            return total_budget - 5000  # Reserve for system prompt + buffer
            
    except Exception as e:
        # Fallback: assume 50k available
        return 50000


def _set_focused_files(files: set):
    """Set focused files for current session in Signella."""
    session_id = _get_current_session_id()
    _store.set('focus', session_id, 'files', list(files))


def _get_prism_session():
    """Get or create the PrismSession for the current project.
    
    Returns either a local PrismSession or RemotePrismSession for SSH projects.
    """
    global _session, _remote_session, _remote_session_project_id
    
    # Check if we're on an SSH project
    project = _get_current_project()
    
    if project and project.type == 'ssh':
        # Use RemotePrismSession for SSH projects
        from prism.remote_session import RemotePrismSession
        
        # Create new session if needed or if project changed
        if _remote_session is None or _remote_session_project_id != project.id:
            _remote_session = RemotePrismSession(project)
            _remote_session.scan()
            _remote_session_project_id = project.id
        
        return _remote_session
    else:
        # Use local PrismSession
        from prism.session import PrismSession

        cwd = Path.cwd().resolve()

        # Create new session if needed or if project changed
        if _session is None or _session.project_root != cwd:
            _session = PrismSession(cwd)
            try:
                _session.scan()
            except Exception as e:
                print(f"Warning: Initial project scan failed: {e}")

        # Auto-scan if session exists but wasn't scanned
        if not _session._is_scanned:
            try:
                _session.scan()
            except Exception as e:
                raise RuntimeError(f"Failed to scan project: {e}")

        return _session


def _get_entry_points() -> List[Dict[str, Any]]:
    """Get stored entry points from Signella."""
    session_id = _get_current_session_id()
    return _store.get('prism', session_id, 'entry_points', default=[])


def _set_entry_points(entry_points: List[Dict[str, Any]]):
    """Store entry points in Signella."""
    session_id = _get_current_session_id()
    _store.set('prism', session_id, 'entry_points', entry_points)


def _format_file_info(node_dict: Dict[str, Any], indent: int = 0) -> str:
    """Format a node dict as a concise line."""
    prefix = "  " * indent
    rel_path = node_dict.get("relative_path", "unknown")
    lines = node_dict.get("lines", 0)
    tokens = node_dict.get("tokens", 0)
    return f"{prefix}{rel_path} ({lines} lines, {tokens} tokens)"


def find_entry_points(top_n: int = 20, include_tests: bool = False) -> str:
    """Find potential entry points in the project ranked by dependency count.
    
    Entry points are files that import many other files - typically main scripts,
    API servers, CLI tools, etc. Files with more dependencies are ranked higher.
    
    Args:
        top_n: Maximum number of entry points to return (default 20)
        include_tests: Whether to include test files in results (default False)
    
    Returns:
        Ranked list of potential entry points with stats
    """
    try:
        session = _get_prism_session()
        suggestions = session.get_entry_points(top_n=top_n, include_tests=include_tests)
        
        if not suggestions:
            return "No entry points found. The project may have no files with dependencies."
        
        lines = [f"Top {len(suggestions)} potential entry points:\n"]
        for i, ep in enumerate(suggestions, 1):
            lines.append(
                f"{i:2}. {ep['path']}\n"
                f"    └─ {ep['deps']} deps, {ep['lines']} lines, {ep['type']}"
            )
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error finding entry points: {e}"


def get_dependency_info(
    file_path: str,
    child_depth: int = -1,
    parent_depth: int = 1,
    include_frontend: bool = False,
    max_tokens: str = None
) -> str:
    """Get dependency information for a file (dry run - doesn't focus anything).
    
    Shows what files would be included if you called focus_dependencies with
    the same parameters. Use this to preview before focusing.
    
    Args:
        file_path: Relative path to the target Python file
        child_depth: How many levels of children to include (-1 = all, 0 = none)
        parent_depth: How many levels of parents to include (default 1)
        include_frontend: Whether to include HTML/JS/CSS files (default False)
        max_tokens: Optional token budget - if set, limits files returned
    
    Returns:
        Dependency tree with file paths, line counts, and token counts
    """
    try:
        # Convert max_tokens to int if provided as string
        if max_tokens is not None:
            max_tokens = int(max_tokens)
        
        session = _get_prism_session()
        
        # Normalize child_depth: -1 means all (None internally)
        internal_child_depth = None if child_depth == -1 else child_depth
        
        result = session.get_dependency_graph(
            target_file=file_path,
            parent_depth=parent_depth,
            child_depth=internal_child_depth,
            include_frontend=include_frontend
        )
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        target = result["target"]
        parents = result["parents"]
        children = result["children"]
        
        # Calculate totals
        all_files = [target] + parents + children
        total_lines = sum(f.get("lines", 0) for f in all_files)
        total_tokens = sum(f.get("tokens", 0) for f in all_files)
        
        # Apply token budget if specified
        if max_tokens is not None and total_tokens > max_tokens:
            # Sort children by tokens and cut off
            sorted_children = sorted(children, key=lambda x: x.get("tokens", 0))
            budget_children = []
            running_tokens = target.get("tokens", 0) + sum(p.get("tokens", 0) for p in parents)
            
            for child in sorted_children:
                child_tokens = child.get("tokens", 0)
                if running_tokens + child_tokens <= max_tokens:
                    budget_children.append(child)
                    running_tokens += child_tokens
            
            children = budget_children
            total_lines = sum(f.get("lines", 0) for f in [target] + parents + children)
            total_tokens = running_tokens
        
        # Format output
        lines = [
            f"Dependency info for: {file_path}",
            f"{'─' * 50}",
            f"",
            f"📎 TARGET:",
            _format_file_info(target, indent=1),
            f""
        ]
        
        if parents:
            lines.append(f"⬆️  PARENTS ({len(parents)} files):")
            for p in parents:
                lines.append(_format_file_info(p, indent=1))
            lines.append("")
        
        if children:
            lines.append(f"⬇️  CHILDREN ({len(children)} files):")
            for c in children:
                lines.append(_format_file_info(c, indent=1))
            lines.append("")
        
        lines.extend([
            f"{'─' * 50}",
            f"TOTALS: {len([target] + parents + children)} files, {total_lines} lines, {total_tokens} tokens"
        ])
        
        if max_tokens is not None:
            lines.append(f"(Limited to {max_tokens} token budget)")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error getting dependency info: {e}"


def macro_focus(
    file_path: str,
    child_depth: int = -1,
    parent_depth: int = -1,
    include_frontend: bool = True,
    max_tokens: str = None
) -> str:
    """Add a file and its full dependency tree to the HUD focus.
    
    Performs a comprehensive focus operation - by default includes the full
    backend (all parent and child depths) AND frontend (HTML/JS/CSS) files.
    Adds files breadth-first until the token budget is exhausted.
    
    Args:
        file_path: Relative path to the target Python file
        child_depth: How many levels of children to include (-1 = all, 0 = none)
        parent_depth: How many levels of parents to include (-1 = all, 0 = none)
        include_frontend: Whether to include HTML/JS/CSS files (default True)
        max_tokens: Optional token budget - stops adding files when exceeded
    
    Returns:
        Summary of files added to focus with dependency tree
    """
    try:
        session = _get_prism_session()
        
        # Auto-detect max_tokens if not provided
        if max_tokens is None:
            max_tokens = _get_available_context_budget()
            auto_budget = True
        else:
            max_tokens = int(max_tokens)
            auto_budget = False
        
        # Get target file info
        target_result = session.get_dependency_graph(
            target_file=file_path,
            parent_depth=0,
            child_depth=0,
            include_frontend=False
        )
        
        if "error" in target_result:
            return f"Error: {target_result['error']}"
        
        target = target_result["target"]
        
        # Breadth-first expansion from target
        # Order: target -> parents d1 -> children d1 -> parents d2 -> children d2 -> frontend -> ...
        files_to_focus = []
        running_tokens = 0
        seen_paths = set()
        
        def add_file(f):
            nonlocal running_tokens
            path = f.get("path") or f.get("relative_path")
            if path in seen_paths:
                return False
            tokens = f.get("tokens", 0)
            if running_tokens + tokens > max_tokens:
                return False
            seen_paths.add(path)
            files_to_focus.append(f)
            running_tokens += tokens
            return True
        
        # 1. Target file (always include)
        add_file(target)
        
        # 2. Expand parents and children breadth-first
        max_depth = 10 if child_depth == -1 else max(child_depth, parent_depth if parent_depth != -1 else 10)
        
        for depth in range(1, max_depth + 1):
            if running_tokens >= max_tokens:
                break
            
            # Get parents at this depth
            if parent_depth == -1 or depth <= parent_depth:
                parent_result = session.get_dependency_graph(
                    target_file=file_path,
                    parent_depth=depth,
                    child_depth=0,
                    include_frontend=False
                )
                for p in parent_result.get("parents", []):
                    if not add_file(p):
                        break
            
            # Get children at this depth
            if child_depth == -1 or depth <= child_depth:
                child_result = session.get_dependency_graph(
                    target_file=file_path,
                    parent_depth=0,
                    child_depth=depth,
                    include_frontend=False
                )
                for c in child_result.get("children", []):
                    if not add_file(c):
                        break
        
        # 3. Add frontend files if budget allows and requested
        if include_frontend and running_tokens < max_tokens:
            frontend_result = session.get_dependency_graph(
                target_file=file_path,
                parent_depth=1,
                child_depth=None,  # All children
                include_frontend=True
            )
            # Filter to just frontend files (HTML/JS/CSS)
            frontend_types = {'html', 'javascript', 'css', 'typescript'}
            for f in frontend_result.get("children", []):
                if f.get("type") in frontend_types:
                    if not add_file(f):
                        break
        
        # Add to focus
        focused = _get_focused_files()
        added = []
        skipped = []
        fs = _get_fs()
        
        for f in files_to_focus:
            # Get relative path from the file info
            rel_path = f.get("relative_path") or f.get("path", "")
            # Convert to absolute path using filesystem
            abs_path = fs.absolute(rel_path)
            
            if abs_path not in focused:
                if fs.exists(rel_path):
                    focused.add(abs_path)
                    added.append(f)
                else:
                    skipped.append(rel_path or "unknown")
            else:
                skipped.append((rel_path or "unknown") + " (already focused)")
        
        _set_focused_files(focused)
        
        # Calculate totals
        total_lines = sum(f.get("lines", 0) for f in files_to_focus)
        total_tokens = sum(f.get("tokens", 0) for f in files_to_focus)
        
        # Format output
        lines = [
            f"✓ Macro focus on: {file_path}",
            f"{'─' * 50}",
        ]
        
        if auto_budget:
            lines.append(f"Auto-detected budget: {max_tokens:,} tokens available")
        else:
            lines.append(f"Token budget: {max_tokens:,}")
        lines.append("")
        
        if added:
            lines.append(f"ADDED ({len(added)} files):")
            for f in added[:15]:  # Show first 15
                lines.append(_format_file_info(f, indent=1))
            if len(added) > 15:
                lines.append(f"  ... and {len(added) - 15} more")
            lines.append("")
        
        if skipped:
            lines.append(f"SKIPPED ({len(skipped)}):")
            for s in skipped[:5]:
                lines.append(f"  {s}")
            if len(skipped) > 5:
                lines.append(f"  ... and {len(skipped) - 5} more")
            lines.append("")
        
        lines.extend([
            f"{'─' * 50}",
            f"TOTALS: {len(files_to_focus)} files, {total_lines:,} lines, {total_tokens:,} tokens",
            f"Budget used: {total_tokens:,} / {max_tokens:,} ({total_tokens * 100 // max_tokens}%)" if max_tokens > 0 else "",
            f"Currently focused: {len(focused)} file(s)"
        ])
        
        return "\n".join(lines)
    
    except Exception as e:
        import traceback
        return f"Error focusing dependencies: {e}\n{traceback.format_exc()}"


def add_entry_point(file_path: str, label: Optional[str] = None) -> str:
    """Add a file as a named entry point for dependency tracing.
    
    Entry points are used to trace which files are connected to your main
    scripts. Files not reachable from any entry point are considered orphans.
    
    Args:
        file_path: Relative path to the entry point file
        label: Human-readable label (defaults to filename)
    
    Returns:
        Confirmation message
    """
    try:
        # Verify file exists using filesystem abstraction
        fs = _get_fs()
        
        if not fs.exists(file_path):
            return f"Error: File not found: {file_path}"
        
        # Get existing entry points
        entry_points = _get_entry_points()
        
        # Check if already exists
        for ep in entry_points:
            if ep["path"] == file_path:
                return f"Entry point already exists: {file_path} ({ep['label']})"
        
        # Add new entry point
        if label is None:
            label = Path(file_path).stem
        
        entry_points.append({
            "path": file_path,
            "label": label,
            "enabled": True
        })
        
        _set_entry_points(entry_points)
        
        return f"✓ Added entry point: {file_path} ({label})\nTotal entry points: {len(entry_points)}"
    
    except Exception as e:
        return f"Error adding entry point: {e}"


def remove_entry_point(file_path: str) -> str:
    """Remove a file from the entry points list.
    
    Args:
        file_path: Relative path to the entry point to remove
    
    Returns:
        Confirmation message
    """
    try:
        entry_points = _get_entry_points()
        
        # Find and remove
        original_len = len(entry_points)
        entry_points = [ep for ep in entry_points if ep["path"] != file_path]
        
        if len(entry_points) == original_len:
            return f"Entry point not found: {file_path}"
        
        _set_entry_points(entry_points)
        
        return f"✓ Removed entry point: {file_path}\nRemaining entry points: {len(entry_points)}"
    
    except Exception as e:
        return f"Error removing entry point: {e}"


def list_entry_points() -> str:
    """List all configured entry points.
    
    Returns:
        List of entry points with their labels and status
    """
    try:
        entry_points = _get_entry_points()
        
        if not entry_points:
            return "No entry points configured.\nUse find_entry_points() to discover potential entry points, then add_entry_point() to add them."
        
        lines = [f"Configured entry points ({len(entry_points)}):"]
        for i, ep in enumerate(entry_points, 1):
            status = "✓" if ep.get("enabled", True) else "○"
            lines.append(f"  {status} {i}. {ep['path']} ({ep['label']})")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error listing entry points: {e}"


def trace_entry_point(entry_point_path: str) -> str:
    """Trace all files connected to an entry point.
    
    Performs a breadth-first traversal from the entry point, following all
    imports to build a complete picture of connected files.
    
    Args:
        entry_point_path: Relative path to the entry point file
    
    Returns:
        Summary of connected files with connection paths
    """
    try:
        session = _get_prism_session()
        result = session.trace_from_entry_point(entry_point_path)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        connected = result["connected_files"]
        total_lines = sum(f.get("lines", 0) for f in connected)
        total_tokens = sum(f.get("tokens", 0) for f in connected)
        
        # Group by type
        by_type: Dict[str, List] = {}
        for f in connected:
            ftype = f.get("type", "unknown")
            if ftype not in by_type:
                by_type[ftype] = []
            by_type[ftype].append(f)
        
        lines = [
            f"Trace from: {entry_point_path}",
            f"{'─' * 50}",
            f"Connected: {len(connected)} files, {total_lines} lines, {total_tokens} tokens",
            f""
        ]
        
        for ftype, files in sorted(by_type.items()):
            lines.append(f"{ftype.upper()} ({len(files)}):")
            for f in files[:10]:  # Show first 10 of each type
                lines.append(_format_file_info(f, indent=1))
            if len(files) > 10:
                lines.append(f"  ... and {len(files) - 10} more")
            lines.append("")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error tracing entry point: {e}"


def rescan_project() -> str:
    """Rescan the project to pick up new files or changes.
    
    Call this if you've added new files or significantly restructured
    the project since the last scan.
    
    Returns:
        Scan statistics
    """
    try:
        global _session, _remote_session, _remote_session_project_id
        
        # Check if SSH project
        project = _get_current_project()
        
        if project and project.type == 'ssh':
            from prism.remote_session import RemotePrismSession
            _remote_session = RemotePrismSession(project)
            stats = _remote_session.scan(force=True)
            _remote_session_project_id = project.id
        else:
            from prism.session import PrismSession
            cwd = Path.cwd().resolve()
            _session = PrismSession(cwd)
            stats = _session.scan()
        
        lines = [
            "✓ Project rescanned",
            f"{'─' * 50}",
            f"Total files: {stats['total_files']}",
            f"Packages: {', '.join(stats['project_packages']) or 'none'}",
        ]
        
        if stats.get("template_folder"):
            lines.append(f"Templates: {stats['template_folder']}")
        if stats.get("static_folder"):
            lines.append(f"Static: {stats['static_folder']}")
        
        lines.append("")
        lines.append("By type:")
        for ntype, count in stats.get("node_types", {}).items():
            lines.append(f"  {ntype}: {count}")
        
        return "\n".join(lines)
    
    except Exception as e:
        return f"Error rescanning project: {e}"
