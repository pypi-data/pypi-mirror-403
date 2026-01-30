# Multi-Project & SSH Architecture

## Vision

Mobius becomes a **multi-project, multi-agent workspace** that can seamlessly work with:
- Local projects on your machine
- Remote projects via SSH (servers, VMs, cloud instances)

All from a single interface, with agents that can switch between projects mid-conversation, run in the background, and leverage your existing SSH configuration.

---

## Core Concepts

### 1. Project

A **Project** is a directory (local or remote) containing code you want to work on.

```python
@dataclass
class Project:
    id: str                          # Unique identifier (e.g., "mobius", "api-prod")
    name: str                        # Display name
    type: Literal["local", "ssh"]    # Connection type
    path: str                        # Root path on the filesystem
    color: str = "#ff6b2b"           # UI accent color
    
    # SSH-specific (only if type == "ssh")
    host: Optional[str] = None       # Hostname or SSH config alias
    user: Optional[str] = None       # Username (optional if in SSH config)
    port: int = 22                   # SSH port
    
    def get_filesystem(self) -> "FileSystem":
        """Get the appropriate filesystem for this project."""
        if self.type == "local":
            return LocalFileSystem(Path(self.path))
        else:
            return SSHFileSystem(
                host=self.host,
                user=self.user,
                port=self.port,
                root=self.path
            )
```

### 2. FileSystem Protocol

All file operations go through an abstract **FileSystem** interface, making tools agnostic to whether they're operating locally or over SSH.

```python
from typing import Protocol, Tuple, List

class FileSystem(Protocol):
    """Abstract filesystem interface - local or remote."""
    
    @property
    def root(self) -> str:
        """Project root path."""
        ...
    
    def read(self, path: str) -> str:
        """Read file contents."""
        ...
    
    def write(self, path: str, content: str) -> None:
        """Write content to file (creates parent dirs if needed)."""
        ...
    
    def delete(self, path: str) -> None:
        """Delete a file."""
        ...
    
    def rename(self, old_path: str, new_path: str) -> None:
        """Rename/move a file."""
        ...
    
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        ...
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        ...
    
    def is_dir(self, path: str) -> bool:
        """Check if path is a directory."""
        ...
    
    def ls(self, path: str = ".") -> List[dict]:
        """List directory contents with metadata."""
        ...
    
    def mkdir(self, path: str, parents: bool = True) -> None:
        """Create directory."""
        ...
    
    def exec(self, command: str, cwd: str = None, timeout: int = 120) -> Tuple[str, int]:
        """Execute shell command, return (output, exit_code)."""
        ...
    
    def walk(self, path: str = ".") -> Iterator[Tuple[str, List[str], List[str]]]:
        """Walk directory tree like os.walk."""
        ...
```

### 3. Session & Project Relationship

- **Sessions are tied to their originating project** but can switch to other projects
- **History entries are tagged** with which project they were executed in
- **Context flows across projects** - if you switch from Project A to Project B, the agent remembers what happened in A

```python
@dataclass
class Entry:
    id: str
    timestamp: str
    message: dict
    meta: dict  # Includes:
                #   project_id: str
                #   project_path: str
                #   project_type: "local" | "ssh"
```

---

## Implementation Details

### LocalFileSystem

Straightforward wrapper around Python's `pathlib` and `subprocess`:

```python
class LocalFileSystem:
    """Filesystem operations on local machine."""
    
    def __init__(self, root: Path):
        self._root = root.resolve()
    
    @property
    def root(self) -> str:
        return str(self._root)
    
    def _resolve(self, path: str) -> Path:
        """Resolve relative path to absolute, ensuring it's within root."""
        p = Path(path)
        if p.is_absolute():
            return p
        return self._root / path
    
    def read(self, path: str) -> str:
        return self._resolve(path).read_text(encoding='utf-8')
    
    def write(self, path: str, content: str) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
    
    def delete(self, path: str) -> None:
        self._resolve(path).unlink()
    
    def rename(self, old_path: str, new_path: str) -> None:
        old = self._resolve(old_path)
        new = self._resolve(new_path)
        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)
    
    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()
    
    def is_file(self, path: str) -> bool:
        return self._resolve(path).is_file()
    
    def is_dir(self, path: str) -> bool:
        return self._resolve(path).is_dir()
    
    def ls(self, path: str = ".") -> List[dict]:
        p = self._resolve(path)
        items = []
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            items.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0,
            })
        return items
    
    def mkdir(self, path: str, parents: bool = True) -> None:
        self._resolve(path).mkdir(parents=parents, exist_ok=True)
    
    def exec(self, command: str, cwd: str = None, timeout: int = 120) -> Tuple[str, int]:
        work_dir = self._resolve(cwd) if cwd else self._root
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=work_dir
        )
        output = result.stdout + result.stderr
        return output, result.returncode
    
    def walk(self, path: str = ".") -> Iterator[Tuple[str, List[str], List[str]]]:
        for root, dirs, files in os.walk(self._resolve(path)):
            yield root, dirs, files
```

### SSHFileSystem

Uses the system `ssh` command to leverage existing `~/.ssh/config`:

```python
class SSHFileSystem:
    """Filesystem operations over SSH using system ssh command.
    
    Leverages ~/.ssh/config for hosts, keys, and connection settings.
    This means any host configured for VS Code, git, etc. works automatically.
    """
    
    def __init__(self, host: str, root: str, user: str = None, port: int = 22):
        self.host = host
        self.user = user
        self.port = port
        self._root = root
        
        # Build SSH destination (user@host or just host if in config)
        if user:
            self._dest = f"{user}@{host}"
        else:
            self._dest = host
        
        # SSH command prefix with options
        self._ssh_opts = [
            "-o", "BatchMode=yes",           # Don't prompt for password
            "-o", "ConnectTimeout=10",       # Connection timeout
            "-o", "StrictHostKeyChecking=accept-new",  # Accept new hosts
        ]
        if port != 22:
            self._ssh_opts.extend(["-p", str(port)])
    
    @property
    def root(self) -> str:
        return self._root
    
    def _ssh_cmd(self, remote_command: str, timeout: int = 120) -> Tuple[str, int]:
        """Execute command over SSH."""
        cmd = ["ssh"] + self._ssh_opts + [self._dest, remote_command]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout + result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s", 1
    
    def _remote_path(self, path: str) -> str:
        """Convert relative path to absolute remote path."""
        if path.startswith("/"):
            return path
        return f"{self._root}/{path}"
    
    def read(self, path: str) -> str:
        output, code = self._ssh_cmd(f"cat '{self._remote_path(path)}'")
        if code != 0:
            raise FileNotFoundError(f"Failed to read {path}: {output}")
        return output
    
    def write(self, path: str, content: str) -> None:
        remote = self._remote_path(path)
        # Ensure parent directory exists
        parent = "/".join(remote.rsplit("/", 1)[:-1])
        if parent:
            self._ssh_cmd(f"mkdir -p '{parent}'")
        
        # Write via stdin to handle special characters
        cmd = ["ssh"] + self._ssh_opts + [self._dest, f"cat > '{remote}'"]
        result = subprocess.run(
            cmd,
            input=content,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise IOError(f"Failed to write {path}: {result.stderr}")
    
    def delete(self, path: str) -> None:
        output, code = self._ssh_cmd(f"rm '{self._remote_path(path)}'")
        if code != 0:
            raise FileNotFoundError(f"Failed to delete {path}: {output}")
    
    def rename(self, old_path: str, new_path: str) -> None:
        old_remote = self._remote_path(old_path)
        new_remote = self._remote_path(new_path)
        # Ensure parent of new path exists
        parent = "/".join(new_remote.rsplit("/", 1)[:-1])
        if parent:
            self._ssh_cmd(f"mkdir -p '{parent}'")
        output, code = self._ssh_cmd(f"mv '{old_remote}' '{new_remote}'")
        if code != 0:
            raise IOError(f"Failed to rename {old_path}: {output}")
    
    def exists(self, path: str) -> bool:
        _, code = self._ssh_cmd(f"test -e '{self._remote_path(path)}'")
        return code == 0
    
    def is_file(self, path: str) -> bool:
        _, code = self._ssh_cmd(f"test -f '{self._remote_path(path)}'")
        return code == 0
    
    def is_dir(self, path: str) -> bool:
        _, code = self._ssh_cmd(f"test -d '{self._remote_path(path)}'")
        return code == 0
    
    def ls(self, path: str = ".") -> List[dict]:
        remote = self._remote_path(path)
        # Use ls with specific format for parsing
        output, code = self._ssh_cmd(f"ls -la '{remote}' 2>/dev/null")
        if code != 0:
            raise FileNotFoundError(f"Directory not found: {path}")
        
        items = []
        for line in output.strip().split("\n")[1:]:  # Skip "total" line
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 9:
                name = " ".join(parts[8:])  # Handle spaces in names
                if name in (".", ".."):
                    continue
                items.append({
                    "name": name,
                    "is_dir": parts[0].startswith("d"),
                    "size": int(parts[4]) if parts[4].isdigit() else 0,
                })
        return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))
    
    def mkdir(self, path: str, parents: bool = True) -> None:
        flag = "-p" if parents else ""
        output, code = self._ssh_cmd(f"mkdir {flag} '{self._remote_path(path)}'")
        if code != 0:
            raise IOError(f"Failed to create directory {path}: {output}")
    
    def exec(self, command: str, cwd: str = None, timeout: int = 120) -> Tuple[str, int]:
        work_dir = self._remote_path(cwd) if cwd else self._root
        remote_cmd = f"cd '{work_dir}' && {command}"
        return self._ssh_cmd(remote_cmd, timeout)
    
    def walk(self, path: str = ".") -> Iterator[Tuple[str, List[str], List[str]]]:
        """Walk remote directory tree."""
        remote = self._remote_path(path)
        # Use find to get all files and directories
        output, code = self._ssh_cmd(
            f"find '{remote}' -type f -o -type d 2>/dev/null | sort"
        )
        if code != 0:
            return
        
        # Build tree structure
        tree = {}
        for line in output.strip().split("\n"):
            if not line:
                continue
            rel = os.path.relpath(line, remote)
            parts = rel.split("/")
            # ... (build tree and yield like os.walk)
```

### Connection Pooling (Optional Enhancement)

For better performance with many operations, we can add connection multiplexing:

```python
class SSHFileSystem:
    def __init__(self, ...):
        ...
        # Set up ControlMaster for connection reuse
        self._control_path = f"/tmp/mobius-ssh-{host}-{os.getpid()}"
        self._ssh_opts.extend([
            "-o", f"ControlPath={self._control_path}",
            "-o", "ControlMaster=auto",
            "-o", "ControlPersist=600",  # Keep connection for 10 min
        ])
    
    def close(self):
        """Close the persistent connection."""
        subprocess.run(
            ["ssh", "-O", "exit", "-o", f"ControlPath={self._control_path}", self._dest],
            capture_output=True
        )
```

---

## Tool Refactoring

### Current Tools (Path.cwd() based)

```python
# tools/tools.py - CURRENT
def read_file(file_path: str) -> str:
    p = Path(file_path)
    return p.read_text()

def bash(command: str, timeout: int = 120) -> str:
    result = subprocess.run(command, shell=True, cwd=Path.cwd(), ...)
    return result.stdout
```

### New Tools (FileSystem based)

```python
# tools/tools.py - NEW
from core.filesystem import get_current_filesystem

def read_file(file_path: str) -> str:
    """Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
    """
    fs = get_current_filesystem()
    try:
        return fs.read(file_path)
    except Exception as e:
        return f"Error: {e}"

def create_file(file_path: str, content: str) -> str:
    """Create a new file with the given content.
    
    Args:
        file_path: Path for the new file
        content: Content to write to the file
    """
    fs = get_current_filesystem()
    try:
        if fs.exists(file_path):
            return f"Error: File already exists: {file_path}"
        fs.write(file_path, content)
        return f"Created file: {file_path}"
    except Exception as e:
        return f"Error: {e}"

def edit_file(file_path: str, old_str: str, new_str: str, intent: str = "") -> str:
    """Replace text in a file using fuzzy matching.
    
    Args:
        file_path: Path to the file to edit
        old_str: The text to find and replace
        new_str: The replacement text
        intent: Brief description of the change (optional)
    """
    fs = get_current_filesystem()
    try:
        content = fs.read(file_path)
        # Use existing FileEditor logic for fuzzy matching
        result = _editor.str_replace_content(content, old_str, new_str)
        if result.success:
            fs.write(file_path, result.new_content)
        return result.message
    except Exception as e:
        return f"Error: {e}"

def bash(command: str, timeout: int = 120) -> str:
    """Execute a shell command.
    
    Args:
        command: The command to execute
        timeout: Maximum seconds to wait (default 120)
    
    Returns:
        Command output (stdout + stderr)
    """
    fs = get_current_filesystem()
    try:
        output, code = fs.exec(command, timeout=timeout)
        if code != 0:
            return f"[Exit code: {code}]\n{output}"
        return output or "(no output)"
    except Exception as e:
        return f"Error: {e}"
```

### Getting Current FileSystem

```python
# core/filesystem.py

from core.signella import Signella

_store = Signella()
_filesystems: Dict[str, FileSystem] = {}

def get_current_filesystem() -> FileSystem:
    """Get filesystem for the current project context."""
    session_id = _store.get('session', 'current', default='default')
    project_id = _store.get('session', session_id, 'project_id', default='local')
    
    if project_id not in _filesystems:
        project = get_project(project_id)
        _filesystems[project_id] = project.get_filesystem()
    
    return _filesystems[project_id]

def set_current_project(session_id: str, project_id: str):
    """Switch the current project for a session."""
    _store.set('session', session_id, 'project_id', project_id)
    # Clear cached filesystem to force refresh
    if project_id in _filesystems:
        old_fs = _filesystems.pop(project_id)
        if hasattr(old_fs, 'close'):
            old_fs.close()
```

---

## Prism Over SSH

### Challenge

Prism needs to scan many files to build the dependency graph. Over SSH, this could be slow.

### Solution: Cached Graph with Incremental Updates

```python
class RemotePrismSession:
    """Prism session for remote projects with caching."""
    
    def __init__(self, project: Project):
        self.project = project
        self.fs = project.get_filesystem()
        self.cache_path = Path.home() / ".mobius" / "prism_cache" / f"{project.id}.json"
        self._graph = None
    
    def scan(self, force: bool = False) -> dict:
        """Scan project, using cache if available."""
        
        # Check if cache exists and is fresh
        if not force and self.cache_path.exists():
            cache_age = time.time() - self.cache_path.stat().st_mtime
            if cache_age < 3600:  # Cache valid for 1 hour
                return self._load_cache()
        
        # Full scan - batch file discovery
        files = self._discover_files()
        
        # Batch read files (minimize SSH round-trips)
        contents = self._batch_read(files)
        
        # Build graph locally
        self._graph = self._build_graph(files, contents)
        
        # Cache results
        self._save_cache()
        
        return self._graph.stats()
    
    def _discover_files(self) -> List[str]:
        """Find all relevant files using single SSH command."""
        cmd = """
        find . -type f \( -name "*.py" -o -name "*.html" -o -name "*.js" -o -name "*.css" \) \
            -not -path "*/.venv/*" \
            -not -path "*/__pycache__/*" \
            -not -path "*/node_modules/*" \
            2>/dev/null
        """
        output, _ = self.fs.exec(cmd)
        return [f.strip() for f in output.strip().split("\n") if f.strip()]
    
    def _batch_read(self, files: List[str]) -> Dict[str, str]:
        """Read multiple files in batched SSH commands."""
        contents = {}
        
        # Read in batches of 50 files
        batch_size = 50
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            
            # Create a tar archive and extract contents
            file_list = " ".join(f"'{f}'" for f in batch)
            cmd = f"tar -cf - {file_list} 2>/dev/null | base64"
            output, code = self.fs.exec(cmd)
            
            if code == 0:
                # Decode and extract
                import tarfile
                import base64
                import io
                
                tar_data = base64.b64decode(output)
                tar = tarfile.open(fileobj=io.BytesIO(tar_data))
                for member in tar.getmembers():
                    if member.isfile():
                        f = tar.extractfile(member)
                        contents[member.name] = f.read().decode('utf-8', errors='ignore')
        
        return contents
```

---

## Project Management

### Storage

```
~/.mobius/
├── config.json            # Global settings
├── projects.json          # Project registry
├── sessions.json          # Session index (maps sessions to projects)
├── histories/
│   └── {session_id}.gt.json
└── prism_cache/
    └── {project_id}.json  # Cached dependency graphs
```

### sessions.json Schema

The session index tracks which project each session belongs to, supporting project switches mid-session:

```json
{
  "version": 1,
  "sessions": {
    "20250123_abc123": {
      "original_project_id": "mobius",
      "current_project_id": "mobius",
      "title": "Refactoring tools layer",
      "created_at": "2025-01-23T10:00:00Z",
      "last_accessed": "2025-01-23T14:30:00Z"
    },
    "20250123_def456": {
      "original_project_id": "mobius",
      "current_project_id": "api-server",
      "title": "Connect frontend to API",
      "created_at": "2025-01-23T11:00:00Z",
      "last_accessed": "2025-01-23T15:45:00Z"
    },
    "20250122_xyz789": {
      "original_project_id": "api-server",
      "current_project_id": "api-server",
      "title": "Fix authentication bug",
      "created_at": "2025-01-22T09:00:00Z",
      "last_accessed": "2025-01-22T16:20:00Z"
    }
  }
}
```

This enables:
- **List by original project**: "Sessions started in Mobius" → abc123, def456
- **List by current project**: "Sessions currently on api-server" → def456, xyz789
- **Track journey**: Session def456 started in mobius, now working on api-server

### projects.json Schema

```json
{
  "version": 1,
  "projects": [
    {
      "id": "mobius",
      "name": "Mobius",
      "type": "local",
      "path": "/Users/offbeat/mobius",
      "color": "#ff6b2b",
      "created_at": "2025-01-23T12:00:00Z",
      "last_accessed": "2025-01-23T14:30:00Z"
    },
    {
      "id": "prod-api",
      "name": "Production API",
      "type": "ssh",
      "host": "api.example.com",
      "user": "deploy",
      "port": 22,
      "path": "/var/www/api",
      "color": "#3b82f6",
      "created_at": "2025-01-20T10:00:00Z",
      "last_accessed": "2025-01-23T09:15:00Z"
    },
    {
      "id": "ml-gpu",
      "name": "ML Training Box",
      "type": "ssh",
      "host": "ml-server",
      "path": "/home/ubuntu/training",
      "color": "#10b981",
      "created_at": "2025-01-15T08:00:00Z",
      "last_accessed": "2025-01-22T16:45:00Z"
    }
  ],
  "default_project": "mobius"
}
```

Note: `host: "ml-server"` uses the alias from `~/.ssh/config`, inheriting user, key, port, etc.

### Project Manager Class

```python
class ProjectManager:
    """Manages project configurations."""
    
    CONFIG_PATH = Path.home() / ".mobius" / "projects.json"
    
    def __init__(self):
        self._projects: Dict[str, Project] = {}
        self._load()
    
    def _load(self):
        """Load projects from config file."""
        if self.CONFIG_PATH.exists():
            data = json.loads(self.CONFIG_PATH.read_text())
            for p in data.get("projects", []):
                project = Project(**p)
                self._projects[project.id] = project
    
    def _save(self):
        """Save projects to config file."""
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "projects": [p.__dict__ for p in self._projects.values()]
        }
        self.CONFIG_PATH.write_text(json.dumps(data, indent=2, default=str))
    
    def list(self) -> List[Project]:
        """List all projects."""
        return list(self._projects.values())
    
    def get(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self._projects.get(project_id)
    
    def add(self, project: Project) -> None:
        """Add a new project."""
        self._projects[project.id] = project
        self._save()
    
    def remove(self, project_id: str) -> bool:
        """Remove a project."""
        if project_id in self._projects:
            del self._projects[project_id]
            self._save()
            return True
        return False
    
    def test_connection(self, project: Project) -> Tuple[bool, str]:
        """Test if we can connect to a project."""
        try:
            fs = project.get_filesystem()
            fs.ls(".")
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
```

---

## API Endpoints

```python
# run_web.py additions

@app.route('/api/projects')
def api_projects():
    """List all configured projects."""
    pm = ProjectManager()
    session_id = get_current_session_id()
    current_project_id = _store.get('session', session_id, 'project_id', default='local')
    
    return jsonify({
        "projects": [p.__dict__ for p in pm.list()],
        "current": current_project_id
    })

@app.route('/api/projects/add', methods=['POST'])
def api_add_project():
    """Add a new project."""
    data = request.json
    pm = ProjectManager()
    
    project = Project(
        id=data['id'],
        name=data['name'],
        type=data['type'],
        path=data['path'],
        color=data.get('color', '#ff6b2b'),
        host=data.get('host'),
        user=data.get('user'),
        port=data.get('port', 22),
    )
    
    # Test connection first
    success, message = pm.test_connection(project)
    if not success:
        return jsonify({"error": f"Connection failed: {message}"}), 400
    
    pm.add(project)
    return jsonify({"success": True, "project": project.__dict__})

@app.route('/api/projects/switch', methods=['POST'])
def api_switch_project():
    """Switch current session to a different project."""
    data = request.json
    project_id = data['project_id']
    
    pm = ProjectManager()
    project = pm.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    session_id = get_current_session_id()
    set_current_project(session_id, project_id)
    
    # Notify agent of project switch
    agent = get_agent()
    agent.switch_project(project)
    
    return jsonify({
        "success": True,
        "project": project.__dict__
    })

@app.route('/api/projects/test', methods=['POST'])
def api_test_project():
    """Test connection to a project."""
    data = request.json
    project = Project(**data)
    
    pm = ProjectManager()
    success, message = pm.test_connection(project)
    
    return jsonify({
        "success": success,
        "message": message
    })
```

---

## Agent Integration

### Agent with Project Context

```python
class Agent:
    def __init__(
        self,
        system_prompt: str,
        tools: List[Callable] = None,
        model: str = "gpt-4o-mini",
        session_id: Optional[str] = None,
        project: Optional[Project] = None,
    ):
        # ... existing init ...
        
        self.project = project or self._get_default_project()
        self._filesystem = self.project.get_filesystem()
        
        # Store project in Signella
        _store.set('session', self.history.session_id, 'project_id', self.project.id)
    
    def switch_project(self, project: Project):
        """Switch to a different project mid-session."""
        old_project = self.project
        self.project = project
        self._filesystem = project.get_filesystem()
        
        # Update Signella
        _store.set('session', self.history.session_id, 'project_id', project.id)
        
        # Log the switch in history
        self.history_manager.add_system(
            f"Switched project: {old_project.name} → {project.name}\n"
            f"New root: {project.path}"
        )
        
        # Clear focus (files from old project won't exist in new)
        _store.set('focus', self.history.session_id, 'files', [])
        
        # Rescan Prism if available
        global _session
        _session = None  # Force rescan on next prism tool use
    
    def _build_hud(self) -> str:
        """Build HUD with project context."""
        hud = f"# Project: {self.project.name}\n"
        hud += f"Type: {self.project.type}\n"
        hud += f"Root: {self.project.path}\n"
        if self.project.type == "ssh":
            hud += f"Host: {self.project.host}\n"
        hud += "\n"
        
        # ... rest of HUD building using self._filesystem ...
```

---

## UI Integration

### Project Switcher Component

```javascript
// static/workspace/js/components/project-switcher.js

class ProjectSwitcher extends MobiusComponent {
    async loadProjects() {
        const res = await fetch('/api/projects');
        const data = await res.json();
        this.projects = data.projects;
        this.currentProject = data.current;
        this.render();
    }
    
    async switchProject(projectId) {
        const res = await fetch('/api/projects/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: projectId })
        });
        
        if (res.ok) {
            this.currentProject = projectId;
            this.render();
            
            // Update UI accent color
            const project = this.projects.find(p => p.id === projectId);
            document.documentElement.style.setProperty('--project-color', project.color);
            
            // Emit event for other components
            bus.emit('project-switched', { project });
        }
    }
    
    render() {
        this.innerHTML = `
            <div class="project-switcher">
                <div class="current-project" style="--project-color: ${this.getCurrentColor()}">
                    <span class="project-dot"></span>
                    <span class="project-name">${this.getCurrentName()}</span>
                    <span class="project-type">${this.getCurrentType()}</span>
                </div>
                <div class="project-list hidden">
                    ${this.projects.map(p => `
                        <div class="project-item ${p.id === this.currentProject ? 'active' : ''}"
                             data-id="${p.id}"
                             style="--project-color: ${p.color}">
                            <span class="project-dot"></span>
                            <span class="project-name">${p.name}</span>
                            <span class="project-type">${p.type}</span>
                            ${p.type === 'ssh' ? `<span class="project-host">${p.host}</span>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
}
```

### CSS for Project Colors

```css
/* static/workspace/css/variables.css */

:root {
    --project-color: #ff6b2b;  /* Default/fallback */
}

/* Dynamic project theming */
.project-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--project-color);
}

.sidebar {
    border-left: 3px solid var(--project-color);
}

.toolbar-project {
    background: color-mix(in srgb, var(--project-color) 15%, transparent);
    border: 1px solid var(--project-color);
    color: var(--project-color);
}

/* SSH indicator */
.project-type.ssh::before {
    content: "⚡";
    margin-right: 4px;
}
```

---

## Background Agents

For agents that continue running after browser disconnect:

```python
class AgentRunner:
    """Manages background agent execution."""
    
    def __init__(self):
        self._threads: Dict[str, Thread] = {}
        self._queues: Dict[str, Queue] = {}  # Message queues for each session
        self._results: Dict[str, List] = {}  # Accumulated results while disconnected
    
    def start_background(self, session_id: str, message: str):
        """Start processing a message in background."""
        if session_id in self._threads and self._threads[session_id].is_alive():
            # Already running, queue the message
            self._queues[session_id].put(message)
            return
        
        self._queues[session_id] = Queue()
        self._results[session_id] = []
        
        thread = Thread(target=self._run_agent, args=(session_id, message))
        thread.daemon = True
        thread.start()
        self._threads[session_id] = thread
    
    def _run_agent(self, session_id: str, initial_message: str):
        """Run agent in background thread."""
        agent = get_agent_for_session(session_id)
        
        # Process initial message
        for event in agent.stream(initial_message):
            self._results[session_id].append(event)
        
        # Process any queued messages
        while not self._queues[session_id].empty():
            message = self._queues[session_id].get()
            for event in agent.stream(message):
                self._results[session_id].append(event)
    
    def get_pending_results(self, session_id: str) -> List:
        """Get results accumulated while client was disconnected."""
        results = self._results.get(session_id, [])
        self._results[session_id] = []  # Clear after retrieval
        return results
    
    def is_running(self, session_id: str) -> bool:
        """Check if agent is currently processing."""
        return session_id in self._threads and self._threads[session_id].is_alive()
```

---

## Implementation Phases

### Phase 1: FileSystem Abstraction (Foundation)
- [ ] Create `FileSystem` protocol in `core/filesystem.py`
- [ ] Implement `LocalFileSystem`
- [ ] Refactor `tools/tools.py` to use FileSystem
- [ ] Add `get_current_filesystem()` with Signella integration
- [ ] Test all existing functionality still works

### Phase 2: Project Management
- [ ] Create `Project` dataclass
- [ ] Implement `ProjectManager` with JSON storage
- [ ] Add API endpoints for project CRUD
- [ ] Update Agent to accept project context
- [ ] Add project switching capability

### Phase 3: SSH Support
- [ ] Implement `SSHFileSystem`
- [ ] Add connection testing endpoint
- [ ] Handle SSH errors gracefully
- [ ] Add connection pooling (ControlMaster)
- [ ] Test with real SSH hosts

### Phase 4: Prism Over SSH
- [ ] Create `RemotePrismSession` with caching
- [ ] Implement batched file reading
- [ ] Add cache invalidation logic
- [ ] Test dependency scanning over SSH

### Phase 5: UI Integration
- [ ] Add project switcher to workspace UI
- [ ] Implement dynamic color theming
- [ ] Add project management modal
- [ ] Show connection status indicators
- [ ] Add SSH host configuration UI

### Phase 6: Background Agents
- [ ] Implement `AgentRunner`
- [ ] Add message queuing
- [ ] Handle reconnection and result retrieval
- [ ] Add status indicators in UI
- [ ] Test concurrent agents

---

## Security Considerations

1. **SSH Keys**: Use existing `~/.ssh/` keys, never copy or store keys in Mobius
2. **Host Verification**: Use `StrictHostKeyChecking=accept-new` to accept new hosts but reject changed keys
3. **Command Injection**: Always quote paths in SSH commands
4. **Timeouts**: Enforce timeouts on all SSH operations
5. **Connection Limits**: Limit concurrent SSH connections per host

---

## Future Enhancements

1. **Remote Agent Mode**: Run a lightweight Mobius agent on remote host for faster operations
2. **File Sync**: Selective sync of files for offline editing
3. **Tunnel Support**: SSH tunneling for accessing services on remote hosts
4. **Container Support**: Connect to Docker containers via `docker exec`
5. **Cloud Integration**: Direct AWS/GCP/Azure VM connections
