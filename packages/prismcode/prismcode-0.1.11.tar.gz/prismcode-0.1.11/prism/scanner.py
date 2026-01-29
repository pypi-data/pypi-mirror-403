"""File discovery and scanning for the Prism dependency analyzer."""
import os
import subprocess
from pathlib import Path
from typing import Set, List, Dict, Any, Optional
from concurrent.futures import ProcessPoolExecutor

from .models import NodeType


# File extensions to scan
SUPPORTED_EXTENSIONS = {
    ".py",  # Python
    ".html", ".htm", ".jinja", ".jinja2",  # HTML/Templates
    ".js", ".jsx",  # JavaScript
    ".ts", ".tsx",  # TypeScript
    ".css", ".scss", ".less",  # CSS
}

DEFAULT_EXCLUDE_PATTERNS = [
    ".venv",
    ".local",
    ".git",
    ".cache",
    "__pycache__",
    "node_modules",
    "site-packages",
    ".tox",
    ".eggs",
    "build",
    "dist",
    "__MACOSX",
]

DEFAULT_EXCLUDE_FILES = [
    "__init__.py",
]


class FileScanner:
    """Scans a project directory for relevant files."""

    def __init__(
        self,
        project_root: Path,
        exclude_patterns: Optional[List[str]] = None,
        exclude_files: Optional[List[str]] = None,
        include_init: bool = False,
    ):
        """Initialize the file scanner.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Directory patterns to exclude
            exclude_files: Specific filenames to exclude
            include_init: Whether to include __init__.py files
        """
        self.project_root = project_root.resolve()
        self.exclude_patterns = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS
        self.exclude_files = exclude_files or ([] if include_init else DEFAULT_EXCLUDE_FILES)

    def scan_all_files(self, parallel: bool = False) -> Set[Path]:
        """Scan project for all supported files.

        Args:
            parallel: Whether to use parallel processing for large directories

        Returns:
            Set of absolute paths to discovered files
        """
        all_files: Set[Path] = set()

        # Get top-level directories
        top_level_dirs = [
            d for d in self.project_root.iterdir()
            if d.is_dir() and not self._should_exclude_dir(d)
        ]

        # Scan top-level files
        for f in self.project_root.glob("*"):
            if f.is_file() and not self._should_exclude_file(f):
                if f.suffix in SUPPORTED_EXTENSIONS:
                    all_files.add(f.resolve())

        # Scan directories
        if len(top_level_dirs) > 4 and parallel:
            # Use parallel processing for large projects
            with ProcessPoolExecutor(max_workers=min(8, len(top_level_dirs))) as executor:
                args_list = [
                    (d, self.exclude_patterns, self.exclude_files)
                    for d in top_level_dirs
                ]
                for result in executor.map(self._scan_directory_static, args_list):
                    all_files.update(result)
        else:
            # Sequential scanning for small projects
            for d in top_level_dirs:
                all_files.update(self._scan_directory(d))

        return all_files

    def scan_python_files(self) -> Set[Path]:
        """Scan for Python files only."""
        all_files = self.scan_all_files()
        return {f for f in all_files if f.suffix == ".py"}

    def scan_frontend_files(self) -> Set[Path]:
        """Scan for frontend files (HTML, JS, CSS)."""
        all_files = self.scan_all_files()
        frontend_exts = {
            ".html", ".htm", ".jinja", ".jinja2",
            ".js", ".jsx", ".ts", ".tsx",
            ".css", ".scss", ".less",
        }
        return {f for f in all_files if f.suffix in frontend_exts}

    def detect_project_packages(self) -> List[str]:
        """Detect top-level Python packages in the project.

        Returns:
            List of package names
        """
        packages = []
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Check if it's a Python package
                if (item / "__init__.py").exists() or any(item.glob("*.py")):
                    packages.append(item.name)
        return packages

    def find_template_folder(self) -> Optional[Path]:
        """Find the templates directory in the project."""
        candidates = ["templates", "template"]

        # Check root level
        for name in candidates:
            candidate = self.project_root / name
            if candidate.exists() and candidate.is_dir():
                return candidate

        # Search subdirectories (max 3 levels)
        for root, dirs, _ in os.walk(self.project_root):
            # Filter excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude_pattern(d)]

            root_path = Path(root)
            depth = len(root_path.relative_to(self.project_root).parts)
            if depth > 3:
                dirs.clear()
                continue

            for name in candidates:
                candidate = root_path / name
                if candidate.exists() and candidate.is_dir():
                    return candidate

        return None

    def find_static_folder(self) -> Optional[Path]:
        """Find the static/assets directory in the project."""
        candidates = ["static", "public", "assets", "frontend"]

        # Check root level
        for name in candidates:
            candidate = self.project_root / name
            if candidate.exists() and candidate.is_dir():
                return candidate

        # Search subdirectories (max 3 levels)
        for root, dirs, _ in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if not self._should_exclude_pattern(d)]

            root_path = Path(root)
            depth = len(root_path.relative_to(self.project_root).parts)
            if depth > 3:
                dirs.clear()
                continue

            for name in candidates:
                candidate = root_path / name
                if candidate.exists() and candidate.is_dir():
                    return candidate

        return None

    def get_git_submodules(self) -> List[str]:
        """Get list of git submodules in the project.

        Returns:
            List of submodule paths
        """
        submodules = set()

        # Try git command
        try:
            result = subprocess.run(
                ["git", "config", "--file", ".gitmodules", "--get-regexp", "path"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split(None, 1)
                        if len(parts) == 2:
                            submodules.add(parts[1])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: parse .gitmodules file
        if not submodules:
            gitmodules_path = self.project_root / ".gitmodules"
            if gitmodules_path.exists():
                try:
                    with open(gitmodules_path, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("path"):
                                parts = line.split("=", 1)
                                if len(parts) == 2:
                                    submodules.add(parts[1].strip())
                except Exception:
                    pass

        # Detect directories with .git marker
        for item in self.project_root.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                git_marker = item / ".git"
                if git_marker.exists():
                    submodules.add(item.name)

        return sorted(submodules)

    def _scan_directory(self, directory: Path) -> List[Path]:
        """Scan a directory recursively for files."""
        results = []
        try:
            for root, dirs, files in os.walk(directory):
                root_path = Path(root)

                # Filter directories
                dirs[:] = [
                    d for d in dirs
                    if not self._should_exclude_dir(root_path / d)
                ]

                # Add files
                for f in files:
                    file_path = root_path / f
                    if not self._should_exclude_file(file_path):
                        if file_path.suffix in SUPPORTED_EXTENSIONS:
                            results.append(file_path.resolve())
        except Exception:
            pass
        return results

    @staticmethod
    def _scan_directory_static(args) -> List[Path]:
        """Static method for parallel directory scanning."""
        directory, exclude_patterns, exclude_files = args
        results = []
        try:
            for root, dirs, files in os.walk(directory):
                root_path = Path(root)

                # Filter directories
                dirs[:] = [
                    d for d in dirs
                    if not FileScanner._should_exclude_pattern_static(
                        root_path / d, exclude_patterns
                    )
                ]

                # Add files
                for f in files:
                    if f in exclude_files:
                        continue
                    file_path = root_path / f
                    if file_path.suffix in SUPPORTED_EXTENSIONS:
                        if not FileScanner._should_exclude_pattern_static(
                            file_path, exclude_patterns
                        ):
                            results.append(file_path.resolve())
        except Exception:
            pass
        return results

    def _should_exclude_dir(self, path: Path) -> bool:
        """Check if a directory should be excluded."""
        return self._should_exclude_pattern(path.name)

    def _should_exclude_file(self, path: Path) -> bool:
        """Check if a file should be excluded."""
        if path.name in self.exclude_files:
            return True
        return self._should_exclude_pattern(path.name)

    def _should_exclude_pattern(self, name: str) -> bool:
        """Check if a name matches any exclude pattern."""
        return any(pattern in name for pattern in self.exclude_patterns)

    @staticmethod
    def _should_exclude_pattern_static(path: Path, exclude_patterns: List[str]) -> bool:
        """Static method to check if path matches exclude patterns."""
        path_parts = path.parts
        return any(pattern in path_parts for pattern in exclude_patterns)


# Standalone function for compatibility
def get_git_submodules(project_root: Path) -> List[str]:
    """Get list of git submodules in the project.

    Args:
        project_root: Root directory of the project

    Returns:
        List of submodule paths
    """
    scanner = FileScanner(project_root)
    return scanner.get_git_submodules()
