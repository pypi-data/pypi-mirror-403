from pathlib import Path
from .history import get_histories_dir

# Lazy import to avoid circular dependencies
_file_tree_module = None

def get_file_tree_for_project():
    """Get file tree string for the current project (local or remote)."""
    global _file_tree_module
    if _file_tree_module is None:
        from HUD import file_tree as ft
        _file_tree_module = ft
    return _file_tree_module.get_file_tree_for_project()

def get_history_path(session_id: str) -> Path:
    """Get the path for a history file."""
    # Strip any existing .gt suffix to prevent doubling
    if session_id.endswith(".gt"):
        session_id = session_id[:-3]
    return get_histories_dir() / f"{session_id}.gt.json"
