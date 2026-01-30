"""
SocketIO event handlers.
"""
import threading
from pathlib import Path
from flask import session as flask_session
from flask_socketio import emit, join_room, leave_room

from core.agent import Agent
from config import LANG_MAP, SLASH_COMMANDS, get_agent_config
from settings import Settings

from .shared import (
    get_agent, get_store, get_client_tabs, set_client_tabs,
    get_current_tab, set_current_tab, get_client_state,
    generate_title_async, active_agents, active_processing,
    _get_config
)

_store = get_store()

# Reference to socketio - will be set by run_web.py
_socketio = None

def set_socketio(socketio):
    """Set the SocketIO instance."""
    global _socketio
    _socketio = socketio


def register_handlers(socketio):
    """Register all SocketIO event handlers."""

    @socketio.on('terminal_exec')
    def handle_terminal_exec(data):
        """Execute a command from the web terminal."""
        command = data.get('command', '').strip()
        if not command:
            return

        import subprocess
        try:
            # Execute command in shell
            # Note: This is simplified. In a production app, this should be 
            # more restricted or run in a proper PTY.
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            if not output.strip() and result.returncode == 0:
                output = "(completed with no output)"
                
            emit('terminal_output', {
                "output": output,
                "terminal": data.get('terminal'),
                "type": "stdout" if result.returncode == 0 else "stderr"
            })
        except Exception as e:
            emit('terminal_output', {
                "output": f"Error: {str(e)}",
                "terminal": data.get('terminal'),
                "type": "stderr"
            })

    @socketio.on('join_session')
    def handle_join_session(data):
        """Join a session room to receive streaming events."""
        session_id = data.get('session_id')
        old_session_id = data.get('old_session_id')

        if old_session_id:
            leave_room(old_session_id)

        if session_id:
            join_room(session_id)
            if session_id in active_processing:
                emit('agent_reconnected', {"session_id": session_id, "processing": True})

    @socketio.on('cancel')
    def handle_cancel():
        """Handle cancel request from client."""
        client_id = flask_session.get('client_id')
        if client_id:
            state = get_client_state(client_id)
            state["cancelled"] = True
            state["queued_message"] = None
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
        session_id = data.get('session_id')

        if not message:
            return

        client_id = flask_session.get('client_id')
        state = get_client_state(client_id) if client_id else {"cancelled": False, "queued_message": None}

        state["cancelled"] = False
        state["queued_message"] = None

        agent = get_agent(session_id)
        session_id = agent.history.session_id
        settings = Settings()

        # Always join the session room AFTER we have the actual session_id
        # (get_agent may create a new session if session_id was None)
        join_room(session_id)

        # Handle slash commands
        if message.startswith('/'):
            handle_slash_command(message, agent, settings, socketio)
            return

        emit('user_message', {"content": message, "session_id": session_id})

        # Check for title generation
        current_title = agent.history_manager.metadata.get('title') if hasattr(agent, 'history_manager') else None
        msg_count = len(agent.history_manager.working.entries) if hasattr(agent, 'history_manager') else len(agent.history.messages)
        is_new_session = msg_count <= 2 and not current_title

        if is_new_session:
            thread = threading.Thread(target=generate_title_async, args=(agent, socketio, False, "first_user"))
            thread.daemon = True
            thread.start()

        emit('agent_start', {"session_id": session_id}, to=session_id)
        active_processing.add(session_id)

        try:
            current_text = ""

            for event in agent.stream(message):
                if state["cancelled"]:
                    if current_text:
                        emit('agent_cancelled', {"session_id": session_id, "content": current_text}, to=session_id)
                    else:
                        emit('agent_cancelled', {"session_id": session_id, "content": ""}, to=session_id)
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
                    tool_data = {
                        "session_id": session_id,
                        "name": event.name,
                        "args": event.arguments,
                        "result": event.result,
                        "show_diff": settings.show_diff
                    }

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

                    if event.name in ("focus", "unfocus", "macro_focus", "edit_file", "create_file", "delete_file"):
                        files = list(_store.get('focus', session_id, 'files', default=[]))
                        cwd = str(Path.cwd())
                        display_files = [f[len(cwd)+1:] if f.startswith(cwd) else f for f in files]
                        emit('focused_files_updated', {"session_id": session_id, "files": display_files, "count": len(files)}, to=session_id)

            if current_text and not state["cancelled"]:
                emit('agent_done', {"session_id": session_id, "content": current_text}, to=session_id)

            if not state["cancelled"]:
                emit('agent_complete', {"session_id": session_id}, to=session_id)

            active_processing.discard(session_id)

            if not state["cancelled"]:
                thread = threading.Thread(target=generate_title_async, args=(agent, socketio))
                thread.daemon = True
                thread.start()

            if state["queued_message"] and not state["cancelled"]:
                queued = state["queued_message"]
                state["queued_message"] = None
                emit('processing_queued', {"message": queued}, to=session_id)
                handle_message({"message": queued, "session_id": session_id})

        except Exception as e:
            active_processing.discard(session_id)
            emit('agent_error', {"session_id": session_id, "error": str(e)}, to=session_id)


def handle_slash_command(command, agent, settings, socketio):
    """Handle slash commands."""
    parts = command[1:].split()
    if not parts:
        return

    cmd = parts[0].lower()
    session_id = agent.history.session_id

    if cmd == "sessions":
        from core.history import list_sessions
        sessions = list_sessions()
        emit('command_result', {
            "type": "sessions",
            "sessions": sessions,
            "current": session_id
        })

    elif cmd == "new":
        client_id = flask_session['client_id']
        old_session = session_id

        new_agent = Agent(
            system_prompt=_get_config()["system_prompt"],
            tools=_get_config()["tools"],
            model=_get_config()["model"],
            litellm_params=_get_config().get("litellm_params", {}),
        )
        if client_id not in active_agents:
            active_agents[client_id] = {}
        active_agents[client_id][new_agent.history.session_id] = new_agent

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
        load_session_id = parts[1]
        try:
            client_id = flask_session['client_id']
            old_session = session_id

            new_agent = get_agent(load_session_id)
            set_current_tab(client_id, load_session_id)

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
                "new_session": load_session_id,
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
        commands = []
        for c, desc in SLASH_COMMANDS:
            commands.append({"command": c, "description": desc})
        commands.extend([
            {"command": "/new", "description": "Start new session"},
            {"command": "/load <session_id>", "description": "Load a session"},
            {"command": "/sessions", "description": "List recent sessions"},
            {"command": "/toggle-diff", "description": "Toggle detailed diff display"},
            {"command": "/help", "description": "Show help"},
        ])

        emit('command_result', {
            "type": "help",
            "commands": commands,
            "session_id": session_id,
            "model": agent.model.split('/')[-1],
            "tools": [t.__name__ for t in agent.tools],
            "show_diff": settings.show_diff
        })

    elif cmd == "unfocus":
        file_path = parts[1] if len(parts) > 1 else None

        if file_path:
            files = set(_store.get('focus', session_id, 'files', default=[]))
            cwd = str(Path.cwd())
            abs_path = str(Path(file_path).resolve()) if not file_path.startswith('/') else file_path

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
            _store.set('focus', session_id, 'files', [])
            message = "Cleared all focused files"

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
        file_path = parts[1]
        cwd = str(Path.cwd())

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
