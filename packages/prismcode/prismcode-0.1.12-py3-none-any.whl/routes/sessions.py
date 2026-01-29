"""
Session management routes.
"""
import uuid
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify, render_template, session as flask_session

from core.agent import Agent
from core.history import list_sessions
from config import SLASH_COMMANDS, get_agent_config
from settings import Settings

from .shared import (
    get_agent, get_store, get_client_tabs, set_client_tabs,
    get_current_tab, set_current_tab, build_rich_history,
    generate_title_async, active_agents, active_processing,
    _get_config, get_socketio
)

sessions_bp = Blueprint('sessions', __name__)
_store = get_store()


def get_available_slash_commands():
    """Get all available slash commands with descriptions."""
    commands = []
    for cmd, desc in SLASH_COMMANDS:
        commands.append({"command": cmd, "description": desc})

    commands.extend([
        {"command": "/new", "description": "Start new session"},
        {"command": "/load <session_id>", "description": "Load a session"},
        {"command": "/sessions", "description": "List recent sessions"},
        {"command": "/toggle-diff", "description": "Toggle detailed diff display"},
        {"command": "/help", "description": "Show help"},
    ])

    return commands


@sessions_bp.route('/')
def index():
    """Main interface - redirects to workspace."""
    return workspace()


@sessions_bp.route('/workspace')
def workspace():
    """New modular workspace UI."""
    get_agent()  # Ensure agent is initialized
    return render_template('workspace.html')


@sessions_bp.route('/api/sessions')
def api_sessions():
    """Get list of available sessions, optionally filtered by project."""
    project_id = request.args.get('project_id')
    sessions = list_sessions()

    if project_id:
        filtered = []
        for s in sessions:
            session_project = _store.get('session', s['id'], 'project_id')
            if session_project == project_id:
                filtered.append(s)
        sessions = filtered

    try:
        current_id = get_agent().history.session_id
    except Exception as e:
        print(f"Warning: Failed to get current agent: {e}")
        current_id = None

    return jsonify({
        "sessions": sessions,
        "current": current_id
    })


@sessions_bp.route('/api/current-session')
def api_current_session():
    """Get current session info and history (for page load)."""
    from core.project_manager import SessionIndex

    project_id = request.args.get('project_id')
    agent = get_agent()
    session_id = agent.history.session_id

    if project_id:
        idx = SessionIndex()
        session_info = idx.get_session_info(session_id)
        current_project = session_info.get('current_project_id') if session_info else None

        if not current_project and agent.project:
            current_project = agent.project.id

        if current_project and current_project != project_id:
            return jsonify({
                "error": "Session belongs to different project",
                "session_id": None,
                "project_mismatch": True
            }), 409

    title = agent.history_manager.metadata.get('title') if hasattr(agent, 'history_manager') else None
    history = build_rich_history(agent)

    return jsonify({
        "session_id": session_id,
        "title": title,
        "history": history,
        "message_count": len(history),
        "project_id": agent.project.id if agent.project else "local",
        "processing": session_id in active_processing
    })


@sessions_bp.route('/api/load-session', methods=['POST'])
def api_load_session():
    """Load a specific session."""
    from core.project_manager import SessionIndex, ProjectManager

    data = request.json
    session_id = data.get('session_id')
    target_project_id = data.get('project_id')

    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400

    try:
        client_id = flask_session['client_id']

        if target_project_id:
            idx = SessionIndex()
            info = idx.get_session_info(session_id)
            if info:
                current_project = info.get('current_project_id')
                if current_project and current_project != target_project_id:
                    return jsonify({
                        "error": f"Session belongs to project {current_project}",
                        "project_mismatch": True
                    }), 409

        agent = None
        if client_id in active_agents and session_id in active_agents[client_id]:
            agent = active_agents[client_id][session_id]
        else:
            idx = SessionIndex()
            info = idx.get_session_info(session_id)
            project = None
            if info and info.get('current_project_id'):
                pm = ProjectManager()
                project = pm.get(info.get('current_project_id'))

            if not project:
                pm = ProjectManager()
                project = pm.get_default()

            agent = Agent(
                system_prompt=_get_config()["system_prompt"],
                tools=_get_config()["tools"],
                model=_get_config()["model"],
                session_id=session_id,
                project=project,
                litellm_params=_get_config().get("litellm_params", {}),
            )

            if client_id not in active_agents:
                active_agents[client_id] = {}
            active_agents[client_id][session_id] = agent

        set_current_tab(client_id, session_id)

        title = agent.history_manager.metadata.get('title') if hasattr(agent, 'history_manager') else None
        msg_count = len(agent.history_manager.working.entries) if hasattr(agent, 'history_manager') and agent.history_manager else len(agent.history.messages)

        if not title and msg_count >= 2:
            socketio = get_socketio()
            if socketio:
                thread = threading.Thread(target=generate_title_async, args=(agent, socketio))
                thread.daemon = True
                thread.start()

        history = build_rich_history(agent)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "title": title,
            "history": history,
            "message_count": msg_count,
            "project_id": agent.project.id if agent.project else "local",
            "processing": session_id in active_processing
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@sessions_bp.route('/api/new-session', methods=['POST'])
def api_new_session():
    """Create a new session."""
    from core.project_manager import ProjectManager, SessionIndex

    data = request.json or {}
    project_id = data.get('project_id')
    client_id = flask_session.get('client_id')
    if not client_id:
        client_id = str(uuid.uuid4())
        flask_session['client_id'] = client_id

    pm = ProjectManager()
    project = None
    if project_id:
        project = pm.get(project_id)
        if not project:
            return jsonify({"error": f"Project not found: {project_id}"}), 404
    else:
        project = pm.get_default()
        project_id = project.id

    agent = Agent(
        system_prompt=_get_config()["system_prompt"],
        tools=_get_config()["tools"],
        model=_get_config()["model"],
        project=project,
        litellm_params=_get_config().get("litellm_params", {}),
    )

    session_id = agent.history.session_id

    idx = SessionIndex()
    idx.set_session_project(session_id, project_id, is_original=True)

    if client_id not in active_agents:
        active_agents[client_id] = {}
    active_agents[client_id][session_id] = agent

    tabs = get_client_tabs(client_id)
    tabs.append(session_id)
    set_client_tabs(client_id, tabs)
    set_current_tab(client_id, session_id)

    return jsonify({
        "success": True,
        "session_id": session_id,
        "project_id": project_id
    })


@sessions_bp.route('/api/toggle-diff', methods=['POST'])
def api_toggle_diff():
    """Toggle diff display setting."""
    settings = Settings()
    settings.show_diff = not settings.show_diff
    settings.save()

    return jsonify({
        "success": True,
        "show_diff": settings.show_diff
    })


@sessions_bp.route('/api/context-stats')
def api_context_stats():
    """Get token usage breakdown for context visualization."""
    from core.context_management import ModelProfile

    session_id = request.args.get('session_id')

    client_id = flask_session.get('client_id')
    if client_id and client_id in active_agents:
        if session_id and session_id in active_agents[client_id]:
            agent = active_agents[client_id][session_id]
            stats = agent.get_context_stats()
            return jsonify(stats)

    config = _get_config()
    model_name = config["model"]

    try:
        profile = ModelProfile.from_model_string(model_name)
        budget = profile.context_window
        threshold = int(budget * 0.7)
        model_display = profile.name
    except:
        budget = 128000
        threshold = 89600
        model_display = model_name

    return jsonify({
        "system": 0,
        "history": 0,
        "gists": 0,
        "gist_count": 0,
        "focus": 0,
        "focus_count": 0,
        "tree": 0,
        "total": 0,
        "budget": budget,
        "threshold": threshold,
        "model": model_display,
        "context_window": budget,
        "cached": False
    })


@sessions_bp.route('/api/folders')
def api_folders():
    """Get folder contents for browsing."""
    import os

    path = request.args.get('path', '~')

    if path.startswith('~'):
        path = os.path.expanduser(path)

    path = os.path.abspath(path)

    if os.path.isfile(path):
        path = os.path.dirname(path)

    while not os.path.exists(path) and path != '/':
        path = os.path.dirname(path)

    contents = []
    try:
        entries = os.listdir(path)
        for name in sorted(entries):
            if name.startswith('.'):
                continue

            full_path = os.path.join(path, name)
            is_dir = os.path.isdir(full_path)

            if is_dir:
                contents.append({
                    'name': name,
                    'path': full_path,
                    'is_dir': True
                })
    except PermissionError:
        pass
    except Exception as e:
        print(f"Error listing directory {path}: {e}")

    import os
    return jsonify({
        'path': path,
        'contents': contents,
        'home_dir': os.path.expanduser('~')
    })


@sessions_bp.route('/api/focused-files')
def api_focused_files():
    """Get list of focused files for current session with line counts."""
    from core.project_manager import ProjectManager, SessionIndex
    from core.filesystem import LocalFileSystem

    session_id = request.args.get('session_id')

    if not session_id:
        client_id = flask_session.get('client_id')
        if client_id:
            session_id = get_current_tab(client_id)

    if not session_id:
        return jsonify({"files": [], "count": 0, "session_id": None})

    files = list(_store.get('focus', session_id, 'files', default=[]))

    idx = SessionIndex()
    pm = ProjectManager()

    session_info = idx.get_session_info(session_id)
    project_id = session_info.get('current_project_id') if session_info else None
    project = pm.get(project_id) if project_id else None

    if project:
        fs = project.get_filesystem()
        project_root = project.path
    else:
        fs = LocalFileSystem(Path.cwd())
        project_root = str(Path.cwd())

    file_info = []
    for f in files:
        if f.startswith(project_root):
            display_path = f[len(project_root):].lstrip('/')
        else:
            display_path = f

        try:
            content = fs.read(f)
            line_count = content.count('\n') + (1 if content and not content.endswith('\n') else 0)
        except:
            line_count = 0

        file_info.append({
            "path": display_path,
            "lines": line_count
        })

    return jsonify({
        "files": file_info,
        "count": len(files),
        "session_id": session_id
    })
