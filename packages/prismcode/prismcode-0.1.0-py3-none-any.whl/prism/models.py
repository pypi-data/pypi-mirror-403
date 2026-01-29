"""Data models for the Prism dependency graph."""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Set, Optional, Dict, Any


class NodeType(Enum):
    """Type of file/node in the dependency graph."""
    PYTHON = "python"
    HTML = "html"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    CSS = "css"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, ext: str) -> "NodeType":
        """Determine node type from file extension."""
        ext = ext.lower()
        if ext == ".py":
            return cls.PYTHON
        elif ext in {".html", ".htm", ".jinja", ".jinja2"}:
            return cls.HTML
        elif ext in {".js", ".jsx"}:
            return cls.JAVASCRIPT
        elif ext in {".ts", ".tsx"}:
            return cls.TYPESCRIPT
        elif ext in {".css", ".scss", ".less"}:
            return cls.CSS
        else:
            return cls.UNKNOWN


class EdgeType(Enum):
    """Type of dependency relationship."""
    IMPORT = "import"  # Python import
    DYNAMIC_IMPORT = "dynamic"  # importlib.import_module, __import__
    STRING_REF = "string_ref"  # String reference to module
    TEMPLATE = "template"  # Flask render_template
    SCRIPT = "script"  # HTML <script src="">
    STYLESHEET = "stylesheet"  # HTML <link rel="stylesheet">
    INCLUDE = "include"  # Jinja {% include %}
    EXTENDS = "extends"  # Jinja {% extends %}
    JS_IMPORT = "js_import"  # ES6 import / require()
    CSS_IMPORT = "css_import"  # @import


@dataclass
class Node:
    """Represents a file in the dependency graph."""
    path: Path  # Absolute path
    node_type: NodeType
    relative_path: str = ""  # Relative to project root
    lines: int = 0
    tokens: int = 0

    # Graph metadata
    is_entry_point: bool = False
    entry_point_label: Optional[str] = None
    entry_point_color: Optional[str] = None
    entry_point_emoji: Optional[str] = None

    # Computed properties
    depth_from_entry: Optional[int] = None

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.path == other.path
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "relative_path": self.relative_path,
            "type": self.node_type.value,
            "lines": self.lines,
            "tokens": self.tokens,
            "is_entry_point": self.is_entry_point,
            "entry_point_label": self.entry_point_label,
            "entry_point_color": self.entry_point_color,
            "entry_point_emoji": self.entry_point_emoji,
            "depth_from_entry": self.depth_from_entry,
        }


@dataclass
class Edge:
    """Represents a dependency relationship between two nodes."""
    source: Node  # The file that imports/includes
    target: Node  # The file being imported/included
    edge_type: EdgeType

    # Path metadata (for chain tracing)
    chain: list[str] = field(default_factory=list)  # Path from entry point

    def __hash__(self):
        return hash((self.source.path, self.target.path, self.edge_type))

    def __eq__(self, other):
        if isinstance(other, Edge):
            return (self.source.path == other.source.path and
                    self.target.path == other.target.path and
                    self.edge_type == other.edge_type)
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source": self.source.relative_path,
            "target": self.target.relative_path,
            "type": self.edge_type.value,
            "chain": self.chain,
        }


@dataclass
class EntryPoint:
    """Configuration for an entry point in the project."""
    path: str  # Relative path from project root
    label: str
    color: str = "#58a6ff"
    emoji: str = "🔵"
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "label": self.label,
            "color": self.color,
            "emoji": self.emoji,
            "enabled": self.enabled,
        }


@dataclass
class SnapshotConfig:
    """Configuration for generating a dependency snapshot."""
    target_path: str  # Relative path to target file

    # Parent configuration
    parent_depth: int = 1

    # Chain configuration
    include_chain: bool = False
    chain_length: Optional[int] = None

    # Children configuration
    child_depth: int = 0
    child_max_tokens: int = 0
    excluded_children: Set[str] = field(default_factory=set)

    # Frontend configuration
    include_frontend: bool = False
    excluded_frontend: Set[str] = field(default_factory=set)

    # Extra files (manually selected from sidebar)
    extra_files: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target_path": self.target_path,
            "parent_depth": self.parent_depth,
            "include_chain": self.include_chain,
            "chain_length": self.chain_length,
            "child_depth": self.child_depth,
            "child_max_tokens": self.child_max_tokens,
            "excluded_children": list(self.excluded_children),
            "include_frontend": self.include_frontend,
            "excluded_frontend": list(self.excluded_frontend),
            "extra_files": list(self.extra_files),
        }
