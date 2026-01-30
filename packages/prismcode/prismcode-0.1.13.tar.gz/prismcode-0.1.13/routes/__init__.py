"""
Routes package - Modular Flask routes for Prism web interface.

Modules:
- sessions: Session management (load, new, current)
- projects: Project CRUD and switching
- ssh: SSH connection testing and browsing
- llm: LLM provider configuration
- socket_handlers: SocketIO event handlers
"""

from .sessions import sessions_bp
from .projects import projects_bp
from .ssh import ssh_bp
from .llm import llm_bp

__all__ = ['sessions_bp', 'projects_bp', 'ssh_bp', 'llm_bp']
