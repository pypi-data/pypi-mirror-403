"""
Project model and data structures.

A Project represents a directory (local or remote) containing code to work on.
Projects can be local filesystem paths or remote SSH connections.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .filesystem import FileSystem


@dataclass
class Project:
    """
    A project configuration pointing to a code directory.
    
    Projects can be either local (filesystem path) or remote (SSH).
    Each project has a unique ID, display name, and connection details.
    """
    
    id: str                                    # Unique identifier (slug format: alphanumeric + hyphens)
    name: str                                  # Display name
    type: Literal["local", "ssh"]              # Connection type
    path: str                                  # Root path on the filesystem
    color: str = "#ff6b2b"                     # UI accent color
    
    # SSH-specific fields (only used if type == "ssh")
    host: Optional[str] = None                 # SSH hostname or config alias
    user: Optional[str] = None                 # SSH username (optional if in SSH config)
    port: int = 22                             # SSH port
    
    # Timestamps
    created_at: Optional[str] = None           # ISO timestamp
    last_accessed: Optional[str] = None        # ISO timestamp
    
    # UI state
    favorite: bool = False                     # Pinned to project bar
    notifications: int = 0                     # Pending notifications (placeholder)
    
    def __post_init__(self):
        """Validate project configuration."""
        # Validate ID is slug-safe
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$', self.id):
            raise ValueError(
                f"Project ID must be lowercase alphanumeric with hyphens, "
                f"not starting or ending with hyphen: {self.id}"
            )
        
        # Validate type
        if self.type not in ("local", "ssh"):
            raise ValueError(f"Project type must be 'local' or 'ssh', got: {self.type}")
        
        # SSH projects require host
        if self.type == "ssh" and not self.host:
            raise ValueError("SSH projects require a host")
        
        # Set created_at if not provided
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def get_filesystem(self) -> "FileSystem":
        """
        Get the appropriate filesystem for this project.
        
        Returns:
            LocalFileSystem for local projects, SSHFileSystem for SSH projects.
        """
        from .filesystem import LocalFileSystem, SSHFileSystem
        
        if self.type == "local":
            return LocalFileSystem(Path(self.path))
        else:
            return SSHFileSystem(
                host=self.host,
                root=self.path,
                user=self.user,
                port=self.port
            )
    
    def to_dict(self) -> dict:
        """
        Serialize project to dictionary for JSON storage.
        
        Returns:
            Dictionary representation of the project.
        """
        data = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "path": self.path,
            "color": self.color,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "favorite": self.favorite,
            "notifications": self.notifications,
        }
        
        # Only include SSH fields if it's an SSH project
        if self.type == "ssh":
            data["host"] = self.host
            if self.user:
                data["user"] = self.user
            if self.port != 22:
                data["port"] = self.port
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """
        Create a Project from a dictionary.
        
        Args:
            data: Dictionary with project fields
            
        Returns:
            Project instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            type=data["type"],
            path=data["path"],
            color=data.get("color", "#ff6b2b"),
            host=data.get("host"),
            user=data.get("user"),
            port=data.get("port", 22),
            created_at=data.get("created_at"),
            last_accessed=data.get("last_accessed"),
            favorite=data.get("favorite", False),
            notifications=data.get("notifications", 0),
        )
    
    def touch_accessed(self) -> None:
        """Update last_accessed timestamp to now."""
        self.last_accessed = datetime.now().isoformat()
    
    def __str__(self) -> str:
        if self.type == "ssh":
            return f"{self.name} ({self.host}:{self.path})"
        return f"{self.name} ({self.path})"
    
    def __repr__(self) -> str:
        return f"Project(id={self.id!r}, name={self.name!r}, type={self.type!r})"
