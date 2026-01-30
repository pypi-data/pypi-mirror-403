"""Flask API routes using Prism backend.

This is a drop-in replacement for routes.py that uses the new Prism architecture.
"""
import os
from pathlib import Path
from flask import Blueprint, jsonify, request, render_template, Response, stream_with_context

# Import Prism components
from prism.adapter import (
    get_session_manager,
    run_full_analysis_prism,
    suggest_entry_points_prism,
    generate_snapshot_prism,
    get_children_preview_prism,
    get_frontend_preview_prism,
    get_full_dependency_info_prism,
)

# Prism config management
from prism.config import (
    load_config,
    save_config,
    get_project_root,
    reload_config,
    toggle_entry_point,
    switch_project,
    get_recent_projects,
    get_enabled_entry_points,
    get_excluded_submodules,
    toggle_submodule,
)

# Prism scanner for git submodules
from prism.scanner import get_git_submodules

api = Blueprint("api", __name__)


@api.route("/")
def index():
    return render_template("index.html")


@api.route("/api/data")
def get_data():
    """Get analysis data for the current project."""
    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    # Get or create session
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    session = manager.get_current_session()

    # Check if we need to scan
    if not session._is_scanned:
        result = run_full_analysis_prism(str(project_root), entry_points)
    else:
        # Use existing scan
        from prism.adapter import build_analysis_result_compat
        stats = session.get_stats()
        result = build_analysis_result_compat(session, entry_points, stats)

    return jsonify(result)


@api.route("/api/refresh")
def refresh_data():
    """Refresh analysis by re-scanning the project."""
    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    reload_config()

    # Invalidate and re-scan
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    manager.invalidate_current()

    run_full_analysis_prism(str(project_root), entry_points)

    return jsonify({"status": "refreshed"})


@api.route("/api/entry-points", methods=["POST"])
def add_entry_point():
    """Add a new entry point."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    config = load_config()

    for ep in config["entry_points"]:
        if ep["path"] == data["path"]:
            return jsonify({"error": "Entry point already exists"}), 400

    config["entry_points"].append({
        "path": data["path"],
        "label": data["label"],
        "color": data["color"],
        "emoji": data.get("emoji", "🔵"),
        "enabled": True,
    })

    save_config(config)

    # Invalidate to force re-analysis with new entry point
    manager = get_session_manager()
    manager.invalidate_current()

    return jsonify({"status": "added"})


@api.route("/api/entry-points", methods=["DELETE"])
def remove_entry_point():
    """Remove an entry point."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    config = load_config()
    config["entry_points"] = [
        ep for ep in config["entry_points"] if ep["path"] != data["path"]
    ]

    save_config(config)

    # Invalidate cache
    manager = get_session_manager()
    manager.invalidate_current()

    return jsonify({"status": "removed"})


@api.route("/api/entry-points/toggle", methods=["POST"])
def toggle_entry_point_route():
    """Toggle an entry point on/off."""
    data = request.json
    if not data or "path" not in data:
        return jsonify({"error": "No path provided"}), 400

    new_state = toggle_entry_point(data["path"])

    # Invalidate cache
    manager = get_session_manager()
    manager.invalidate_current()

    return jsonify({"status": "toggled", "enabled": new_state})


@api.route("/api/config")
def get_config():
    """Get current configuration."""
    return jsonify(load_config())


@api.route("/api/copy-snapshot", methods=["POST"])
def copy_snapshot():
    """Generate a dependency snapshot."""
    data = request.json
    if not data or "path" not in data:
        return jsonify({"error": "No file path provided"}), 400

    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    # Get session
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    session = manager.get_current_session()

    # Ensure scanned
    if not session._is_scanned:
        run_full_analysis_prism(str(project_root), entry_points)
        session = manager.get_current_session()

    # Build options
    options = {
        "parent_depth": data.get("parent_depth", 1),
        "include_chain": data.get("include_chain", False),
        "chain_length": data.get("chain_length"),
        "child_depth": data.get("child_depth", 0),
        "child_max_tokens": data.get("child_max_tokens", 0),
        "excluded_children": set(data.get("excluded_children", [])),
        "include_frontend": data.get("include_frontend", False),
        "excluded_frontend": set(data.get("excluded_frontend", [])),
        "extra_files": set(data.get("extra_files", [])),
    }

    result = generate_snapshot_prism(session, data["path"], options, entry_points)

    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)


@api.route("/api/preview-children", methods=["POST"])
def preview_children():
    """Preview children of a file."""
    data = request.json
    if not data or "path" not in data:
        return jsonify({"error": "No file path provided"}), 400

    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    # Get session
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    session = manager.get_current_session()

    # Ensure scanned
    if not session._is_scanned:
        run_full_analysis_prism(str(project_root), entry_points)
        session = manager.get_current_session()

    # Pass entry_points to get connection info for each child
    result = get_children_preview_prism(session, data["path"], entry_points)

    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)


@api.route("/api/preview-frontend", methods=["POST"])
def preview_frontend():
    """Preview front-end dependencies for a Python file."""
    data = request.json
    if not data or "path" not in data:
        return jsonify({"error": "No file path provided"}), 400

    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    # Get session
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    session = manager.get_current_session()

    # Ensure scanned
    if not session._is_scanned:
        run_full_analysis_prism(str(project_root), entry_points)
        session = manager.get_current_session()

    # Pass entry_points to get connection info for each frontend file
    result = get_frontend_preview_prism(session, data["path"], entry_points)

    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)


@api.route("/api/full-dependencies", methods=["POST"])
def full_dependencies():
    """Get full dependency info for a file."""
    data = request.json
    if not data or "path" not in data:
        return jsonify({"error": "No file path provided"}), 400

    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    # Get session
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    session = manager.get_current_session()

    # Ensure scanned
    if not session._is_scanned:
        run_full_analysis_prism(str(project_root), entry_points)
        session = manager.get_current_session()

    # Use the full dependency info adapter
    result = get_full_dependency_info_prism(session, data["path"], entry_points)

    if "error" in result:
        return jsonify(result), 404

    return jsonify(result)


@api.route("/api/project-root", methods=["POST"])
def set_project_root():
    """Set/switch project root."""
    data = request.json
    if not data or "path" not in data:
        return jsonify({"error": "No path provided"}), 400

    new_root = Path(data["path"]).expanduser().resolve()
    if not new_root.exists():
        return jsonify({"error": f"Path does not exist: {new_root}"}), 400
    if not new_root.is_dir():
        return jsonify({"error": f"Path is not a directory: {new_root}"}), 400

    switch_project(str(new_root))
    reload_config()

    # Set new project in session manager
    manager = get_session_manager()
    manager.set_current_project(str(new_root))

    # Run analysis for new project
    config = load_config()
    entry_points = config.get("entry_points", [])
    run_full_analysis_prism(str(new_root), entry_points)

    return jsonify({"status": "updated", "project_root": str(new_root)})


@api.route("/api/suggest-entry-points")
def get_suggested_entry_points():
    """Get suggested entry points."""
    top_n = request.args.get("limit", 500, type=int)
    include_tests = request.args.get("include_tests", "false").lower() == "true"

    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    # Get session
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    session = manager.get_current_session()

    # Ensure scanned
    if not session._is_scanned:
        run_full_analysis_prism(str(project_root), entry_points)
        session = manager.get_current_session()

    suggestions = suggest_entry_points_prism(session, top_n, include_tests)

    return jsonify({"suggestions": suggestions, "count": len(suggestions)})


@api.route("/api/recent-projects")
def get_recent_projects_route():
    """Get recent projects."""
    projects = get_recent_projects()
    result = []
    for project_path in projects:
        path = Path(project_path)
        result.append({
            "path": project_path,
            "name": path.name,
            "exists": path.exists(),
        })
    return jsonify({"projects": result})


@api.route("/api/browse-directory", methods=["POST"])
def browse_directory():
    """Browse filesystem directories."""
    data = request.json or {}
    target_path = data.get("path", str(Path.home()))

    path = Path(target_path).expanduser().resolve()
    if not path.exists():
        path = Path.home()
    if not path.is_dir():
        path = path.parent

    folders = []
    files_count = 0

    try:
        for item in sorted(path.iterdir(), key=lambda x: x.name.lower()):
            if item.name.startswith("."):
                continue
            if item.is_dir():
                folders.append({
                    "name": item.name,
                    "path": str(item),
                })
            else:
                files_count += 1
    except PermissionError:
        pass

    parent = str(path.parent) if path.parent != path else None

    return jsonify({
        "current": str(path),
        "parent": parent,
        "folders": folders,
        "files_count": files_count,
    })


@api.route("/api/autocomplete-path", methods=["POST"])
def autocomplete_path():
    """Autocomplete filesystem paths."""
    data = request.json or {}
    partial_path = data.get("path", "")

    if not partial_path:
        return jsonify({"suggestions": []})

    path = Path(partial_path).expanduser()

    if partial_path.endswith("/") or partial_path.endswith(os.sep):
        search_dir = path
        prefix = ""
    else:
        search_dir = path.parent
        prefix = path.name.lower()

    if not search_dir.exists():
        return jsonify({"suggestions": []})

    suggestions = []
    try:
        for item in sorted(search_dir.iterdir(), key=lambda x: x.name.lower()):
            if item.name.startswith("."):
                continue
            if item.is_dir() and item.name.lower().startswith(prefix):
                suggestions.append({
                    "name": item.name,
                    "path": str(item),
                })
                if len(suggestions) >= 10:
                    break
    except PermissionError:
        pass

    return jsonify({"suggestions": suggestions})


@api.route("/api/orphans/list")
def list_orphans():
    """List orphan files."""
    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    # Get session
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    session = manager.get_current_session()

    # Ensure scanned
    if not session._is_scanned:
        run_full_analysis_prism(str(project_root), entry_points)
        session = manager.get_current_session()

    # Get orphans using Prism
    from prism.models import EntryPoint
    ep_objects = [EntryPoint(**ep) for ep in entry_points if ep.get("enabled", True)]
    orphan_result = session.get_orphans(ep_objects)

    files = [
        {
            "path": node["relative_path"],
            "full_path": str(Path(project_root) / node["relative_path"]),
            "lines": node["lines"],
        }
        for node in orphan_result["orphans"]
    ]

    return jsonify({"files": files, "count": len(files)})


@api.route("/api/orphans/preview-delete", methods=["POST"])
def preview_orphan_delete():
    """Preview orphan deletion (files and folders)."""
    from prism.cleaner import preview_deletion
    from prism.models import EntryPoint

    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    # Get session
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    session = manager.get_current_session()

    # Ensure scanned
    if not session._is_scanned:
        run_full_analysis_prism(str(project_root), entry_points)
        session = manager.get_current_session()

    # Get orphan paths
    ep_objects = [EntryPoint(**ep) for ep in entry_points if ep.get("enabled", True)]
    orphan_result = session.get_orphans(ep_objects)
    orphan_paths = {node["relative_path"] for node in orphan_result["orphans"]}

    # Use Prism cleaner for preview
    result = preview_deletion(orphan_paths, project_root)
    return jsonify(result)


@api.route("/api/orphans/delete", methods=["POST"])
def delete_orphans_route():
    """Delete orphan files."""
    from prism.cleaner import delete_orphans
    from prism.models import EntryPoint

    data = request.json or {}
    if data.get("confirmation") != "DELETE":
        return jsonify({
            "error": "Confirmation required. Send confirmation: 'DELETE'"
        }), 400

    config = load_config()
    project_root = get_project_root()
    entry_points = config.get("entry_points", [])

    # Get session
    manager = get_session_manager()
    manager.set_current_project(str(project_root))
    session = manager.get_current_session()

    # Ensure scanned
    if not session._is_scanned:
        run_full_analysis_prism(str(project_root), entry_points)
        session = manager.get_current_session()

    # Get orphan paths
    ep_objects = [EntryPoint(**ep) for ep in entry_points if ep.get("enabled", True)]
    orphan_result = session.get_orphans(ep_objects)
    orphan_paths = {node["relative_path"] for node in orphan_result["orphans"]}

    # Delete using Prism cleaner
    result = delete_orphans(orphan_paths, project_root)

    if result["errors"]:
        result["error"] = "; ".join(result["errors"][:5])

    return jsonify(result)


@api.route("/api/submodules")
def get_submodules():
    """Get git submodules."""
    project_root = get_project_root()
    all_submodules = get_git_submodules(project_root)
    excluded = get_excluded_submodules()

    result = []
    for submodule in all_submodules:
        if excluded is None:
            is_included = False
        else:
            is_included = submodule not in excluded
        result.append({
            "path": submodule,
            "included": is_included,
        })

    return jsonify({"submodules": result, "count": len(result)})


@api.route("/api/submodules/toggle", methods=["POST"])
def toggle_submodule_route():
    """Toggle a submodule's inclusion."""
    data = request.json
    if not data or "path" not in data:
        return jsonify({"error": "No path provided"}), 400

    project_root = get_project_root()
    all_submodules = get_git_submodules(project_root)

    if data["path"] not in all_submodules:
        return jsonify({"error": "Not a valid submodule"}), 400

    now_included = toggle_submodule(data["path"], all_submodules)

    # Invalidate cache to force re-scan
    manager = get_session_manager()
    manager.invalidate_current()

    return jsonify({"status": "toggled", "included": now_included})


# ============================================================================
# Chat with Claude API
# ============================================================================

@api.route("/api/chat", methods=["POST"])
def chat_with_context():
    """Chat with Claude using the current snapshot as context."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    try:
        from llm.google_apiclaude_api import get_claude_api
    except ImportError as e:
        return jsonify({"error": f"Claude API not available: {e}"}), 500

    data = request.json or {}
    message = data.get("message", "").strip()
    snapshot_content = data.get("snapshot", "")
    chat_history = data.get("history", [])
    use_streaming = data.get("stream", True)

    if not message:
        return jsonify({"error": "No message provided"}), 400

    # System prompt
    system_prompt = """You are a helpful coding assistant analyzing a codebase.

FORMATTING RULES:
- Be concise and direct
- Use markdown for structure
- Use bullet points and headers to organize information
- NEVER create ASCII art, ASCII diagrams, or ASCII flowcharts - they don't render correctly
- For diagrams, describe the flow in words or use bullet points instead
- Use fenced code blocks (```) for any code snippets"""

    if snapshot_content:
        system_prompt += f"\n\n## Code Context\n\n{snapshot_content}"

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    if use_streaming:
        def generate():
            try:
                stream = get_claude_api(messages, max_tokens=4096, stream=True, thinking=False)
                for chunk in stream:
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: [ERROR] {str(e)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    else:
        try:
            response = get_claude_api(messages, max_tokens=4096, stream=False, thinking=False)
            return jsonify({"content": response})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
