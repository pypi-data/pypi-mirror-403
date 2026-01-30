"""
Shared state and utilities for route modules.
"""
import uuid
import threading
from pathlib import Path
from flask import session as flask_session

from core.agent import Agent
from core.history import list_sessions
from core.signella import Signella
from config import get_agent_config
import litellm

_store = Signella()

# Shared state
active_agents = {}  # {client_id: {session_id: Agent}}
client_state = {}   # {client_id: {"cancelled": bool, "queued_message": str|None}}
active_processing = set()  # Set of session_ids currently being processed

# SocketIO reference - set by run_web.py
_socketio = None

def set_socketio(socketio):
    """Set the SocketIO instance for modules that need it."""
    global _socketio
    _socketio = socketio

def get_socketio():
    """Get the SocketIO instance."""
    return _socketio


def _get_config():
    """Get fresh agent config each time (for dynamic model switching)."""
    return get_agent_config()


def get_store():
    """Get the Signella store instance."""
    return _store


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


def get_client_state(client_id):
    """Get or create client state."""
    if client_id not in client_state:
        client_state[client_id] = {"cancelled": False, "queued_message": None}
    return client_state[client_id]


def refresh_active_agents():
    """Refresh model config for all active agents."""
    config = _get_config()
    for client_agents in active_agents.values():
        for agent in client_agents.values():
            agent._model = config.get("model")
            agent.litellm_params = config.get("litellm_params", {})
            agent.history.metadata["model"] = agent.model
            agent._refresh_model_profile()


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
        if existing_title and not force:
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

        def clean_content(text):
            if not text: return ""
            if "[Conversation gist]" in text:
                text = text.replace("[Conversation gist]", "").strip()
            if "Memory Archive:" in text:
                lines = text.split('\n')
                text = '\n'.join([l for l in lines if not l.startswith("Memory Archive")])
            return text.strip()

        # Try new format first (ground truth entries)
        if entries:
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
            max_tokens=20,
            temperature=0.3,
        )

        title = (response.choices[0].message.content or "").strip()
        title = title.split('\n')[0]
        title = title.strip('"\'')
        title = title.lstrip('#').strip()
        title = title.strip('*')
        title = title[:40]

        if not title:
            return

        # Save title to history_manager
        if hasattr(agent, 'history_manager'):
            agent.history_manager.metadata['title'] = title
            agent.history_manager._auto_save()

        # Emit title update to client
        socketio_instance.emit('title_updated', {'session_id': session_id, 'title': title})

    except Exception as e:
        print(f"Error generating title: {e}")


def build_rich_history(agent):
    """Build rich history from ground truth, including tool_args for diff rendering.

    For large tools (edit_file), we only send metadata (file_path, line counts)
    to keep payloads small.
    """
    history = []

    if hasattr(agent, 'history_manager') and agent.history_manager:
        for entry in agent.history_manager.ground_truth.entries:
            msg = entry.message
            role = msg.get("role")

            if role == "user":
                content = msg.get("content", "")
                if "[Conversation gist]" in content:
                    continue
                history.append({
                    "role": "user",
                    "content": content
                })
            elif role == "assistant":
                content = msg.get("content")
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
                    tool_args = {'command': full_args.get('command', '')}
                elif tool_name == 'edit_file':
                    old_str = full_args.get('old_str', '')
                    new_str = full_args.get('new_str', '')
                    tool_args = {
                        'file_path': full_args.get('file_path', ''),
                        'old_lines': len(old_str.splitlines()) if old_str else 0,
                        'new_lines': len(new_str.splitlines()) if new_str else 0,
                    }
                elif tool_name in ('read_file', 'create_file', 'delete_file', 'focus', 'unfocus', 'ls', 'rename_file'):
                    tool_args = full_args
                else:
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
