"""
Project management routes.
"""
import os
import re
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, session as flask_session

from core.agent import Agent
from core.project import Project
from core.project_manager import ProjectManager, SessionIndex
from core.filesystem import set_current_project, clear_filesystem_cache

from .shared import (
    get_agent, get_store, get_client_tabs, set_client_tabs,
    set_current_tab, active_agents, _get_config
)

projects_bp = Blueprint('projects', __name__)
_store = get_store()


@projects_bp.route('/api/projects')
def api_projects():
    """Get list of configured projects."""
    pm = ProjectManager()
    agent = get_agent()

    default_project = pm.get_default()
    default_id = default_project.id if default_project else "local"

    projects = []
    for p in pm.list():
        projects.append({
            "id": p.id,
            "name": p.name,
            "type": p.type,
            "color": p.color,
            "path": p.path,
            "host": p.host if p.type == "ssh" else None,
            "user": p.user if p.type == "ssh" else None,
            "port": p.port if p.type == "ssh" else None,
            "favorite": getattr(p, 'favorite', False),
            "last_accessed": getattr(p, 'last_accessed', None),
            "notifications": getattr(p, 'notifications', 0),
            "is_default": p.id == default_id,
        })

    ssh_profiles = pm.list_ssh_profiles() if hasattr(pm, 'list_ssh_profiles') else []

    return jsonify({
        "projects": projects,
        "current": agent.project.id if agent.project else "local",
        "default": default_id,
        "ssh_profiles": ssh_profiles,
        "home_dir": os.path.expanduser('~')
    })


@projects_bp.route('/api/projects', methods=['POST'])
def api_create_project():
    """Create or update a project."""
    data = request.json
    pm = ProjectManager()

    name = data.get('name', '').strip()
    path = data.get('path', '').strip()
    project_type = data.get('type', 'local')

    if not name:
        return jsonify({"error": "Project name is required"}), 400
    if not path:
        return jsonify({"error": "Project path is required"}), 400

    project_id = data.get('id')
    if not project_id:
        project_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        base_id = project_id
        counter = 1
        while pm.get(project_id):
            project_id = f"{base_id}-{counter}"
            counter += 1

    project_data = {
        'id': project_id,
        'name': name,
        'type': project_type,
        'path': path,
        'color': data.get('color', '#ff6b2b'),
    }

    if project_type == 'ssh':
        host = data.get('host', '').strip()
        user = data.get('user', '').strip()

        if not host:
            return jsonify({"error": "SSH host is required"}), 400
        if not user:
            return jsonify({"error": "SSH username is required"}), 400

        project_data['host'] = host
        project_data['user'] = user
        project_data['port'] = int(data.get('port', 22))

    try:
        project = Project.from_dict(project_data)

        existing = pm.get(project_id)
        if existing:
            pm.update(project)
        else:
            pm.add(project)

        if data.get('save_profile') and project_type == 'ssh':
            pm.save_ssh_profile({
                'name': name,
                'host': project_data['host'],
                'user': project_data['user'],
                'port': project_data['port'],
                'key_path': data.get('key_path', ''),
            })

        return jsonify({
            "success": True,
            "project": project.to_dict()
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create project: {e}"}), 500


@projects_bp.route('/api/projects/<project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    """Delete a project."""
    pm = ProjectManager()

    try:
        if pm.remove(project_id):
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Project not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to delete project: {e}"}), 500


@projects_bp.route('/api/projects/<project_id>/set-default', methods=['POST'])
def api_set_default_project(project_id):
    """Set a project as the default."""
    pm = ProjectManager()

    try:
        pm.set_default(project_id)
        return jsonify({"success": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to set default: {e}"}), 500


@projects_bp.route('/api/projects/<project_id>', methods=['PATCH'])
def api_update_project(project_id):
    """Update a project's editable fields (name, color, favorite)."""
    pm = ProjectManager()
    project = pm.get(project_id)

    if not project:
        return jsonify({"error": "Project not found"}), 404

    data = request.json

    if 'name' in data:
        project.name = data['name'].strip()
    if 'color' in data:
        project.color = data['color']
    if 'favorite' in data:
        if data['favorite'] and not project.favorite:
            current_favorites = sum(1 for p in pm.list() if getattr(p, 'favorite', False))
            if current_favorites >= 5:
                return jsonify({"error": "Maximum 5 favorites allowed"}), 400
        project.favorite = bool(data['favorite'])
    if 'notifications' in data:
        project.notifications = int(data['notifications'])

    try:
        pm.update(project)
        return jsonify({
            "success": True,
            "project": project.to_dict()
        })
    except Exception as e:
        return jsonify({"error": f"Failed to update project: {e}"}), 500


@projects_bp.route('/api/projects/switch', methods=['POST'])
def api_switch_project():
    """Switch current session to a different project."""
    data = request.json
    project_id = data.get('project_id')
    session_id = data.get('session_id')

    if not project_id:
        return jsonify({"error": "No project_id provided"}), 400

    pm = ProjectManager()
    project = pm.get(project_id)

    if not project:
        return jsonify({"error": f"Project not found: {project_id}"}), 404

    agent = get_agent(session_id)
    agent.project = project

    effective_session_id = session_id or agent.history.session_id
    set_current_project(effective_session_id, project_id)
    clear_filesystem_cache()

    return jsonify({
        "success": True,
        "project": {
            "id": project.id,
            "name": project.name,
            "type": project.type,
            "color": project.color,
            "path": project.path,
        }
    })


@projects_bp.route('/api/projects/<project_id>/sessions')
def api_project_sessions(project_id):
    """Get sessions for a specific project."""
    from core.history import list_sessions

    sessions = list_sessions()

    project_sessions = []
    for s in sessions:
        session_project = _store.get('session', s['id'], 'project_id')
        if session_project == project_id:
            project_sessions.append(s)

    most_recent = project_sessions[0] if project_sessions else None

    return jsonify({
        "sessions": project_sessions,
        "most_recent": most_recent['id'] if most_recent else None,
        "count": len(project_sessions)
    })


@projects_bp.route('/api/projects/<project_id>/new-session', methods=['POST'])
def api_project_new_session(project_id):
    """Create a new session for a specific project."""
    pm = ProjectManager()
    project = pm.get(project_id)

    if not project:
        return jsonify({"error": f"Project not found: {project_id}"}), 404

    client_id = flask_session.get('client_id')
    if not client_id:
        client_id = str(uuid.uuid4())
        flask_session['client_id'] = client_id

    agent = Agent(
        system_prompt=_get_config()["system_prompt"],
        tools=_get_config()["tools"],
        model=_get_config()["model"],
        litellm_params=_get_config().get("litellm_params", {}),
    )
    agent.project = project

    if client_id not in active_agents:
        active_agents[client_id] = {}
    active_agents[client_id][agent.history.session_id] = agent

    session_id = agent.history.session_id
    set_current_project(session_id, project_id)

    tabs = get_client_tabs(client_id)
    tabs.append(session_id)
    set_client_tabs(client_id, tabs)
    set_current_tab(client_id, session_id)

    return jsonify({
        "success": True,
        "session_id": session_id,
        "project_id": project_id
    })
