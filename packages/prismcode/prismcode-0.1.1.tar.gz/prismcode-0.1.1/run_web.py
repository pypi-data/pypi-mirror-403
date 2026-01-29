#!/usr/bin/env python3
"""
Flask web interface for Prism agent.
Real-time streaming, session management, tool display with diffs.
"""
from flask import Flask, render_template, request, jsonify, session as flask_session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import json
import os
from datetime import datetime

from core.agent import Agent
from core.history import list_sessions, get_session_title, set_session_title
from core.signella import Signella
import litellm
import threading
from tools import read_file, create_file, edit_file, rename_file, delete_file, ls
from config import LANG_MAP, get_agent_config, SLASH_COMMANDS
from settings import Settings
from pathlib import Path

_store = Signella()

# Helper to get fresh agent config (picks up model changes without restart)
def _get_config():
    """Get fresh agent config each time (for dynamic model switching)."""
    return get_agent_config()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'prism-web-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active agents: {client_id: {session_id: Agent}}
active_agents = {}

# Store cancellation flags and queued messages per client
client_state = {}  # client_id -> {"cancelled": bool, "queued_message": str|None}

# Track which sessions are actively processing (in-memory, not persisted)
# This is the source of truth for "is agent running" - checked on page load
active_processing = set()  # Set of session_ids currently being processed

# Track open tabs per client in Signella
def get_client_tabs(client_id: str) -> list:
    """Get list of open session IDs for this client."""
    return _store.get('tabs', client_id, 'active', default=[]) or []

def set_client_tabs(client_id: str, tabs: list):
    """Set list of open session IDs for this client."""
    _store.set('tabs', client_id, 'active', tabs)

def get_current_tab(client_id: str) -> str:
    """Get currently focused session ID for this client."""
    return _store.get('tabs', client_id, 'current', default=None)

def set_current_tab(client_id: str, session_id: str):
    """Set currently focused session ID for this client."""
    _store.set('tabs', client_id, 'current', session_id)

def get_agent(session_id=None):
    """Get or create agent for a specific session.
    
    Args:
        session_id: The session to get/create agent for. If None, uses current tab.
    
    Returns:
        Agent instance for the session.
    """
    client_id = flask_session.get('client_id')
    if not client_id:
        client_id = str(uuid.uuid4())
        flask_session['client_id'] = client_id
    
    # Initialize client's agent dict if needed
    if client_id not in active_agents:
        active_agents[client_id] = {}
    
    # If no session_id provided, use current tab or load most recent
    if session_id is None:
        session_id = get_current_tab(client_id)
        if session_id is None:
            # No current tab - try to load most recent session
            sessions = list_sessions(limit=1)
            if sessions and sessions[0].get('message_count', 0) > 0:
                session_id = sessions[0]['id']
    
    # Get or create agent for this session
    if session_id is None or session_id not in active_agents[client_id]:
        # Restore project context for existing sessions
        project = None
        if session_id:
            from core.project_manager import SessionIndex, ProjectManager
            idx = SessionIndex()
            info = idx.get_session_info(session_id)
            if info and info.get('current_project_id'):
                pm = ProjectManager()
                project = pm.get(info.get('current_project_id'))

        agent = Agent(
            system_prompt=_get_config()["system_prompt"],
            tools=_get_config()["tools"],
            model=_get_config()["model"],
            session_id=session_id,
            project=project,
            litellm_params=_get_config().get("litellm_params", {}),
        )
        
        # Use the actual session_id from the agent (may be new if session_id was None)
        actual_session_id = agent.history.session_id
        active_agents[client_id][actual_session_id] = agent
        
        # Track this session as open tab
        tabs = get_client_tabs(client_id)
        if actual_session_id not in tabs:
            tabs.append(actual_session_id)
            set_client_tabs(client_id, tabs)
        
        # Set as current tab if none set
        if get_current_tab(client_id) is None:
            set_current_tab(client_id, actual_session_id)
        
        session_id = actual_session_id
    
    # Always update session:current in Signella so tools use the right session
    _store.set('session', 'current', session_id)
    
    return active_agents[client_id][session_id]

def generate_title_async(agent, socketio_instance, force=False, trigger_phase="ongoing"):
    """Generate a title for the session in the background.
    
    Args:
        agent: The agent instance
        socketio_instance: SocketIO instance for emitting updates
        force: If True, regenerate even if title exists
        trigger_phase: 'first_user', 'ongoing'
    """
    try:
        session_id = agent.history.session_id
        
        # Determine if we should generate
        existing_title = agent.history_manager.metadata.get('title') if hasattr(agent, 'history_manager') else agent.history.metadata.get('title')
        
        # If it's the very first message, always generate (unless forced off)
        should_generate = force or not existing_title
        
        # If we have a title, only regenerate periodically (e.g. every 10 messages)
        # or if the first title was just a placeholder
        if existing_title and not force:
            # Use new history manager if available, fall back to legacy
            if hasattr(agent, 'history_manager'):
                msg_count = len(agent.history_manager.working.entries)
            else:
                msg_count = len(agent.history.messages)
            # Regenerate early (msg 4) to capture context, then periodically
            if msg_count == 4 or (msg_count > 4 and msg_count % 10 == 0):
                should_generate = True
            else:
                return

        # Need at least one message
        messages = agent.history.messages
        entries = agent.history_manager.working.entries if hasattr(agent, 'history_manager') else []
        
        if not messages and not entries:
            return
        
        # Build conversation preview
        preview_parts = []
        
        # Helper to clean content
        def clean_content(text):
            if not text: return ""
            # Strip Gist markers
            if "[Conversation gist]" in text:
                text = text.replace("[Conversation gist]", "").strip()
            if "Memory Archive:" in text:
                lines = text.split('\n')
                text = '\n'.join([l for l in lines if not l.startswith("Memory Archive")])
            return text.strip()

        # Try new format first (ground truth entries)
        if entries:
            # Look at last 8 messages for context
            start_idx = max(0, len(entries) - 8)
            for entry in entries[start_idx:]:
                msg = entry.message
                role = msg.get("role")
                content = clean_content(msg.get("content", ""))
                
                if role == "user" and content:
                    preview_parts.append(f"User: {content[:300]}")
                elif role == "assistant" and content:
                    preview_parts.append(f"Assistant: {content[:300]}")
        
        # Fall back to legacy format
        if not preview_parts:
            # Look at last 8 messages
            start_idx = max(0, len(messages) - 8)
            for msg in messages[start_idx:]:
                role = msg.get("role")
                content = clean_content(msg.get("content", ""))
                if role == "user":
                    preview_parts.append(f"User: {content[:300]}")
                elif role == "assistant" and content:
                    preview_parts.append(f"Assistant: {content[:300]}")
        
        if not preview_parts:
            return
            
        # If it's the very first user message, just use that to generate a quick title
        if trigger_phase == "first_user" and len(preview_parts) == 1:
            prompt_context = f"User Request: {preview_parts[0]}"
        else:
            prompt_context = "\n".join(preview_parts)
        
        # Generate title using same model
        response = litellm.completion(
            model=_get_config()["model"],
            messages=[{
                "role": "user",
                "content": f"""Summarize this conversation in 2-4 words. Be specific and unique. 
No generic titles like "Code Help" or "Python Script".
No quotes.

Content:
{prompt_context}

Title:"""
            }],
            max_tokens=15,
            temperature=0.3,
        )
        
        title = response.choices[0].message.content.strip()
        # Clean up the title
        title = title.split('\n')[0]  # First line only
        title = title.strip('"\'')     # Remove quotes
        title = title.lstrip('#').strip()  # Remove markdown headers
        title = title.strip('*')       # Remove bold markers
        title = title[:40]             # Limit length (shorter now)
        
        if not title:
            return
        
        # Save title to both formats
        # Save title to history_manager (single source of truth)
        if hasattr(agent, 'history_manager'):
            agent.history_manager.metadata['title'] = title
            agent.history_manager._auto_save()
        
        # Emit title update to client
        socketio_instance.emit('title_updated', {'session_id': session_id, 'title': title})
        
    except Exception as e:
        print(f"Error generating title: {e}")


def _build_rich_history(agent):
    """Build rich history from ground truth, including tool_args for diff rendering.
    
    For large tools (edit_file), we only send metadata (file_path, line counts)
    to keep payloads small. Full diffs are only shown during live sessions.
    """
    history = []
    
    # Use ground truth entries for rich data (has tool_args in meta)
    if hasattr(agent, 'history_manager') and agent.history_manager:
        for entry in agent.history_manager.ground_truth.entries:
            msg = entry.message
            role = msg.get("role")
            
            if role == "user":
                content = msg.get("content", "")
                # Skip gist markers for display
                if "[Conversation gist]" in content:
                    continue
                history.append({
                    "role": "user",
                    "content": content
                })
            elif role == "assistant":
                content = msg.get("content")
                # Only add if there's actual content (skip tool-only messages)
                if content:
                    history.append({
                        "role": "assistant", 
                        "content": content
                    })
            elif role == "tool":
                tool_name = entry.meta.get("tool_name", "unknown")
                full_args = entry.meta.get("tool_args", {})
                content = msg.get("content", "")
                
                # Selectively include tool_args to keep payload small
                if tool_name == 'bash':
                    # Just send command (small), content already has output
                    tool_args = {'command': full_args.get('command', '')}
                elif tool_name == 'edit_file':
                    # Send file_path and line counts, not full content
                    old_str = full_args.get('old_str', '')
                    new_str = full_args.get('new_str', '')
                    tool_args = {
                        'file_path': full_args.get('file_path', ''),
                        'old_lines': len(old_str.splitlines()) if old_str else 0,
                        'new_lines': len(new_str.splitlines()) if new_str else 0,
                    }
                elif tool_name in ('read_file', 'create_file', 'delete_file', 'focus', 'unfocus', 'ls', 'rename_file'):
                    # Small args, send as-is
                    tool_args = full_args
                else:
                    # Other tools - send file_path if present, skip large content
                    tool_args = {}
                    if 'file_path' in full_args:
                        tool_args['file_path'] = full_args['file_path']
                
                history.append({
                    "role": "tool",
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "content": content
                })
    else:
        # Fallback to legacy format
        for msg in agent.history.messages:
            history.append({
                "role": msg.get("role"),
                "content": msg.get("content", ""),
                "tool_name": msg.get("tool_name")
            })
    
    return history


def get_available_slash_commands():
    """Get all available slash commands with descriptions."""
    commands = []
    # Add commands from config
    for cmd, desc in SLASH_COMMANDS:
        commands.append({"command": cmd, "description": desc})
    
    # Add session management commands
    commands.extend([
        {"command": "/new", "description": "Start new session"},
        {"command": "/load <session_id>", "description": "Load a session"},
        {"command": "/sessions", "description": "List recent sessions"},
        {"command": "/toggle-diff", "description": "Toggle detailed diff display"},
        {"command": "/help", "description": "Show help"},
    ])
    
    return commands

@app.route('/')
def index():
    """Main chat interface."""
    agent = get_agent()
    settings = Settings()
    session_id = agent.history.session_id
    session_title = agent.history_manager.metadata.get('title') if hasattr(agent, 'history_manager') else None
    
    # Get history for initial load
    history = []
    for msg in agent.history.messages:
        history.append({
            "role": msg.get("role"),
            "content": msg.get("content", ""),
            "tool_name": msg.get("tool_name")
        })
    
    return render_template('index.html', 
                         session_id=session_id[:8],
                         session_title=session_title,
                         history=history,
                         commands=get_available_slash_commands(),
                         show_diff=settings.show_diff)

@app.route('/workspace')
def workspace():
    """New modular workspace UI."""
    get_agent()  # Ensure agent is initialized
    return render_template('workspace.html')

@app.route('/api/sessions')
def api_sessions():
    """Get list of available sessions, optionally filtered by project."""
    project_id = request.args.get('project_id')
    sessions = list_sessions()
    
    # Filter by project if specified
    if project_id:
        filtered = []
        for s in sessions:
            session_project = _store.get('session', s['id'], 'project_id')
            # Only include sessions that explicitly match the project
            if session_project == project_id:
                filtered.append(s)
        sessions = filtered
    
    try:
        current_id = get_agent().history.session_id
    except Exception as e:
        # If current agent fails to load, just return sessions without current
        print(f"Warning: Failed to get current agent: {e}")
        current_id = None
    return jsonify({
        "sessions": sessions,
        "current": current_id
    })

@app.route('/api/current-session')
def api_current_session():
    """Get current session info and history (for page load)."""
    from core.project_manager import SessionIndex
    
    project_id = request.args.get('project_id')
    agent = get_agent()
    session_id = agent.history.session_id
    
    # STRICT MODE: If project_id is provided, ensure the current session belongs to it.
    if project_id:
        idx = SessionIndex()
        # Check explicit mapping first
        session_info = idx.get_session_info(session_id)
        current_project = session_info.get('current_project_id') if session_info else None
        
        # If not in index, fallback to checking agent's project (for fresh sessions)
        if not current_project and agent.project:
            current_project = agent.project.id
            
        # If mismatch, DO NOT return this session.
        # This prevents "bleed" where Project B loads Project A's session.
        if current_project and current_project != project_id:
            return jsonify({
                "error": "Session belongs to different project",
                "session_id": None,
                "project_mismatch": True
            }), 409

    title = agent.history_manager.metadata.get('title') if hasattr(agent, 'history_manager') else None
    
    # Build rich history from ground truth (includes tool_args for diff rendering)
    history = _build_rich_history(agent)
    
    return jsonify({
        "session_id": session_id,
        "title": title,
        "history": history,
        "message_count": len(history),
        "project_id": agent.project.id if agent.project else "local",
        "processing": session_id in active_processing
    })

@app.route('/api/load-session', methods=['POST'])
def api_load_session():
    """Load a specific session."""
    from core.project_manager import SessionIndex, ProjectManager
    
    data = request.json
    session_id = data.get('session_id')
    # Optional: If loading in context of a specific project
    target_project_id = data.get('project_id') 
    
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    
    try:
        client_id = flask_session['client_id']
        
        # Verify project ownership if context provided
        if target_project_id:
            idx = SessionIndex()
            info = idx.get_session_info(session_id)
            if info:
                # Allow loading if it belongs to target, OR if we're moving it?
                # For now, strict check: current_project_id must match
                current_project = info.get('current_project_id')
                if current_project and current_project != target_project_id:
                     return jsonify({
                        "error": f"Session belongs to project {current_project}",
                        "project_mismatch": True
                    }), 409

        # Use get_agent to properly track in tabs
        # But wait, get_agent might create a default one if not active.
        # We need to ensure the loaded agent has the correct project context from storage.
        
        # Check if agent is already active
        agent = None
        if client_id in active_agents and session_id in active_agents[client_id]:
            agent = active_agents[client_id][session_id]
        else:
            # Need to resurrect it.
            # First, find its project
            idx = SessionIndex()
            info = idx.get_session_info(session_id)
            project = None
            if info and info.get('current_project_id'):
                pm = ProjectManager()
                project = pm.get(info.get('current_project_id'))
            
            # If no project record, it might be an old session or local default
            if not project:
                pm = ProjectManager()
                project = pm.get_default()
                
            # Instantiate
            agent = Agent(
                system_prompt=_get_config()["system_prompt"],
                tools=_get_config()["tools"],
                model=_get_config()["model"],
                session_id=session_id,
                project=project, # Crucial: Restore with correct project
                litellm_params=_get_config().get("litellm_params", {}),
            )
            
            # Cache it
            if client_id not in active_agents:
                active_agents[client_id] = {}
            active_agents[client_id][session_id] = agent

        # Set as current tab
        set_current_tab(client_id, session_id)
        
        # Generate title in background if missing
        title = agent.history_manager.metadata.get('title') if hasattr(agent, 'history_manager') else None
        # Use new history manager if available, fall back to legacy
        msg_count = len(agent.history_manager.working.entries) if hasattr(agent, 'history_manager') and agent.history_manager else len(agent.history.messages)
        if not title and msg_count >= 2:
            thread = threading.Thread(target=generate_title_async, args=(agent, socketio))
            thread.daemon = True
            thread.start()
        
        # Return session info and rich history (includes tool_args for diff rendering)
        history = _build_rich_history(agent)
        
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

@app.route('/api/new-session', methods=['POST'])
def api_new_session():
    """Create a new session."""
    from core.project_manager import ProjectManager, SessionIndex
    
    data = request.json or {}
    project_id = data.get('project_id')
    client_id = flask_session.get('client_id')
    if not client_id:
        client_id = str(uuid.uuid4())
        flask_session['client_id'] = client_id
    
    # Resolve project
    pm = ProjectManager()
    project = None
    if project_id:
        project = pm.get(project_id)
        if not project:
            return jsonify({"error": f"Project not found: {project_id}"}), 404
    else:
        # Fallback to default (Local) if not specified, but this should be avoided by frontend
        project = pm.get_default()
        project_id = project.id
    
    # Create new agent with explicit project
    agent = Agent(
        system_prompt=_get_config()["system_prompt"],
        tools=_get_config()["tools"],
        model=_get_config()["model"],
        project=project,
        litellm_params=_get_config().get("litellm_params", {}),
    )
    
    session_id = agent.history.session_id
    
    # Persist session->project mapping
    idx = SessionIndex()
    idx.set_session_project(session_id, project_id, is_original=True)
    
    # Track in client's agents
    if client_id not in active_agents:
        active_agents[client_id] = {}
    active_agents[client_id][session_id] = agent
    
    # Track as open tab and set as current
    tabs = get_client_tabs(client_id)
    tabs.append(session_id)
    set_client_tabs(client_id, tabs)
    set_current_tab(client_id, session_id)
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "project_id": project_id
    })

@app.route('/api/toggle-diff', methods=['POST'])
def api_toggle_diff():
    """Toggle diff display setting."""
    settings = Settings()
    settings.show_diff = not settings.show_diff
    settings.save()
    
    return jsonify({
        "success": True,
        "show_diff": settings.show_diff
    })

@app.route('/api/projects')
def api_projects():
    """Get list of configured projects."""
    import os
    from core.project_manager import ProjectManager
    
    pm = ProjectManager()
    agent = get_agent()
    
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
        })
    
    # Get SSH profiles (saved connection templates)
    ssh_profiles = pm.list_ssh_profiles() if hasattr(pm, 'list_ssh_profiles') else []
    
    return jsonify({
        "projects": projects,
        "current": agent.project.id if agent.project else "local",
        "ssh_profiles": ssh_profiles,
        "home_dir": os.path.expanduser('~')
    })


@app.route('/api/projects', methods=['POST'])
def api_create_project():
    """Create or update a project."""
    import re
    from core.project_manager import ProjectManager
    from core.project import Project
    
    data = request.json
    pm = ProjectManager()
    
    # Validate required fields
    name = data.get('name', '').strip()
    path = data.get('path', '').strip()
    project_type = data.get('type', 'local')
    
    if not name:
        return jsonify({"error": "Project name is required"}), 400
    if not path:
        return jsonify({"error": "Project path is required"}), 400
    
    # Generate ID from name if not provided
    project_id = data.get('id')
    if not project_id:
        # Convert name to slug
        project_id = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        # Ensure uniqueness
        base_id = project_id
        counter = 1
        while pm.get(project_id):
            project_id = f"{base_id}-{counter}"
            counter += 1
    
    # Build project data
    project_data = {
        'id': project_id,
        'name': name,
        'type': project_type,
        'path': path,
        'color': data.get('color', '#ff6b2b'),
    }
    
    # Add SSH fields if SSH project
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
        
        # Check if updating existing or creating new
        existing = pm.get(project_id)
        if existing:
            pm.update(project)
        else:
            pm.add(project)
        
        # Save SSH profile if requested
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


@app.route('/api/projects/<project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    """Delete a project."""
    from core.project_manager import ProjectManager
    
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


@app.route('/api/projects/<project_id>', methods=['PATCH'])
def api_update_project(project_id):
    """Update a project's editable fields (name, color, favorite)."""
    from core.project_manager import ProjectManager
    
    pm = ProjectManager()
    project = pm.get(project_id)
    
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.json
    
    # Update allowed fields
    if 'name' in data:
        project.name = data['name'].strip()
    if 'color' in data:
        project.color = data['color']
    if 'favorite' in data:
        # Enforce max 5 favorites
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


@app.route('/api/ssh/hosts')
def api_ssh_hosts():
    """Get SSH hosts from ~/.ssh/config."""
    import os
    import re
    
    ssh_config_path = os.path.expanduser('~/.ssh/config')
    hosts = []
    
    try:
        if os.path.exists(ssh_config_path):
            with open(ssh_config_path, 'r') as f:
                content = f.read()
            
            # Parse SSH config
            current_host = None
            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Match "Host <name>" (but not "Host *")
                host_match = re.match(r'^Host\s+(\S+)$', line, re.IGNORECASE)
                if host_match:
                    host_name = host_match.group(1)
                    if host_name != '*':
                        current_host = {'name': host_name, 'hostname': None, 'user': None, 'port': 22}
                        hosts.append(current_host)
                    else:
                        current_host = None
                    continue
                
                if current_host:
                    # Parse host properties
                    if line.lower().startswith('hostname'):
                        current_host['hostname'] = line.split(None, 1)[1] if len(line.split()) > 1 else None
                    elif line.lower().startswith('user'):
                        current_host['user'] = line.split(None, 1)[1] if len(line.split()) > 1 else None
                    elif line.lower().startswith('port'):
                        try:
                            current_host['port'] = int(line.split()[1])
                        except (IndexError, ValueError):
                            pass
    except Exception as e:
        print(f"Error reading SSH config: {e}")
    
    return jsonify({'hosts': hosts})


@app.route('/api/ssh/parse', methods=['POST'])
def api_ssh_parse():
    """Parse an SSH command string like 'ssh -p 3333 user@host'."""
    import re
    
    data = request.json
    command = data.get('command', '').strip()
    
    # Remove 'ssh' prefix if present
    if command.lower().startswith('ssh '):
        command = command[4:].strip()
    
    result = {'host': '', 'user': '', 'port': 22}
    
    # Parse -p port
    port_match = re.search(r'-p\s*(\d+)', command)
    if port_match:
        result['port'] = int(port_match.group(1))
        command = re.sub(r'-p\s*\d+', '', command).strip()
    
    # Parse user@host
    if '@' in command:
        parts = command.split('@')
        result['user'] = parts[0].strip()
        result['host'] = parts[1].split()[0].strip() if parts[1] else ''
    else:
        # Just host
        result['host'] = command.split()[0] if command else ''
    
    return jsonify(result)


@app.route('/api/ssh/test', methods=['POST'])
def api_test_ssh():
    """Test SSH connection."""
    from core.filesystem import SSHFileSystem, SSHConnectionError, SSHAuthenticationError
    
    data = request.json
    host = data.get('host', '').strip()
    user = data.get('user', '').strip()
    port = int(data.get('port', 22))
    
    if not host:
        return jsonify({"success": False, "error": "Host is required"})
    if not user:
        return jsonify({"success": False, "error": "Username is required"})
    
    try:
        # Create temporary SSH filesystem to test connection
        ssh_fs = SSHFileSystem(
            host=host,
            root="/tmp",  # Just need to test connection
            user=user,
            port=port
        )
        
        # Try to list home directory as a simple test
        ssh_fs.ls(".")
        ssh_fs.close()
        
        return jsonify({"success": True, "message": "Connection successful"})
    
    except SSHAuthenticationError as e:
        return jsonify({"success": False, "error": f"Authentication failed: {e}"})
    except SSHConnectionError as e:
        return jsonify({"success": False, "error": f"Connection failed: {e}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/ssh/browse', methods=['POST'])
def api_ssh_browse():
    """Browse folders on a remote SSH server."""
    from core.filesystem import SSHFileSystem, SSHConnectionError, SSHAuthenticationError
    
    data = request.json
    host = data.get('host', '').strip()
    user = data.get('user', '').strip()
    port = int(data.get('port', 22))
    path = data.get('path', '~').strip()
    
    if not host or not user:
        return jsonify({"success": False, "error": "Host and user required"})
    
    try:
        # Expand ~ to home directory
        if path == '~' or path.startswith('~/'):
            path = f"/home/{user}" + path[1:] if path != '~' else f"/home/{user}"
        
        ssh_fs = SSHFileSystem(
            host=host,
            root=path,
            user=user,
            port=port
        )
        
        # List directory
        items = ssh_fs.ls(".")
        ssh_fs.close()
        
        # Filter to directories only and format
        folders = []
        for item in items:
            if item.get('is_dir'):
                folders.append({
                    'name': item['name'],
                    'path': f"{path}/{item['name']}".replace('//', '/'),
                    'is_dir': True
                })
        
        return jsonify({
            "success": True,
            "path": path,
            "contents": folders
        })
    
    except SSHAuthenticationError as e:
        return jsonify({"success": False, "error": f"Authentication failed"})
    except SSHConnectionError as e:
        return jsonify({"success": False, "error": f"Connection failed"})
    except FileNotFoundError:
        return jsonify({"success": False, "error": f"Path not found: {path}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/projects/switch', methods=['POST'])
def api_switch_project():
    """Switch current session to a different project."""
    from core.project_manager import ProjectManager
    from core.filesystem import set_current_project, clear_filesystem_cache
    
    data = request.json
    project_id = data.get('project_id')
    session_id = data.get('session_id')  # Optional - use provided or fall back to agent's
    
    if not project_id:
        return jsonify({"error": "No project_id provided"}), 400
    
    pm = ProjectManager()
    project = pm.get(project_id)
    
    if not project:
        return jsonify({"error": f"Project not found: {project_id}"}), 404
    
    # Update the agent's project
    agent = get_agent(session_id)  # Use provided session_id if given
    agent.project = project
    
    # Update Signella so tools use the new project
    # Use provided session_id or fall back to agent's session_id
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


@app.route('/api/projects/<project_id>/sessions')
def api_project_sessions(project_id):
    """Get sessions for a specific project."""
    sessions = list_sessions()
    
    # Filter to sessions that belong to this project
    project_sessions = []
    for s in sessions:
        session_project = _store.get('session', s['id'], 'project_id')
        if session_project == project_id:
            project_sessions.append(s)
    
    # Get the most recent session for this project (if any)
    most_recent = project_sessions[0] if project_sessions else None
    
    return jsonify({
        "sessions": project_sessions,
        "most_recent": most_recent['id'] if most_recent else None,
        "count": len(project_sessions)
    })


@app.route('/api/projects/<project_id>/new-session', methods=['POST'])
def api_project_new_session(project_id):
    """Create a new session for a specific project."""
    from core.project_manager import ProjectManager
    from core.filesystem import set_current_project
    
    pm = ProjectManager()
    project = pm.get(project_id)
    
    if not project:
        return jsonify({"error": f"Project not found: {project_id}"}), 404
    
    client_id = flask_session.get('client_id')
    if not client_id:
        client_id = str(uuid.uuid4())
        flask_session['client_id'] = client_id
    
    # Create new agent with this project
    agent = Agent(
        system_prompt=_get_config()["system_prompt"],
        tools=_get_config()["tools"],
        model=_get_config()["model"],
        litellm_params=_get_config().get("litellm_params", {}),
    )
    agent.project = project
    
    # Track in client's agents
    if client_id not in active_agents:
        active_agents[client_id] = {}
    active_agents[client_id][agent.history.session_id] = agent
    
    # Associate session with project in Signella
    session_id = agent.history.session_id
    set_current_project(session_id, project_id)
    
    # Track as open tab and set as current
    tabs = get_client_tabs(client_id)
    tabs.append(session_id)
    set_client_tabs(client_id, tabs)
    set_current_tab(client_id, session_id)
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "project_id": project_id
    })

@app.route('/api/context-stats')
def api_context_stats():
    """Get token usage breakdown for context visualization."""
    session_id = request.args.get('session_id')
    
    # Check if agent is already cached - don't create one just for stats
    client_id = flask_session.get('client_id')
    if client_id and client_id in active_agents:
        if session_id and session_id in active_agents[client_id]:
            agent = active_agents[client_id][session_id]
            stats = agent.get_context_stats()
            return jsonify(stats)
    
    # Agent not cached - return placeholder stats with current configured model
    # The agent will be created when the user actually interacts with the session
    from core.context_management import ModelProfile
    
    # Get current model config to show correct context window
    config = _get_config()
    model_name = config["model"]
    
    # Try to get the model profile for the current model
    try:
        profile = ModelProfile.from_model_string(model_name)
        budget = profile.context_window
        threshold = int(budget * 0.7)
        model_display = profile.name
    except:
        # Fallback
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

@app.route('/api/folders')
def api_folders():
    """Get folder contents for browsing (used by project settings)."""
    import os
    
    path = request.args.get('path', '~')
    
    # Expand ~ to home directory
    if path.startswith('~'):
        path = os.path.expanduser(path)
    
    # Normalize path
    path = os.path.abspath(path)
    
    # If path is a file, use its parent directory
    if os.path.isfile(path):
        path = os.path.dirname(path)
    
    # If path doesn't exist, try to find closest existing parent
    original_path = path
    while not os.path.exists(path) and path != '/':
        path = os.path.dirname(path)
    
    contents = []
    try:
        # List directory contents
        entries = os.listdir(path)
        for name in sorted(entries):
            # Skip hidden files unless we're showing them
            if name.startswith('.'):
                continue
            
            full_path = os.path.join(path, name)
            is_dir = os.path.isdir(full_path)
            
            # Only show directories for project selection
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
    
    return jsonify({
        'path': path,
        'contents': contents,
        'home_dir': os.path.expanduser('~')
    })


@app.route('/api/focused-files')
def api_focused_files():
    """Get list of focused files for current session with line counts."""
    from core.project_manager import ProjectManager, SessionIndex
    from core.filesystem import LocalFileSystem, SSHFileSystem
    
    session_id = request.args.get('session_id')
    
    # If no session_id provided, try to get from current tab
    if not session_id:
        client_id = flask_session.get('client_id')
        if client_id:
            session_id = get_current_tab(client_id)
    
    # If still no session_id, return empty
    if not session_id:
        return jsonify({"files": [], "count": 0, "session_id": None})
    
    # Read directly from Signella - don't create an agent
    files = list(_store.get('focus', session_id, 'files', default=[]))
    
    # Get the filesystem for this session's project
    idx = SessionIndex()
    pm = ProjectManager()
    
    session_info = idx.get_session_info(session_id)
    project_id = session_info.get('current_project_id') if session_info else None
    project = pm.get(project_id) if project_id else None
    
    # Get filesystem and project root
    if project:
        fs = project.get_filesystem()
        project_root = project.path
    else:
        # Fallback to local
        fs = LocalFileSystem(Path.cwd())
        project_root = str(Path.cwd())
    
    # Return relative paths with line counts
    file_info = []
    for f in files:
        # Calculate relative path from project root
        if f.startswith(project_root):
            display_path = f[len(project_root):].lstrip('/')
        else:
            display_path = f
        
        # Get line count using filesystem abstraction
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

def get_client_state(client_id):
    """Get or create client state."""
    if client_id not in client_state:
        client_state[client_id] = {"cancelled": False, "queued_message": None}
    return client_state[client_id]

@socketio.on('join_session')
def handle_join_session(data):
    """Join a session room to receive streaming events."""
    session_id = data.get('session_id')
    old_session_id = data.get('old_session_id')
    
    # Leave old session room if provided
    if old_session_id:
        leave_room(old_session_id)
    
    # Join new session room
    if session_id:
        join_room(session_id)
        # If this session is currently processing, let the client know
        if session_id in active_processing:
            emit('agent_reconnected', {"session_id": session_id, "processing": True})

@socketio.on('cancel')
def handle_cancel():
    """Handle cancel request from client."""
    client_id = flask_session.get('client_id')
    if client_id:
        state = get_client_state(client_id)
        state["cancelled"] = True
        state["queued_message"] = None  # Clear any queued message
        emit('cancelled', {"success": True})

@socketio.on('queue_message')
def handle_queue(data):
    """Queue a message to send after current completes."""
    client_id = flask_session.get('client_id')
    message = data.get('message', '').strip()
    if client_id and message:
        state = get_client_state(client_id)
        state["queued_message"] = message
        emit('message_queued', {"message": message})

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming chat messages with streaming response."""
    message = data.get('message', '').strip()
    session_id = data.get('session_id')  # Optional - uses current tab if not provided
    
    if not message:
        return
    
    client_id = flask_session.get('client_id')
    state = get_client_state(client_id) if client_id else {"cancelled": False, "queued_message": None}
    
    # Join the session room so we receive events (and so reconnecting clients can too)
    if session_id:
        join_room(session_id)
    
    # Reset cancellation flag at start
    state["cancelled"] = False
    state["queued_message"] = None
    
    # Get agent for specific session (or current tab)
    agent = get_agent(session_id)
    session_id = agent.history.session_id  # Ensure we have the actual session_id
    settings = Settings()
    
    # Handle slash commands
    if message.startswith('/'):
        handle_slash_command(message, agent, settings)
        return
    
    # Emit user message with session_id for multi-tab support
    emit('user_message', {"content": message, "session_id": session_id})
    
    # Check if this is a new session without a title
    current_title = agent.history_manager.metadata.get('title') if hasattr(agent, 'history_manager') else None
    msg_count = len(agent.history_manager.working.entries) if hasattr(agent, 'history_manager') else len(agent.history.messages)
    is_new_session = msg_count <= 2 and not current_title
    
    # If new session, trigger title generation immediately using just the user prompt
    if is_new_session:
        # We start a thread but give it a tiny delay to ensure message is persisted
        thread = threading.Thread(target=generate_title_async, args=(agent, socketio, False, "first_user"))
        thread.daemon = True
        thread.start()
    
    # Stream agent response
    emit('agent_start', {"session_id": session_id}, to=session_id)
    active_processing.add(session_id)  # Track that this session is processing
    
    try:
        current_text = ""  # Track text for current segment (resets after tool calls)
        
        for event in agent.stream(message):
            # Check for cancellation
            if state["cancelled"]:
                if current_text:
                    emit('agent_cancelled', {"session_id": session_id, "content": current_text}, to=session_id)
                else:
                    emit('agent_cancelled', {"session_id": session_id, "content": ""}, to=session_id)
                # Clean up incomplete tool calls
                agent.cleanup_incomplete_tool_calls()
                break
            
            if event.type == "text_delta":
                current_text += event.content
                emit('agent_delta', {"session_id": session_id, "content": event.content, "full_content": current_text}, to=session_id)
            
            elif event.type == "text_done":
                emit('agent_done', {"session_id": session_id, "content": current_text}, to=session_id)
                current_text = ""
            
            elif event.type == "tool_progress":
                emit('tool_progress', {
                    "session_id": session_id,
                    "name": event.name,
                    "index": event.index,
                    "bytes_received": event.bytes_received
                }, to=session_id)
            
            elif event.type == "tool_start":
                if current_text:
                    emit('agent_done', {"session_id": session_id, "content": current_text}, to=session_id)
                    current_text = ""
                emit('tool_start', {"session_id": session_id, "name": event.name, "args": event.arguments}, to=session_id)
            
            elif event.type == "tool_done":
                # Process tool result for display
                tool_data = {
                    "session_id": session_id,
                    "name": event.name,
                    "args": event.arguments,
                    "result": event.result,
                    "show_diff": settings.show_diff
                }
                
                # Special handling for edit_file
                if event.name == "edit_file" and "old_str" in event.arguments and "new_str" in event.arguments:
                    file_path = event.arguments.get("file_path", "")
                    ext = file_path.split(".")[-1] if "." in file_path else "text"
                    lang = LANG_MAP.get(ext, ext)
                    
                    tool_data.update({
                        "file_path": file_path,
                        "language": lang,
                        "old_content": event.arguments["old_str"],
                        "new_content": event.arguments["new_str"],
                        "old_lines": len(event.arguments["old_str"].splitlines()),
                        "new_lines": len(event.arguments["new_str"].splitlines()),
                    })
                
                emit('tool_done', tool_data, to=session_id)
                
                # Emit focused files update if focus/unfocus was called OR file was modified
                if event.name in ("focus", "unfocus", "macro_focus", "edit_file", "create_file", "delete_file"):
                    files = list(_store.get('focus', session_id, 'files', default=[]))
                    cwd = str(Path.cwd())
                    display_files = [f[len(cwd)+1:] if f.startswith(cwd) else f for f in files]
                    emit('focused_files_updated', {"session_id": session_id, "files": display_files, "count": len(files)}, to=session_id)
        # If there's remaining text that wasn't finalized, send it now
        if current_text and not state["cancelled"]:
            emit('agent_done', {"session_id": session_id, "content": current_text}, to=session_id)
        
        # Emit completion notification (for tab glow + sound)
        if not state["cancelled"]:
            emit('agent_complete', {"session_id": session_id}, to=session_id)
        
        # Clear processing state
        active_processing.discard(session_id)
        
        # Auto-generate/update title (in background) - logic inside decides if update is needed
        if not state["cancelled"]:
            thread = threading.Thread(target=generate_title_async, args=(agent, socketio))
            thread.daemon = True
            thread.start()
        
        # Check for queued message after completion
        if state["queued_message"] and not state["cancelled"]:
            queued = state["queued_message"]
            state["queued_message"] = None
            emit('processing_queued', {"message": queued}, to=session_id)
            # Recursively process the queued message
            handle_message({"message": queued, "session_id": session_id})
    
    except Exception as e:
        active_processing.discard(session_id)  # Clear on error too
        emit('agent_error', {"session_id": session_id, "error": str(e)}, to=session_id)

def handle_slash_command(command, agent, settings):
    """Handle slash commands."""
    parts = command[1:].split()
    if not parts:
        return
    
    cmd = parts[0].lower()
    
    if cmd == "sessions":
        sessions = list_sessions()
        emit('command_result', {
            "type": "sessions",
            "sessions": sessions,
            "current": agent.history.session_id
        })
    
    elif cmd == "new":
        client_id = flask_session['client_id']
        old_session = agent.history.session_id
        
        # Create new agent and track it
        new_agent = Agent(
            system_prompt=_get_config()["system_prompt"],
            tools=_get_config()["tools"],
            model=_get_config()["model"],
            litellm_params=_get_config().get("litellm_params", {}),
        )
        if client_id not in active_agents:
            active_agents[client_id] = {}
        active_agents[client_id][new_agent.history.session_id] = new_agent
        
        # Track as open tab
        tabs = get_client_tabs(client_id)
        tabs.append(new_agent.history.session_id)
        set_client_tabs(client_id, tabs)
        set_current_tab(client_id, new_agent.history.session_id)
        
        emit('command_result', {
            "type": "new_session", 
            "old_session": old_session,
            "new_session": new_agent.history.session_id
        })
    
    elif cmd == "load" and len(parts) > 1:
        session_id = parts[1]
        try:
            client_id = flask_session['client_id']
            old_session = agent.history.session_id
            
            # Use get_agent to load/create and track
            new_agent = get_agent(session_id)
            set_current_tab(client_id, session_id)
            
            # Send history
            history = []
            for msg in new_agent.history.messages:
                history.append({
                    "role": msg.get("role"),
                    "content": msg.get("content", ""),
                    "tool_name": msg.get("tool_name")
                })
            
            emit('command_result', {
                "type": "load_session",
                "old_session": old_session,
                "new_session": session_id,
                "history": history,
                "message_count": len(new_agent.history.messages)
            })
        except Exception as e:
            emit('command_result', {
                "type": "error",
                "message": f"Failed to load session: {str(e)}"
            })
    
    elif cmd == "toggle-diff" or cmd == "diff":
        settings.show_diff = not settings.show_diff
        settings.save()
        emit('command_result', {
            "type": "toggle_diff",
            "show_diff": settings.show_diff
        })
    
    elif cmd == "help":
        emit('command_result', {
            "type": "help",
            "commands": get_available_slash_commands(),
            "session_id": agent.history.session_id,
            "model": agent.model.split('/')[-1],
            "tools": [t.__name__ for t in agent.tools],
            "show_diff": settings.show_diff
        })
    
    elif cmd == "unfocus":
        session_id = agent.history.session_id
        file_path = parts[1] if len(parts) > 1 else None
        
        if file_path:
            # Remove specific file
            files = set(_store.get('focus', session_id, 'files', default=[]))
            # Try to match by basename or full path
            cwd = str(Path.cwd())
            abs_path = str(Path(file_path).resolve()) if not file_path.startswith('/') else file_path
            
            # Find and remove matching file
            to_remove = None
            for f in files:
                if f == abs_path or f == file_path or f.endswith('/' + file_path):
                    to_remove = f
                    break
            
            if to_remove:
                files.discard(to_remove)
                _store.set('focus', session_id, 'files', list(files))
                message = f"Unfocused: {file_path}"
            else:
                message = f"File not in focus: {file_path}"
        else:
            # Clear all
            _store.set('focus', session_id, 'files', [])
            message = "Cleared all focused files"
        
        # Send updated list
        files = list(_store.get('focus', session_id, 'files', default=[]))
        cwd = str(Path.cwd())
        display_files = [f[len(cwd)+1:] if f.startswith(cwd) else f for f in files]
        
        emit('command_result', {
            "type": "unfocus",
            "message": message,
            "files": display_files,
            "count": len(files)
        })
        emit('focused_files_updated', {"session_id": session_id, "files": display_files, "count": len(files)})
    
    elif cmd == "focus" and len(parts) > 1:
        session_id = agent.history.session_id
        file_path = parts[1]
        cwd = str(Path.cwd())
        
        # Resolve to absolute path
        path = Path(file_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        abs_path = str(path.resolve())
        
        if path.exists():
            files = set(_store.get('focus', session_id, 'files', default=[]))
            files.add(abs_path)
            _store.set('focus', session_id, 'files', list(files))
            message = f"Focused: {file_path}"
        else:
            message = f"File not found: {file_path}"
        
        # Send updated list
        files = list(_store.get('focus', session_id, 'files', default=[]))
        display_files = [f[len(cwd)+1:] if f.startswith(cwd) else f for f in files]
        
        emit('command_result', {
            "type": "focus",
            "message": message,
            "files": display_files,
            "count": len(files)
        })
        emit('focused_files_updated', {"session_id": session_id, "files": display_files, "count": len(files)})
    
    else:
        emit('command_result', {
            "type": "error",
            "message": f"Unknown command: /{cmd}. Type /help for available commands."
        })

# =============================================================================
# LLM Configuration API Routes
# =============================================================================

from core.llm_config import get_llm_config

@app.route('/api/llm/providers')
def api_llm_providers():
    """Get all LLM providers with their status and current selection."""
    try:
        llm_config = get_llm_config()
        return jsonify(llm_config.get_full_status())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/llm/key', methods=['POST'])
def api_llm_set_key():
    """Save an API key for a provider."""
    try:
        data = request.json
        provider_id = data.get('provider_id')
        api_key = data.get('api_key', '').strip()
        
        if not provider_id:
            return jsonify({"error": "provider_id is required"}), 400
        if not api_key:
            return jsonify({"error": "api_key is required"}), 400
        
        llm_config = get_llm_config()
        
        # Validate first
        valid, message = llm_config.validate_api_key(provider_id, api_key)
        if not valid:
            return jsonify({"success": False, "error": message}), 400
        
        # Save the key
        if llm_config.set_api_key(provider_id, api_key):
            # Fetch models now that key is saved
            models = llm_config.fetch_models(provider_id)
            return jsonify({
                "success": True,
                "message": message,
                "models": models
            })
        else:
            return jsonify({"success": False, "error": "Failed to save key"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/llm/key/<provider_id>', methods=['DELETE'])
def api_llm_delete_key(provider_id):
    """Remove an API key for a provider."""
    try:
        llm_config = get_llm_config()
        
        if llm_config.delete_api_key(provider_id):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Key not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/llm/validate', methods=['POST'])
def api_llm_validate():
    """Validate an API key without saving."""
    try:
        data = request.json
        provider_id = data.get('provider_id')
        api_key = data.get('api_key', '').strip()
        
        if not provider_id:
            return jsonify({"error": "provider_id is required"}), 400
        if not api_key:
            return jsonify({"error": "api_key is required"}), 400
        
        llm_config = get_llm_config()
        valid, message = llm_config.validate_api_key(provider_id, api_key)
        
        if valid:
            # Also fetch models on successful validation
            # Temporarily set the key to fetch models without saving to file
            old_key = llm_config.get_api_key(provider_id)
            
            # Temporarily set environment variable for fetching
            env_var = llm_config.PROVIDERS.get(provider_id, {}).get('key_env')
            old_env_value = os.environ.get(env_var) if env_var else None
            
            if env_var:
                os.environ[env_var] = api_key
            
            try:
                models = llm_config.fetch_models(provider_id)
            finally:
                # Restore original environment
                if env_var:
                    if old_env_value is not None:
                        os.environ[env_var] = old_env_value
                    elif env_var in os.environ:
                        del os.environ[env_var]
            
            return jsonify({
                "valid": True,
                "message": message,
                "models": models
            })
        else:
            return jsonify({
                "valid": False,
                "error": message
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/llm/models/<provider_id>')
def api_llm_models(provider_id):
    """Fetch available models for a provider (fetches fresh from API)."""
    try:
        llm_config = get_llm_config()
        models = llm_config.fetch_models(provider_id)
        
        # If fetch failed and returned empty, fallback to static list
        if not models:
            provider = llm_config.PROVIDERS.get(provider_id)
            if provider:
                models = provider.get('models', [])
        
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/llm/active', methods=['POST'])
def api_llm_set_active():
    """Set the active provider and model."""
    try:
        data = request.json
        provider_id = data.get('provider_id')
        model_id = data.get('model_id')
        
        if not provider_id:
            return jsonify({"error": "provider_id is required"}), 400
        if not model_id:
            return jsonify({"error": "model_id is required"}), 400
        
        llm_config = get_llm_config()
        
        if llm_config.set_active_model(provider_id, model_id):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Invalid provider"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/llm/ollama/test', methods=['POST'])
def api_llm_ollama_test():
    """Test Ollama connection."""
    try:
        data = request.json or {}
        url = data.get('url')
        
        llm_config = get_llm_config()
        success, message, models = llm_config.test_ollama_connection(url)
        
        return jsonify({
            "success": success,
            "message": message,
            "models": models
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/llm/ollama/url', methods=['POST'])
def api_llm_ollama_url():
    """Save Ollama server URL."""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "url is required"}), 400
        
        llm_config = get_llm_config()
        llm_config.set_ollama_url(url)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    """Entry point for the prismweb command."""
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()