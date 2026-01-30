"""Configuration management for Prism."""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Config file location
CONFIG_FILE = Path(__file__).parent.parent / "zdeps2" / "zdeps2_config.json"

DEFAULT_GLOBAL_SETTINGS: Dict[str, Any] = {
    "exclude_patterns": [
        ".venv",
        ".local",
        ".git",
        ".cache",
        "__pycache__",
        "node_modules",
        "site-packages",
        ".tox",
        ".eggs",
        "build",
        "dist",
        "__MACOSX",
    ],
    "exclude_files": ["__init__.py"],
    "available_colors": [
        {"id": "blue", "emoji": "🔵", "hex": "#58a6ff", "name": "Blue"},
        {"id": "yellow", "emoji": "🟡", "hex": "#d29922", "name": "Yellow"},
        {"id": "green", "emoji": "🟢", "hex": "#3fb950", "name": "Green"},
        {"id": "purple", "emoji": "🟣", "hex": "#a78bfa", "name": "Purple"},
        {"id": "orange", "emoji": "🟠", "hex": "#f0883e", "name": "Orange"},
        {"id": "red", "emoji": "🔴", "hex": "#f85149", "name": "Red"},
        {"id": "brown", "emoji": "🟤", "hex": "#a87058", "name": "Brown"},
    ],
}

_config_cache: Optional[Dict[str, Any]] = None


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return CONFIG_FILE


def _migrate_old_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate old config format to new multi-project format."""
    if "projects" in old_config:
        return old_config

    project_root = old_config.get("project_root", str(Path.home()))
    old_entry_points = old_config.get("entry_points", [])

    migrated_entry_points = []
    for ep in old_entry_points:
        migrated_ep = {
            "path": ep.get("path", ""),
            "label": ep.get("label", ""),
            "color": ep.get("color", "#58a6ff"),
            "emoji": ep.get("emoji", "🔵"),
            "enabled": ep.get("enabled", True),
        }
        migrated_entry_points.append(migrated_ep)

    new_config = {
        "current_project": project_root,
        "recent_projects": [project_root] if project_root else [],
        "projects": {project_root: {"entry_points": migrated_entry_points}}
        if project_root
        else {},
        "exclude_patterns": old_config.get(
            "exclude_patterns", DEFAULT_GLOBAL_SETTINGS["exclude_patterns"]
        ),
        "exclude_files": old_config.get(
            "exclude_files", DEFAULT_GLOBAL_SETTINGS["exclude_files"]
        ),
        "available_colors": old_config.get(
            "available_colors", DEFAULT_GLOBAL_SETTINGS["available_colors"]
        ),
    }

    return new_config


def _ensure_project_exists(config: Dict[str, Any], project_root: str) -> None:
    """Ensure a project exists in the config."""
    if "projects" not in config:
        config["projects"] = {}
    if project_root not in config["projects"]:
        config["projects"][project_root] = {
            "entry_points": [],
            "excluded_submodules": None,
        }


def _add_to_recent_projects(
    config: Dict[str, Any], project_root: str, max_recent: int = 10
) -> None:
    """Add a project to the recent projects list."""
    if "recent_projects" not in config:
        config["recent_projects"] = []

    if project_root in config["recent_projects"]:
        config["recent_projects"].remove(project_root)

    config["recent_projects"].insert(0, project_root)
    config["recent_projects"] = config["recent_projects"][:max_recent]


def load_raw_config() -> Dict[str, Any]:
    """Load the raw configuration from disk."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                config = _migrate_old_config(config)
                for key, value in DEFAULT_GLOBAL_SETTINGS.items():
                    if key not in config:
                        config[key] = value
                _config_cache = config
                return config
        except (json.JSONDecodeError, IOError):
            pass

    default_project = str(Path(__file__).parent.parent.parent)
    default_config = {
        "current_project": default_project,
        "recent_projects": [default_project],
        "projects": {default_project: {"entry_points": []}},
        **DEFAULT_GLOBAL_SETTINGS,
    }
    save_raw_config(default_config)
    _config_cache = default_config
    return _config_cache


def save_raw_config(config: Dict[str, Any]) -> None:
    """Save the raw configuration to disk."""
    global _config_cache
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    _config_cache = config


def load_config() -> Dict[str, Any]:
    """Load configuration for the current project."""
    raw_config = load_raw_config()
    current_project = raw_config.get("current_project", "")

    project_data = raw_config.get("projects", {}).get(current_project, {})
    entry_points = project_data.get("entry_points", [])
    excluded_submodules = project_data.get("excluded_submodules", None)

    return {
        "project_root": current_project,
        "entry_points": entry_points,
        "excluded_submodules": excluded_submodules,
        "exclude_patterns": raw_config.get(
            "exclude_patterns", DEFAULT_GLOBAL_SETTINGS["exclude_patterns"]
        ),
        "exclude_files": raw_config.get(
            "exclude_files", DEFAULT_GLOBAL_SETTINGS["exclude_files"]
        ),
        "available_colors": raw_config.get(
            "available_colors", DEFAULT_GLOBAL_SETTINGS["available_colors"]
        ),
    }


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration for the current project."""
    raw_config = load_raw_config()

    if "project_root" in config:
        project_root = config["project_root"]
        raw_config["current_project"] = project_root
        _ensure_project_exists(raw_config, project_root)
        _add_to_recent_projects(raw_config, project_root)

    current_project = raw_config.get("current_project", "")

    if "entry_points" in config and current_project:
        _ensure_project_exists(raw_config, current_project)
        raw_config["projects"][current_project]["entry_points"] = config["entry_points"]

    for key in ["exclude_patterns", "exclude_files", "available_colors"]:
        if key in config:
            raw_config[key] = config[key]

    save_raw_config(raw_config)


def reload_config() -> Dict[str, Any]:
    """Reload configuration from disk."""
    global _config_cache
    _config_cache = None
    return load_config()


def get_project_root() -> Path:
    """Get the current project root directory."""
    config = load_config()
    return Path(config["project_root"])


def get_recent_projects() -> List[str]:
    """Get list of recent project paths."""
    raw_config = load_raw_config()
    return raw_config.get("recent_projects", [])


def get_project_entry_points(project_root: str) -> List[Dict[str, Any]]:
    """Get entry points for a specific project."""
    raw_config = load_raw_config()
    project_data = raw_config.get("projects", {}).get(project_root, {})
    return project_data.get("entry_points", [])


def set_project_entry_points(
    project_root: str, entry_points: List[Dict[str, Any]]
) -> None:
    """Set entry points for a specific project."""
    raw_config = load_raw_config()
    _ensure_project_exists(raw_config, project_root)
    raw_config["projects"][project_root]["entry_points"] = entry_points
    save_raw_config(raw_config)


def switch_project(project_root: str) -> Dict[str, Any]:
    """Switch to a different project."""
    raw_config = load_raw_config()
    raw_config["current_project"] = project_root
    _ensure_project_exists(raw_config, project_root)
    _add_to_recent_projects(raw_config, project_root)
    save_raw_config(raw_config)
    return load_config()


def add_entry_point(entry_point: Dict[str, Any]) -> None:
    """Add an entry point to the current project."""
    config = load_config()
    entry_points = config["entry_points"]

    for ep in entry_points:
        if ep["path"] == entry_point["path"]:
            return

    if "enabled" not in entry_point:
        entry_point["enabled"] = True

    entry_points.append(entry_point)
    save_config({"entry_points": entry_points})


def remove_entry_point(path: str) -> None:
    """Remove an entry point from the current project."""
    config = load_config()
    entry_points = [ep for ep in config["entry_points"] if ep["path"] != path]
    save_config({"entry_points": entry_points})


def toggle_entry_point(path: str) -> bool:
    """Toggle an entry point on/off."""
    config = load_config()
    entry_points = config["entry_points"]

    new_state = False
    for ep in entry_points:
        if ep["path"] == path:
            ep["enabled"] = not ep.get("enabled", True)
            new_state = ep["enabled"]
            break

    save_config({"entry_points": entry_points})
    return new_state


def get_enabled_entry_points() -> List[Dict[str, Any]]:
    """Get only enabled entry points."""
    config = load_config()
    return [ep for ep in config["entry_points"] if ep.get("enabled", True)]


def get_excluded_submodules() -> Optional[List[str]]:
    """Get list of excluded git submodules."""
    config = load_config()
    return config.get("excluded_submodules", None)


def set_excluded_submodules(excluded: Optional[List[str]]) -> None:
    """Set list of excluded git submodules."""
    raw_config = load_raw_config()
    current_project = raw_config.get("current_project", "")
    if current_project:
        _ensure_project_exists(raw_config, current_project)
        raw_config["projects"][current_project]["excluded_submodules"] = excluded
        save_raw_config(raw_config)


def toggle_submodule(submodule_path: str, all_submodules: List[str]) -> bool:
    """Toggle a git submodule's inclusion status."""
    raw_config = load_raw_config()
    current_project = raw_config.get("current_project", "")
    if not current_project:
        return False

    _ensure_project_exists(raw_config, current_project)
    project_data = raw_config["projects"][current_project]
    excluded = project_data.get("excluded_submodules", None)

    if excluded is None:
        excluded = list(all_submodules)

    if submodule_path in excluded:
        excluded.remove(submodule_path)
        now_included = True
    else:
        excluded.append(submodule_path)
        now_included = False

    project_data["excluded_submodules"] = excluded
    save_raw_config(raw_config)
    return now_included
