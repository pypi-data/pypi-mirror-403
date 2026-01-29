"""Prism - A clean, modular dependency analysis engine for Python projects.

This package provides a stateless, session-based architecture for analyzing
Python, HTML, JavaScript, and CSS dependencies in a unified graph structure.

Basic Usage:
    >>> from prism import PrismSession
    >>> session = PrismSession("/path/to/project")
    >>> session.scan()
    >>> entry_points = session.get_entry_points()
    >>> snapshot = session.create_snapshot({"target_path": "main.py"})
"""

from .session import PrismSession
from .models import (
    Node,
    Edge,
    NodeType,
    EdgeType,
    EntryPoint,
    SnapshotConfig,
)
from .graph import DependencyGraph
from .scanner import FileScanner
from .snapshot import SnapshotBuilder
from .parsers import (
    PythonParser,
    HTMLParser,
    JavaScriptParser,
    CSSParser,
    PathResolver,
)

__version__ = "1.0.0"

__all__ = [
    # Main interface
    "PrismSession",
    # Models
    "Node",
    "Edge",
    "NodeType",
    "EdgeType",
    "EntryPoint",
    "SnapshotConfig",
    # Core components
    "DependencyGraph",
    "FileScanner",
    "SnapshotBuilder",
    # Parsers
    "PythonParser",
    "HTMLParser",
    "JavaScriptParser",
    "CSSParser",
    "PathResolver",
]
