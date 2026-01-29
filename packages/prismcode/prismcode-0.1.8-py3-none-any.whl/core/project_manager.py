"""
Project and Session management.

Handles CRUD operations for projects and tracks which sessions
belong to which projects.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .project import Project


def get_prism_dir() -> Path:
    """Get or create ~/.prism directory."""
    prism_dir = Path.home() / ".prism"
    prism_dir.mkdir(exist_ok=True)
    return prism_dir


class ProjectManager:
    """
    Manages project configurations.
    
    Projects are stored in ~/.prism/projects.json and represent
    local or remote directories that can be worked on.
    """
    
    PROJECTS_PATH = get_prism_dir() / "projects.json"
    SSH_PROFILES_PATH = get_prism_dir() / "ssh_profiles.json"
    
    def __init__(self):
        """Initialize and load projects from disk."""
        self._projects: Dict[str, Project] = {}
        self._ssh_profiles: List[dict] = []
        self._default_project_id: Optional[str] = None
        self._load()
        self._load_ssh_profiles()
    
    def _load(self) -> None:
        """Load projects from config file."""
        if self.PROJECTS_PATH.exists():
            try:
                data = json.loads(self.PROJECTS_PATH.read_text())
                for p in data.get("projects", []):
                    try:
                        project = Project.from_dict(p)
                        self._projects[project.id] = project
                    except (ValueError, KeyError) as e:
                        print(f"Warning: Skipping invalid project: {e}")
                self._default_project_id = data.get("default_project")
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse projects.json: {e}")
        
        # Ensure we always have a default local project
        self._ensure_default_project()
    
    def _ensure_default_project(self) -> None:
        """Create default local project if none exists."""
        if not self._projects:
            # Create default project for current working directory
            default = Project(
                id="local",
                name="Local",
                type="local",
                path=str(Path.cwd()),
                color="#ff6b2b",
            )
            self._projects["local"] = default
            self._default_project_id = "local"
            self._save()
    
    def _save(self) -> None:
        """Save projects to config file."""
        self.PROJECTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "default_project": self._default_project_id,
            "projects": [p.to_dict() for p in self._projects.values()]
        }
        self.PROJECTS_PATH.write_text(json.dumps(data, indent=2))
    
    def list(self) -> List[Project]:
        """
        List all projects.
        
        Returns:
            List of all configured projects.
        """
        return list(self._projects.values())
    
    def get(self, project_id: str) -> Optional[Project]:
        """
        Get project by ID.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            Project if found, None otherwise.
        """
        return self._projects.get(project_id)
    
    def add(self, project: Project) -> None:
        """
        Add a new project.
        
        Args:
            project: Project to add
            
        Raises:
            ValueError: If project with same ID already exists
        """
        if project.id in self._projects:
            raise ValueError(f"Project with ID '{project.id}' already exists")
        
        self._projects[project.id] = project
        self._save()
    
    def update(self, project: Project) -> None:
        """
        Update an existing project.
        
        Args:
            project: Project with updated fields (matched by ID)
            
        Raises:
            ValueError: If project doesn't exist
        """
        if project.id not in self._projects:
            raise ValueError(f"Project '{project.id}' not found")
        
        self._projects[project.id] = project
        self._save()
    
    def remove(self, project_id: str) -> bool:
        """
        Remove a project.
        
        Args:
            project_id: ID of project to remove
            
        Returns:
            True if removed, False if not found
            
        Raises:
            ValueError: If trying to remove the last project
        """
        if project_id not in self._projects:
            return False
        
        # Can't remove the last project
        if len(self._projects) == 1:
            raise ValueError("Cannot remove the last project")
        
        # If removing default, auto-promote another project
        if project_id == self._default_project_id:
            # Find another project to promote
            for pid in self._projects:
                if pid != project_id:
                    self._default_project_id = pid
                    break
        
        del self._projects[project_id]
        self._save()
        return True
    
    def get_default(self) -> Project:
        """
        Get the default project.
        
        Returns:
            The default project (creates one if none exists)
        """
        if self._default_project_id and self._default_project_id in self._projects:
            return self._projects[self._default_project_id]
        
        # Fallback to first project or create default
        if self._projects:
            return list(self._projects.values())[0]
        
        self._ensure_default_project()
        return self._projects[self._default_project_id]
    
    def set_default(self, project_id: str) -> None:
        """
        Set the default project.
        
        Args:
            project_id: ID of project to make default
            
        Raises:
            ValueError: If project doesn't exist
        """
        if project_id not in self._projects:
            raise ValueError(f"Project '{project_id}' not found")
        
        self._default_project_id = project_id
        self._save()
    
    def touch_accessed(self, project_id: str) -> None:
        """
        Update last_accessed timestamp for a project.
        
        Args:
            project_id: ID of project to update
        """
        if project_id in self._projects:
            self._projects[project_id].touch_accessed()
            self._save()
    
    # -------------------------------------------------------------------------
    # SSH Profiles
    # -------------------------------------------------------------------------
    
    def _load_ssh_profiles(self) -> None:
        """Load SSH profiles from config file."""
        if self.SSH_PROFILES_PATH.exists():
            try:
                data = json.loads(self.SSH_PROFILES_PATH.read_text())
                self._ssh_profiles = data.get("profiles", [])
            except json.JSONDecodeError:
                self._ssh_profiles = []
    
    def _save_ssh_profiles(self) -> None:
        """Save SSH profiles to config file."""
        self.SSH_PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "profiles": self._ssh_profiles
        }
        self.SSH_PROFILES_PATH.write_text(json.dumps(data, indent=2))
    
    def list_ssh_profiles(self) -> List[dict]:
        """
        List all saved SSH profiles.
        
        Returns:
            List of SSH profile dictionaries with id, name, host, user, port
        """
        return self._ssh_profiles.copy()
    
    def save_ssh_profile(self, profile: dict) -> str:
        """
        Save an SSH profile for quick reuse.
        
        Args:
            profile: Dict with name, host, user, port, key_path (optional)
            
        Returns:
            Generated profile ID
        """
        import uuid
        
        profile_id = str(uuid.uuid4())[:8]
        
        # Check for existing profile with same host+user
        for existing in self._ssh_profiles:
            if existing.get('host') == profile.get('host') and \
               existing.get('user') == profile.get('user'):
                # Update existing profile
                existing.update(profile)
                self._save_ssh_profiles()
                return existing.get('id', profile_id)
        
        # Add new profile
        self._ssh_profiles.append({
            'id': profile_id,
            'name': profile.get('name', f"{profile.get('user')}@{profile.get('host')}"),
            'host': profile.get('host'),
            'user': profile.get('user'),
            'port': profile.get('port', 22),
            'key_path': profile.get('key_path', ''),
        })
        self._save_ssh_profiles()
        return profile_id
    
    def get_ssh_profile(self, profile_id: str) -> Optional[dict]:
        """
        Get an SSH profile by ID.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            Profile dict or None if not found
        """
        for profile in self._ssh_profiles:
            if profile.get('id') == profile_id:
                return profile.copy()
        return None
    
    def delete_ssh_profile(self, profile_id: str) -> bool:
        """
        Delete an SSH profile.
        
        Args:
            profile_id: Profile identifier
            
        Returns:
            True if deleted, False if not found
        """
        for i, profile in enumerate(self._ssh_profiles):
            if profile.get('id') == profile_id:
                self._ssh_profiles.pop(i)
                self._save_ssh_profiles()
                return True
        return False
    
    def test_connection(self, project: Project) -> Tuple[bool, str]:
        """
        Test if we can connect to a project.
        
        Args:
            project: Project to test
            
        Returns:
            Tuple of (success, message)
        """
        try:
            fs = project.get_filesystem()
            # Try to list the root directory
            fs.ls(".")
            return True, "Connection successful"
        except NotImplementedError as e:
            return False, str(e)
        except FileNotFoundError:
            return False, f"Path not found: {project.path}"
        except PermissionError:
            return False, f"Permission denied: {project.path}"
        except Exception as e:
            return False, f"Connection failed: {e}"


class SessionIndex:
    """
    Tracks which project each session belongs to.
    
    Sessions can switch between projects, so we track both
    the original project (where session started) and current project.
    """
    
    SESSIONS_PATH = get_prism_dir() / "sessions.json"
    
    def __init__(self):
        """Initialize and load session index from disk."""
        self._sessions: Dict[str, dict] = {}
        self._load()
    
    def _load(self) -> None:
        """Load session index from file."""
        if self.SESSIONS_PATH.exists():
            try:
                data = json.loads(self.SESSIONS_PATH.read_text())
                self._sessions = data.get("sessions", {})
            except json.JSONDecodeError:
                self._sessions = {}
    
    def _save(self) -> None:
        """Save session index to file."""
        self.SESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "sessions": self._sessions
        }
        self.SESSIONS_PATH.write_text(json.dumps(data, indent=2))
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get info for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict with session info or None if not found
        """
        return self._sessions.get(session_id)
    
    def set_session_project(
        self,
        session_id: str,
        project_id: str,
        is_original: bool = False,
        title: Optional[str] = None
    ) -> None:
        """
        Set the project for a session.
        
        Args:
            session_id: Session identifier
            project_id: Project to associate
            is_original: If True, also sets as original project
            title: Optional session title
        """
        now = datetime.now().isoformat()
        
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "original_project_id": project_id,
                "current_project_id": project_id,
                "created_at": now,
                "last_accessed": now,
            }
        else:
            self._sessions[session_id]["current_project_id"] = project_id
            self._sessions[session_id]["last_accessed"] = now
            
            if is_original:
                self._sessions[session_id]["original_project_id"] = project_id
        
        if title:
            self._sessions[session_id]["title"] = title
        
        self._save()
    
    def get_sessions_for_project(
        self,
        project_id: str,
        by_current: bool = True
    ) -> List[str]:
        """
        Get all sessions for a project.
        
        Args:
            project_id: Project to filter by
            by_current: If True, filter by current_project_id,
                       otherwise filter by original_project_id
            
        Returns:
            List of session IDs
        """
        key = "current_project_id" if by_current else "original_project_id"
        return [
            sid for sid, info in self._sessions.items()
            if info.get(key) == project_id
        ]
    
    def get_current_project_id(self, session_id: str) -> Optional[str]:
        """
        Get the current project ID for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current project ID or None
        """
        info = self._sessions.get(session_id)
        return info.get("current_project_id") if info else None
    
    def get_original_project_id(self, session_id: str) -> Optional[str]:
        """
        Get the original project ID for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Original project ID or None
        """
        info = self._sessions.get(session_id)
        return info.get("original_project_id") if info else None
    
    def remove_session(self, session_id: str) -> bool:
        """
        Remove a session from the index.
        
        Args:
            session_id: Session to remove
            
        Returns:
            True if removed, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save()
            return True
        return False
