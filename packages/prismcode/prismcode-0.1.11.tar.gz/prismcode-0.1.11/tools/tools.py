import subprocess
import shlex
from pathlib import Path
from core.code_edit import FileEditor
from core.signella import Signella
from core.filesystem import get_current_filesystem, get_project_root

# Shared editor instance
_editor = FileEditor()

# Signella store for cross-process state
_store = Signella()


def _get_fs():
    """Get the current filesystem (convenience wrapper)."""
    return get_current_filesystem()


def _get_current_session() -> str:
    """Get current session ID from Signella."""
    return _store.get('session', 'current', default='default')


def _get_focused_files() -> set:
    """Get focused files for current session from Signella."""
    session_id = _get_current_session()
    files = _store.get('focus', session_id, 'files', default=[])
    return set(files) if files else set()


def _set_focused_files(files: set):
    """Set focused files for current session in Signella."""
    session_id = _get_current_session()
    _store.set('focus', session_id, 'files', list(files))


def read_file(file_path: str) -> str:
    """Read the contents of a file.

    Args:
        file_path: Path to the file to read
    """
    try:
        fs = _get_fs()
        return fs.read(file_path)
    except Exception as e:
        return f"Error: {e}"


def create_file(file_path: str, content: str) -> str:
    """Create a new file with the given content.

    Args:
        file_path: Path for the new file
        content: Content to write to the file
    """
    try:
        fs = _get_fs()
        if fs.exists(file_path):
            return f"Error: File already exists: {file_path}"
        fs.write(file_path, content)
        return f"Created file: {file_path}"
    except Exception as e:
        return f"Error: {e}"


def edit_file(file_path: str, old_str: str, new_str: str, intent: str = "") -> str:
    """Replace text in a file. Uses fuzzy matching to find the old_str.

    Args:
        file_path: Path to the file to edit
        old_str: The exact text to find and replace (include enough context to be unique)
        new_str: The replacement text
        intent: Brief description of why this change is being made (optional)
    """
    try:
        fs = _get_fs()
        
        # Read current content
        content = fs.read(file_path)
        
        # Use FileEditor's fuzzy matching on the content string
        result = _editor.str_replace_content(content, old_str, new_str)
        
        if not result.success:
            return result.message
        
        # Write the modified content back
        fs.write(file_path, result.new_content)
        
        return f"Edited {file_path}. {result.message}"
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error: {e}"


def rename_file(old_path: str, new_path: str) -> str:
    """Rename or move a file to a new location.

    Args:
        old_path: Current path of the file
        new_path: New path for the file
    """
    try:
        fs = _get_fs()
        if not fs.exists(old_path):
            return f"Error: File not found: {old_path}"
        fs.rename(old_path, new_path)
        return f"Renamed {old_path} → {new_path}"
    except Exception as e:
        return f"Error: {e}"


def delete_file(file_path: str) -> str:
    """Delete a file.

    Args:
        file_path: Path to the file to delete
    """
    try:
        fs = _get_fs()
        if not fs.exists(file_path):
            return f"Error: File not found: {file_path}"
        if fs.is_dir(file_path):
            return f"Error: {file_path} is a directory, not a file"
        fs.delete(file_path)
        return f"Deleted {file_path}"
    except Exception as e:
        return f"Error: {e}"


def ls(path: str = ".") -> str:
    """List files and directories in a path.

    Args:
        path: Directory path to list (defaults to current directory)
    """
    try:
        fs = _get_fs()
        if not fs.exists(path):
            return f"Error: Path not found: {path}"
        if not fs.is_dir(path):
            return f"Error: Not a directory: {path}"

        items = fs.ls(path)
        lines = []
        for item in items:
            if item["is_dir"]:
                lines.append(f"📁 {item['name']}/")
            else:
                lines.append(f"   {item['name']}")
        return "\n".join(lines) if lines else "(empty directory)"
    except Exception as e:
        return f"Error: {e}"


def focus(file_path: str) -> str:
    """Add a file to the HUD (heads-up display) for persistent visibility.

    Unlike read_file which adds content to chat history, focus adds the file
    to the HUD where it stays visible and auto-updates on each turn without
    consuming conversation tokens. Perfect for iterating on files you're actively
    working on.

    Args:
        file_path: Path to the file to add to HUD
    """
    try:
        fs = _get_fs()
        
        if not fs.exists(file_path):
            return f"Error: File not found: {file_path}"
        if fs.is_dir(file_path):
            return f"Error: Not a file: {file_path}"

        # Normalize path using filesystem's absolute path
        abs_path = fs.absolute(file_path)
        focused = _get_focused_files()
        focused.add(abs_path)
        _set_focused_files(focused)

        session_id = _get_current_session()
        return f"✓ Focused on {file_path} (session: {session_id[:8]}). Currently focused: {len(focused)} file(s)"
    except Exception as e:
        return f"Error: {e}"


def unfocus(file_path: str = None) -> str:
    """Remove a file from the HUD, or clear all focused files if no path given.

    Args:
        file_path: Path to file to remove from HUD (optional - clears all if omitted)
    """
    try:
        focused = _get_focused_files()
        
        if file_path is None:
            count = len(focused)
            _set_focused_files(set())
            return f"✓ Cleared all {count} focused file(s) from HUD"

        fs = _get_fs()
        abs_path = fs.absolute(file_path)

        if abs_path in focused:
            focused.remove(abs_path)
            _set_focused_files(focused)
            return f"✓ Unfocused {file_path}. Remaining: {len(focused)} file(s)"
        else:
            # Try matching by filename in case of path format differences
            matching = [f for f in focused if f.endswith('/' + file_path) or f.endswith(file_path)]
            if matching:
                focused.remove(matching[0])
                _set_focused_files(focused)
                return f"✓ Unfocused {file_path}. Remaining: {len(focused)} file(s)"
            return f"File not in focus: {file_path}"
    except Exception as e:
        return f"Error: {e}"


def list_focused() -> str:
    """List all files currently in the HUD."""
    focused = _get_focused_files()
    session_id = _get_current_session()
    
    if not focused:
        return f"No files currently focused in HUD (session: {session_id[:8]})"

    fs = _get_fs()
    project_root = str(get_project_root())
    
    lines = [f"Files in HUD (session: {session_id[:8]}):"]
    for abs_path in sorted(focused):
        # Show relative path if possible
        if project_root and abs_path.startswith(project_root):
            rel_path = abs_path[len(project_root):].lstrip('/')
        else:
            rel_path = abs_path
        lines.append(f"  • {rel_path}")

    return "\n".join(lines)


def bash(command: str, timeout: int = 120) -> str:
    """Execute a bash command and return stdout/stderr.
    
    Use this for running tests, installing packages, git operations,
    checking file contents with grep/cat, and other shell tasks.
    
    Args:
        command: The bash command to execute
        timeout: Maximum seconds to wait (default 120)
    
    Returns:
        Combined stdout and stderr output, or error message
    """
    try:
        fs = _get_fs()
        output, code = fs.exec(command, timeout=timeout)
        
        if code != 0:
            output = f"[Exit code: {code}]\n{output}"
        
        return output.strip() if output else "(no output)"
        
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {e}"
