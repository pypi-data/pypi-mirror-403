#!/usr/bin/env python3
"""
Flask web interface for Prism agent.
Real-time streaming, session management, tool display with diffs.

Routes are organized into modular blueprints:
- routes/sessions.py: Session management
- routes/projects.py: Project CRUD
- routes/ssh.py: SSH connections
- routes/llm.py: LLM configuration
- routes/socket_handlers.py: SocketIO events
"""
# Clean environment before any imports to avoid litellm conflicts with
# misconfigured OpenAI env vars (e.g., OPENAI_API_KEY pointing to Cerebras)
import os
_base_url = os.environ.get('OPENAI_BASE_URL', '') or os.environ.get('OPENAI_API_BASE', '')
if _base_url and 'api.openai.com' not in _base_url:
    # Non-OpenAI base URL detected - clear all OpenAI vars to prevent litellm confusion
    for var in ['OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_API_BASE', 'OPENAI_MODEL']:
        os.environ.pop(var, None)

# Load .env file before anything else
from dotenv import load_dotenv
load_dotenv(override=True)

# Suppress litellm's verbose logging during import
os.environ.setdefault('LITELLM_LOG', 'ERROR')

from flask import Flask
from flask_socketio import SocketIO

# Import blueprints
from routes import sessions_bp, projects_bp, ssh_bp, llm_bp
from routes.socket_handlers import register_handlers
from routes.llm import set_socketio as llm_set_socketio
from routes.shared import set_socketio as shared_set_socketio

# Enable LiteLLM debug logging
import litellm
litellm._turn_on_debug()

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'prism-web-secret-key'

# Create SocketIO instance
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
app.register_blueprint(sessions_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(ssh_bp)
app.register_blueprint(llm_bp)

# Register SocketIO handlers
register_handlers(socketio)

# Set socketio reference for modules that need it
llm_set_socketio(socketio)
shared_set_socketio(socketio)


def main():
    """Entry point for the prismweb command."""
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
