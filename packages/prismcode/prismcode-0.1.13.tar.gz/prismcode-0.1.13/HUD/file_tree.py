# -*- coding: utf-8 -*-
"""
FileTree - Clean project tree generator that shows git-tracked files.

Supports both local and remote (SSH) filesystems via the filesystem abstraction.

Produces output like:
    mobius/
    ├── cli/
    │   ├── __init__.py
    │   └── main.py
    ├── core/
    │   └── agent.py
    └── config.py
"""

import subprocess
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.filesystem import FileSystem


# Box-drawing characters
PIPE = "\u2502"      # │
ELBOW = "\u2514"     # └
TEE = "\u251c"       # ├
DASH = "\u2500"      # ─


class FileTree:
    """Generates a clean file tree from git-tracked files (local filesystem only)."""

    def __init__(
        self,
        root: Optional[Path] = None,
        include_env: bool = True,
        exclude_pycache: bool = True,
        exclude_patterns: Optional[list[str]] = None,
    ):
        """
        Args:
            root: Project root directory (defaults to cwd)
            include_env: Include .env* files even if not tracked
            exclude_pycache: Exclude __pycache__ directories
            exclude_patterns: Additional patterns to exclude (e.g., ["*.pyc", "node_modules"])
        """
        self.root = Path(root) if root else Path.cwd()
        self.include_env = include_env
        self.exclude_pycache = exclude_pycache
        self.exclude_patterns = exclude_patterns or []

    def _get_git_files(self) -> list[str]:
        """Get list of git-tracked files."""
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

    def _get_env_files(self) -> list[str]:
        """Find .env* files."""
        env_files = []
        for f in self.root.glob(".env*"):
            if f.is_file():
                env_files.append(f.name)
        return env_files

    def _load_gitignore(self) -> list[str]:
        """Load patterns from .gitignore."""
        gitignore_path = self.root / ".gitignore"
        if not gitignore_path.exists():
            return []

        patterns = []
        with open(gitignore_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Remove trailing /* for directory patterns
                    pattern = line.rstrip("/*")
                    patterns.append(pattern)
        return patterns

    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded."""
        if self.exclude_pycache and "__pycache__" in path:
            return True
        if path.endswith(".pyc"):
            return True

        # Check gitignore patterns
        gitignore_patterns = self._load_gitignore()
        for pattern in gitignore_patterns:
            if pattern in path or path.startswith(pattern):
                return True

        # Check user-provided patterns
        for pattern in self.exclude_patterns:
            if pattern.startswith("*"):
                if path.endswith(pattern[1:]):
                    return True
            elif pattern in path:
                return True
        return False

    def _build_tree(self, files: list[str]) -> dict:
        """Build nested dict structure from file list."""
        tree = {}
        for filepath in sorted(files):
            if self._should_exclude(filepath):
                continue
            parts = filepath.split("/")
            current = tree
            for part in parts[:-1]:  # directories
                if part not in current:
                    current[part] = {}
                current = current[part]
            # file (leaf node marked with None value)
            current[parts[-1]] = None
        return tree

    def _render_tree(self, tree: dict, prefix: str = "") -> list[str]:
        """Render tree dict to lines with box-drawing characters."""
        lines = []
        # Sort: directories first (subtree is dict), then files (subtree is None)
        items = sorted(tree.items(), key=lambda x: (x[1] is None, x[0].lower()))

        for i, (name, subtree) in enumerate(items):
            is_last = i == len(items) - 1
            connector = ELBOW + DASH + DASH + " " if is_last else TEE + DASH + DASH + " "

            if subtree is None:  # file
                lines.append(prefix + connector + name)
            else:  # directory
                lines.append(prefix + connector + name + "/")
                extension = "    " if is_last else PIPE + "   "
                lines.extend(self._render_tree(subtree, prefix + extension))

        return lines

    def generate(self) -> str:
        """Generate the file tree string."""
        files = self._get_git_files()

        if self.include_env:
            env_files = self._get_env_files()
            files.extend(env_files)

        files = list(set(files))  # dedupe
        tree = self._build_tree(files)

        root_name = self.root.name or "."
        lines = [root_name + "/"]
        lines.extend(self._render_tree(tree))

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.generate()


class RemoteFileTree:
    """
    Generates a file tree for remote (SSH) filesystems.
    
    Uses the filesystem abstraction to list files remotely,
    running git commands over SSH when possible.
    """
    
    def __init__(
        self,
        fs: "FileSystem",
        exclude_pycache: bool = True,
        exclude_patterns: Optional[list[str]] = None,
        max_depth: int = 5,
    ):
        """
        Args:
            fs: FileSystem instance (SSH or local)
            exclude_pycache: Exclude __pycache__ directories
            exclude_patterns: Additional patterns to exclude
            max_depth: Maximum directory depth to traverse
        """
        self.fs = fs
        self.exclude_pycache = exclude_pycache
        self.exclude_patterns = exclude_patterns or []
        self.max_depth = max_depth
        self._gitignore_patterns: list[str] = []
    
    def _load_gitignore(self) -> list[str]:
        """Load patterns from .gitignore on remote."""
        try:
            content = self.fs.read(".gitignore")
            patterns = []
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    pattern = line.rstrip("/*")
                    patterns.append(pattern)
            return patterns
        except (FileNotFoundError, IOError):
            return []
    
    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded."""
        if self.exclude_pycache and "__pycache__" in path:
            return True
        if path.endswith(".pyc"):
            return True
        
        # Common patterns to always exclude
        always_exclude = ['.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache']
        for pattern in always_exclude:
            if pattern in path.split('/'):
                return True
        
        # Check gitignore patterns
        for pattern in self._gitignore_patterns:
            if pattern in path or path.startswith(pattern):
                return True
        
        # Check user-provided patterns
        for pattern in self.exclude_patterns:
            if pattern.startswith("*"):
                if path.endswith(pattern[1:]):
                    return True
            elif pattern in path:
                return True
        return False
    
    def _get_files_via_git(self) -> list[str]:
        """Try to get file list via git ls-files on remote."""
        try:
            output, code = self.fs.exec("git ls-files 2>/dev/null")
            if code == 0 and output.strip():
                return [f for f in output.strip().split("\n") if f]
        except Exception:
            pass
        return []
    
    def _get_files_via_find(self) -> list[str]:
        """Get file list via find command (fallback)."""
        try:
            # Use find with common exclusions built-in for efficiency
            cmd = (
                "find . -maxdepth 5 -type f "
                "-not -path '*/.git/*' "
                "-not -path '*/__pycache__/*' "
                "-not -path '*/.venv/*' "
                "-not -path '*/venv/*' "
                "-not -path '*/node_modules/*' "
                "2>/dev/null | head -500 | sed 's|^\\./||'"
            )
            output, code = self.fs.exec(cmd)
            if code == 0 and output.strip():
                return [f for f in output.strip().split("\n") if f and not f.startswith('.')]
        except Exception:
            pass
        return []
    
    def _build_tree(self, files: list[str]) -> dict:
        """Build nested dict structure from file list."""
        tree = {}
        for filepath in sorted(files):
            if self._should_exclude(filepath):
                continue
            parts = filepath.split("/")
            current = tree
            for part in parts[:-1]:  # directories
                if part not in current:
                    current[part] = {}
                current = current[part]
            # file (leaf node marked with None value)
            if parts[-1]:  # Ensure we have a filename
                current[parts[-1]] = None
        return tree
    
    def _render_tree(self, tree: dict, prefix: str = "") -> list[str]:
        """Render tree dict to lines with box-drawing characters."""
        lines = []
        items = sorted(tree.items(), key=lambda x: (x[1] is None, x[0].lower()))
        
        for i, (name, subtree) in enumerate(items):
            is_last = i == len(items) - 1
            connector = ELBOW + DASH + DASH + " " if is_last else TEE + DASH + DASH + " "
            
            if subtree is None:  # file
                lines.append(prefix + connector + name)
            else:  # directory
                lines.append(prefix + connector + name + "/")
                extension = "    " if is_last else PIPE + "   "
                lines.extend(self._render_tree(subtree, prefix + extension))
        
        return lines
    
    def generate(self) -> str:
        """Generate the file tree string."""
        # Load gitignore patterns
        self._gitignore_patterns = self._load_gitignore()
        
        # Try git first, fall back to find
        files = self._get_files_via_git()
        if not files:
            files = self._get_files_via_find()
        
        if not files:
            return "(unable to list files)"
        
        tree = self._build_tree(files)
        
        # Get project name from root path
        root_name = self.fs.root.rstrip('/').split('/')[-1] or "project"
        lines = [root_name + "/"]
        lines.extend(self._render_tree(tree))
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        return self.generate()


def get_file_tree_for_project() -> str:
    """
    Get file tree for the current project, whether local or remote.
    
    Automatically detects if we're on an SSH project and uses
    the appropriate file tree generator.
    
    Returns:
        File tree as a string
    """
    from core.filesystem import get_current_filesystem
    from core.filesystem import LocalFileSystem
    
    fs = get_current_filesystem()
    
    # Check if it's a local filesystem
    if isinstance(fs, LocalFileSystem):
        tree = FileTree(root=Path(fs.root))
        return tree.generate()
    else:
        # Remote filesystem - use RemoteFileTree
        tree = RemoteFileTree(fs)
        return tree.generate()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate clean project file tree")
    parser.add_argument("--no-env", action="store_true", help="Exclude .env files")
    parser.add_argument("--include-pycache", action="store_true", help="Include __pycache__")
    parser.add_argument("--exclude", nargs="*", default=[], help="Patterns to exclude")
    parser.add_argument("path", nargs="?", default=".", help="Project root path")

    args = parser.parse_args()

    tree = FileTree(
        root=Path(args.path),
        include_env=not args.no_env,
        exclude_pycache=not args.include_pycache,
        exclude_patterns=args.exclude,
    )
    print(tree.generate())


if __name__ == "__main__":
    main()
