"""
FileSystem abstraction layer for local and remote file operations.

This module provides a unified interface for file operations that works
identically whether operating on local files or remote files over SSH.
All tools use this abstraction, making them project-agnostic.

Thread-Local Context:
    When an Agent runs, it sets a thread-local filesystem context that tools
    use. This prevents project switching in one tab from affecting running
    agents in other tabs. The context is set via set_thread_filesystem() and
    read via get_current_filesystem().
"""
import os
import subprocess
import threading
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Protocol, Tuple

from .signella import Signella


# Shared Signella store for session/project state
_store = Signella()

# Cache of filesystem instances by project ID
_filesystems: Dict[str, "FileSystem"] = {}

# Thread-local storage for per-agent filesystem context
# This ensures each running agent uses its own project's filesystem,
# even when the user switches projects in the UI
_thread_local = threading.local()


class FileSystem(Protocol):
    """
    Abstract filesystem interface - local or remote.
    
    All file operations in Prism go through this interface,
    enabling seamless switching between local and SSH projects.
    """
    
    @property
    def root(self) -> str:
        """Project root path."""
        ...
    
    def read(self, path: str) -> str:
        """
        Read file contents.
        
        Args:
            path: Relative or absolute path to file
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        ...
    
    def write(self, path: str, content: str) -> None:
        """
        Write content to file (creates parent dirs if needed).
        
        Args:
            path: Relative or absolute path to file
            content: Content to write
            
        Raises:
            IOError: If file cannot be written
        """
        ...
    
    def delete(self, path: str) -> None:
        """
        Delete a file.
        
        Args:
            path: Relative or absolute path to file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be deleted
        """
        ...
    
    def rename(self, old_path: str, new_path: str) -> None:
        """
        Rename/move a file.
        
        Args:
            old_path: Current path of the file
            new_path: New path for the file
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            IOError: If rename fails
        """
        ...
    
    def exists(self, path: str) -> bool:
        """
        Check if path exists.
        
        Args:
            path: Relative or absolute path
            
        Returns:
            True if path exists, False otherwise
        """
        ...
    
    def is_file(self, path: str) -> bool:
        """
        Check if path is a file.
        
        Args:
            path: Relative or absolute path
            
        Returns:
            True if path is a file, False otherwise
        """
        ...
    
    def is_dir(self, path: str) -> bool:
        """
        Check if path is a directory.
        
        Args:
            path: Relative or absolute path
            
        Returns:
            True if path is a directory, False otherwise
        """
        ...
    
    def ls(self, path: str = ".") -> List[dict]:
        """
        List directory contents with metadata.
        
        Args:
            path: Directory path to list
            
        Returns:
            List of dicts with keys: name, is_dir, size
            
        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        ...
    
    def mkdir(self, path: str, parents: bool = True) -> None:
        """
        Create directory.
        
        Args:
            path: Directory path to create
            parents: If True, create parent directories as needed
            
        Raises:
            IOError: If directory cannot be created
        """
        ...
    
    def exec(self, command: str, cwd: str = None, timeout: int = 120) -> Tuple[str, int]:
        """
        Execute shell command.
        
        Args:
            command: Shell command to execute
            cwd: Working directory (defaults to project root)
            timeout: Maximum seconds to wait
            
        Returns:
            Tuple of (output, exit_code)
        """
        ...
    
    def walk(self, path: str = ".") -> Iterator[Tuple[str, List[str], List[str]]]:
        """
        Walk directory tree like os.walk.
        
        Args:
            path: Starting directory
            
        Yields:
            Tuples of (dirpath, dirnames, filenames)
        """
        ...
    
    def absolute(self, path: str) -> str:
        """
        Get absolute path for a file.
        
        Args:
            path: Relative or absolute path
            
        Returns:
            Absolute path as string
        """
        ...


class SSHConnectionError(Exception):
    """Cannot connect to SSH host."""
    pass


class SSHAuthenticationError(Exception):
    """SSH authentication failed."""
    pass


class SSHTimeoutError(Exception):
    """SSH operation timed out."""
    pass


class SSHFileSystem:
    """
    Filesystem operations over SSH using system ssh command.
    
    Leverages ~/.ssh/config for hosts, keys, and connection settings.
    This means any host configured for VS Code, git, etc. works automatically.
    Uses ControlMaster for connection pooling to minimize SSH overhead.
    """
    
    def __init__(self, host: str, root: str, user: Optional[str] = None, port: int = 22):
        """
        Initialize SSH filesystem.
        
        Args:
            host: SSH hostname or config alias from ~/.ssh/config
            root: Remote project root path
            user: SSH username (optional if defined in SSH config)
            port: SSH port (default 22)
        """
        self.host = host
        self.user = user
        self.port = port
        self._root = root
        
        # Build SSH destination (user@host or just host if in config)
        if user:
            self._dest = f"{user}@{host}"
        else:
            self._dest = host
        
        # Generate unique control path for connection pooling
        self._control_path = f"/tmp/prism-ssh-{host}-{os.getpid()}"
        
        # SSH command options
        self._ssh_opts = [
            "-o", "BatchMode=yes",                    # Don't prompt for password
            "-o", "ConnectTimeout=10",                # Connection timeout
            "-o", "StrictHostKeyChecking=accept-new", # Accept new hosts
            "-o", f"ControlPath={self._control_path}",
            "-o", "ControlMaster=auto",
            "-o", "ControlPersist=600",               # Keep connection for 10 min
        ]
        if port != 22:
            self._ssh_opts.extend(["-p", str(port)])
    
    @property
    def root(self) -> str:
        """Project root path on remote."""
        return self._root
    
    def _remote_path(self, path: str) -> str:
        """
        Convert relative path to absolute remote path.
        
        Args:
            path: Relative or absolute path
            
        Returns:
            Absolute path on remote system
        """
        if path.startswith("/"):
            return path
        # Handle "." specially
        if path == ".":
            return self._root
        return f"{self._root}/{path}"
    
    def _ssh_cmd(self, remote_command: str, timeout: int = 120) -> Tuple[str, int]:
        """
        Execute command over SSH.
        
        Args:
            remote_command: Command to run on remote host
            timeout: Maximum seconds to wait
            
        Returns:
            Tuple of (stdout+stderr, exit_code)
        """
        cmd = ["ssh"] + self._ssh_opts + [self._dest, remote_command]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout
            if result.stderr:
                # Append stderr but filter out common SSH noise
                stderr_lines = [
                    line for line in result.stderr.split('\n')
                    if line and not line.startswith('Warning:')
                ]
                if stderr_lines:
                    if output:
                        output += "\n"
                    output += "\n".join(stderr_lines)
            return output, result.returncode
        except subprocess.TimeoutExpired:
            raise SSHTimeoutError(f"Command timed out after {timeout}s: {remote_command[:50]}...")
        except Exception as e:
            raise SSHConnectionError(f"SSH command failed: {e}")
    
    def _parse_ssh_error(self, output: str, code: int) -> Exception:
        """
        Parse SSH error output and return appropriate exception.
        
        Args:
            output: Command output (stdout+stderr)
            code: Exit code
            
        Returns:
            Appropriate exception based on error type
        """
        lower_output = output.lower()
        
        if "permission denied" in lower_output:
            if "publickey" in lower_output:
                return SSHAuthenticationError(f"SSH authentication failed: {output}")
            return PermissionError(output)
        
        if "no such file or directory" in lower_output:
            return FileNotFoundError(output)
        
        if "connection refused" in lower_output or "connection timed out" in lower_output:
            return SSHConnectionError(f"Cannot connect to {self.host}: {output}")
        
        if "host key verification failed" in lower_output:
            return SSHConnectionError(f"Host key verification failed for {self.host}")
        
        return IOError(f"SSH command failed (exit {code}): {output}")
    
    def read(self, path: str) -> str:
        """Read file contents from remote."""
        remote = self._remote_path(path)
        output, code = self._ssh_cmd(f"cat '{remote}'")
        if code != 0:
            raise self._parse_ssh_error(output, code)
        return output
    
    def write(self, path: str, content: str) -> None:
        """Write content to remote file."""
        remote = self._remote_path(path)
        
        # Ensure parent directory exists
        parent = "/".join(remote.rsplit("/", 1)[:-1])
        if parent:
            self._ssh_cmd(f"mkdir -p '{parent}'")
        
        # Write via stdin to handle special characters safely
        cmd = ["ssh"] + self._ssh_opts + [self._dest, f"cat > '{remote}'"]
        try:
            result = subprocess.run(
                cmd,
                input=content,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                raise self._parse_ssh_error(result.stderr, result.returncode)
        except subprocess.TimeoutExpired:
            raise SSHTimeoutError(f"Write timed out for {path}")
    
    def delete(self, path: str) -> None:
        """Delete a remote file."""
        remote = self._remote_path(path)
        output, code = self._ssh_cmd(f"rm '{remote}'")
        if code != 0:
            raise self._parse_ssh_error(output, code)
    
    def rename(self, old_path: str, new_path: str) -> None:
        """Rename/move a remote file."""
        old_remote = self._remote_path(old_path)
        new_remote = self._remote_path(new_path)
        
        # Ensure parent of new path exists
        parent = "/".join(new_remote.rsplit("/", 1)[:-1])
        if parent:
            self._ssh_cmd(f"mkdir -p '{parent}'")
        
        output, code = self._ssh_cmd(f"mv '{old_remote}' '{new_remote}'")
        if code != 0:
            raise self._parse_ssh_error(output, code)
    
    def exists(self, path: str) -> bool:
        """Check if remote path exists."""
        remote = self._remote_path(path)
        _, code = self._ssh_cmd(f"test -e '{remote}'")
        return code == 0
    
    def is_file(self, path: str) -> bool:
        """Check if remote path is a file."""
        remote = self._remote_path(path)
        _, code = self._ssh_cmd(f"test -f '{remote}'")
        return code == 0
    
    def is_dir(self, path: str) -> bool:
        """Check if remote path is a directory."""
        remote = self._remote_path(path)
        _, code = self._ssh_cmd(f"test -d '{remote}'")
        return code == 0
    
    def ls(self, path: str = ".") -> List[dict]:
        """List remote directory contents with metadata."""
        remote = self._remote_path(path)
        
        # Use ls -la for detailed output
        output, code = self._ssh_cmd(f"ls -la '{remote}' 2>/dev/null")
        if code != 0:
            raise FileNotFoundError(f"Directory not found: {path}")
        
        items = []
        for line in output.strip().split("\n"):
            if not line.strip():
                continue
            # Skip the "total" line
            if line.startswith("total "):
                continue
            
            parts = line.split()
            if len(parts) >= 9:
                # Handle filenames with spaces
                name = " ".join(parts[8:])
                if name in (".", ".."):
                    continue
                
                # Parse size (5th column)
                try:
                    size = int(parts[4])
                except ValueError:
                    size = 0
                
                items.append({
                    "name": name,
                    "is_dir": parts[0].startswith("d"),
                    "size": size,
                })
        
        # Sort: directories first, then by name
        return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))
    
    def mkdir(self, path: str, parents: bool = True) -> None:
        """Create remote directory."""
        remote = self._remote_path(path)
        flag = "-p" if parents else ""
        output, code = self._ssh_cmd(f"mkdir {flag} '{remote}'")
        if code != 0:
            raise self._parse_ssh_error(output, code)
    
    def exec(self, command: str, cwd: str = None, timeout: int = 120) -> Tuple[str, int]:
        """Execute shell command on remote."""
        work_dir = self._remote_path(cwd) if cwd else self._root
        remote_cmd = f"cd '{work_dir}' && {command}"
        return self._ssh_cmd(remote_cmd, timeout)
    
    def absolute(self, path: str) -> str:
        """Get absolute path on remote filesystem."""
        return self._remote_path(path)
    
    def walk(self, path: str = ".") -> Iterator[Tuple[str, List[str], List[str]]]:
        """
        Walk remote directory tree like os.walk.
        
        Note: This is less efficient over SSH - consider using for small trees only.
        """
        remote = self._remote_path(path)
        
        # Use find to get directory structure
        output, code = self._ssh_cmd(
            f"find '{remote}' -maxdepth 10 \\( -type f -o -type d \\) 2>/dev/null | sort"
        )
        if code != 0:
            return
        
        # Build directory tree
        dirs_contents: Dict[str, Tuple[List[str], List[str]]] = {}
        
        for line in output.strip().split("\n"):
            if not line:
                continue
            
            # Get path relative to start
            if line == remote:
                rel_path = "."
            elif line.startswith(remote + "/"):
                rel_path = line[len(remote) + 1:]
            else:
                continue
            
            # Determine parent directory
            if "/" in rel_path:
                parent = "/".join(rel_path.rsplit("/", 1)[:-1])
                name = rel_path.rsplit("/", 1)[-1]
            else:
                parent = "."
                name = rel_path
            
            # Skip the root itself
            if rel_path == ".":
                if "." not in dirs_contents:
                    dirs_contents["."] = ([], [])
                continue
            
            # Initialize parent if needed
            if parent not in dirs_contents:
                dirs_contents[parent] = ([], [])
            
            # Check if it's a directory (ends with / in find output or has children)
            # We need to check with test -d
            full_path = f"{remote}/{rel_path}" if rel_path != "." else remote
            _, is_dir_code = self._ssh_cmd(f"test -d '{full_path}'")
            
            if is_dir_code == 0:
                dirs_contents[parent][0].append(name)
                if rel_path not in dirs_contents:
                    dirs_contents[rel_path] = ([], [])
            else:
                dirs_contents[parent][1].append(name)
        
        # Yield in order (parent before children)
        def yield_dir(dir_path: str, prefix: str):
            if dir_path in dirs_contents:
                dirs, files = dirs_contents[dir_path]
                full_dir = f"{prefix}/{dir_path}" if dir_path != "." else prefix
                yield (full_dir, dirs, files)
                for subdir in sorted(dirs):
                    sub_path = f"{dir_path}/{subdir}" if dir_path != "." else subdir
                    yield from yield_dir(sub_path, prefix)
        
        yield from yield_dir(".", remote)
    
    def close(self) -> None:
        """Close the persistent SSH connection."""
        try:
            subprocess.run(
                ["ssh", "-O", "exit", "-o", f"ControlPath={self._control_path}", self._dest],
                capture_output=True,
                timeout=5
            )
        except Exception:
            pass  # Best effort cleanup
        
        # Clean up control socket file if it exists
        try:
            control_socket = Path(self._control_path)
            if control_socket.exists():
                control_socket.unlink()
        except Exception:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class LocalFileSystem:
    """
    Filesystem operations on local machine.
    
    Wraps Python's pathlib and subprocess for local file operations.
    All paths are resolved relative to the project root.
    """
    
    def __init__(self, root: Path):
        """
        Initialize local filesystem.
        
        Args:
            root: Project root directory
        """
        self._root = root.resolve()
    
    @property
    def root(self) -> str:
        """Project root path."""
        return str(self._root)
    
    def _resolve(self, path: str) -> Path:
        """
        Resolve relative path to absolute, ensuring it's within root.
        
        Args:
            path: Relative or absolute path
            
        Returns:
            Resolved absolute path
        """
        p = Path(path)
        if p.is_absolute():
            return p
        return self._root / path
    
    def read(self, path: str) -> str:
        """Read file contents."""
        resolved = self._resolve(path)
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not resolved.is_file():
            raise IOError(f"Not a file: {path}")
        return resolved.read_text(encoding='utf-8')
    
    def write(self, path: str, content: str) -> None:
        """Write content to file."""
        resolved = self._resolve(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding='utf-8')
    
    def delete(self, path: str) -> None:
        """Delete a file."""
        resolved = self._resolve(path)
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if resolved.is_dir():
            raise IOError(f"Cannot delete directory with delete(), use rmdir: {path}")
        resolved.unlink()
    
    def rename(self, old_path: str, new_path: str) -> None:
        """Rename/move a file."""
        old_resolved = self._resolve(old_path)
        new_resolved = self._resolve(new_path)
        
        if not old_resolved.exists():
            raise FileNotFoundError(f"File not found: {old_path}")
        
        new_resolved.parent.mkdir(parents=True, exist_ok=True)
        old_resolved.rename(new_resolved)
    
    def exists(self, path: str) -> bool:
        """Check if path exists."""
        return self._resolve(path).exists()
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        return self._resolve(path).is_file()
    
    def is_dir(self, path: str) -> bool:
        """Check if path is a directory."""
        return self._resolve(path).is_dir()
    
    def ls(self, path: str = ".") -> List[dict]:
        """List directory contents with metadata."""
        resolved = self._resolve(path)
        
        if not resolved.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not resolved.is_dir():
            raise IOError(f"Not a directory: {path}")
        
        items = []
        for item in sorted(resolved.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            items.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0,
            })
        return items
    
    def mkdir(self, path: str, parents: bool = True) -> None:
        """Create directory."""
        resolved = self._resolve(path)
        resolved.mkdir(parents=parents, exist_ok=True)
    
    def exec(self, command: str, cwd: str = None, timeout: int = 120) -> Tuple[str, int]:
        """Execute shell command."""
        work_dir = self._resolve(cwd) if cwd else self._root
        
        try:
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
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s", 1
    
    def walk(self, path: str = ".") -> Iterator[Tuple[str, List[str], List[str]]]:
        """Walk directory tree like os.walk."""
        resolved = self._resolve(path)
        for root, dirs, files in os.walk(resolved):
            yield root, dirs, files
    
    def absolute(self, path: str) -> str:
        """Get absolute path on local filesystem."""
        return str(self._resolve(path))


# Default filesystem instance (for backward compatibility during transition)
_default_filesystem: Optional[LocalFileSystem] = None


def set_thread_filesystem(fs: "FileSystem") -> None:
    """
    Set the filesystem for the current thread.
    
    Called by Agent before executing tools to ensure all tool operations
    use the agent's project filesystem, regardless of UI project switches.
    
    Args:
        fs: FileSystem instance to use for this thread
    """
    _thread_local.filesystem = fs


def get_thread_filesystem() -> Optional["FileSystem"]:
    """
    Get the filesystem bound to the current thread, if any.
    
    Returns:
        FileSystem if set via set_thread_filesystem(), None otherwise
    """
    return getattr(_thread_local, 'filesystem', None)


def clear_thread_filesystem() -> None:
    """
    Clear the thread-local filesystem binding.
    
    Called after agent completes to clean up thread state.
    """
    if hasattr(_thread_local, 'filesystem'):
        del _thread_local.filesystem


def get_current_filesystem() -> FileSystem:
    """
    Get filesystem for the current context.
    
    Priority:
    1. Thread-local filesystem (set by running Agent) - PREFERRED
    2. Signella-based lookup (fallback for non-agent contexts)
    
    This ensures running agents always use their bound project's filesystem,
    even when the user switches projects in the UI.
    
    Returns:
        FileSystem instance for current context
    """
    # Priority 1: Thread-local filesystem (agent-bound)
    thread_fs = get_thread_filesystem()
    if thread_fs is not None:
        return thread_fs
    
    # Priority 2: Signella-based lookup (UI/non-agent context)
    session_id = _store.get('session', 'current', default='default')
    project_id = _store.get('session', session_id, 'project_id', default='local')
    
    # Check cache first
    if project_id in _filesystems:
        return _filesystems[project_id]
    
    # Get project from ProjectManager
    from .project_manager import ProjectManager
    pm = ProjectManager()
    project = pm.get(project_id)
    
    if project:
        fs = project.get_filesystem()
        _filesystems[project_id] = fs
        return fs
    
    # Fallback to default local project
    default_project = pm.get_default()
    fs = default_project.get_filesystem()
    _filesystems[default_project.id] = fs
    return fs


def set_current_project(session_id: str, project_id: str) -> None:
    """
    Switch the current project for a session.
    
    Updates Signella with the new project ID and clears any cached
    filesystem for that project to force refresh.
    
    Args:
        session_id: Session ID to update
        project_id: New project ID
    """
    _store.set('session', session_id, 'project_id', project_id)
    
    # Clear cached filesystem to force refresh
    if project_id in _filesystems:
        old_fs = _filesystems.pop(project_id)
        # Close if filesystem supports it (e.g., SSH connections)
        if hasattr(old_fs, 'close'):
            old_fs.close()


def get_project_root() -> Path:
    """
    Get the root path of the current project.
    
    Convenience function that returns the root as a Path object.
    
    Returns:
        Path to current project root
    """
    fs = get_current_filesystem()
    return Path(fs.root)


def clear_filesystem_cache() -> None:
    """
    Clear all cached filesystem instances.
    
    Useful for testing or when project configurations change.
    """
    global _filesystems
    for fs in _filesystems.values():
        if hasattr(fs, 'close'):
            fs.close()
    _filesystems.clear()
