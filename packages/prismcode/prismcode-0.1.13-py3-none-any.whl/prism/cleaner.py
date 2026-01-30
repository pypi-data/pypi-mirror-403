"""Orphan file deletion utilities for Prism."""
import os
from pathlib import Path
from typing import Set, Dict, List, Any


def count_lines(filepath: Path) -> int:
    """Count lines in a file.

    Args:
        filepath: Path to file

    Returns:
        Number of lines in file
    """
    try:
        with open(filepath, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def get_orphan_files(
    orphan_paths: Set[str], project_root: Path
) -> List[Dict[str, Any]]:
    """Get list of orphan files with metadata.

    Args:
        orphan_paths: Set of relative paths to orphan files
        project_root: Root directory of project

    Returns:
        List of dictionaries with file metadata
    """
    files = []
    for rel_path in sorted(orphan_paths):
        full_path = project_root / rel_path
        if full_path.exists():
            files.append(
                {
                    "path": rel_path,
                    "full_path": str(full_path),
                    "lines": count_lines(full_path),
                }
            )
    return files


def preview_deletion(orphan_paths: Set[str], project_root: Path) -> Dict[str, Any]:
    """Preview what would be deleted (files and empty folders).

    Args:
        orphan_paths: Set of relative paths to orphan files
        project_root: Root directory of project

    Returns:
        Dictionary with files and folders that would be deleted
    """
    files = get_orphan_files(orphan_paths, project_root)

    # Collect all parent folders
    folders_to_check: Set[Path] = set()
    for f in files:
        folder = Path(f["full_path"]).parent
        while folder != project_root and folder.parent != folder:
            folders_to_check.add(folder)
            folder = folder.parent

    # Find potentially empty folders
    potentially_empty_folders: List[str] = []
    for folder in sorted(folders_to_check, key=lambda x: len(str(x)), reverse=True):
        if not folder.exists():
            continue

        remaining_files = []
        orphan_full_paths = {project_root / f["path"] for f in files}

        for item in folder.iterdir():
            if item.is_file():
                if item not in orphan_full_paths and item.suffix == ".py":
                    remaining_files.append(item)
            elif item.is_dir():
                remaining_files.append(item)

        if len(remaining_files) == 0:
            try:
                rel = str(folder.relative_to(project_root))
                potentially_empty_folders.append(rel)
            except ValueError:
                pass

    return {
        "files": files,
        "folders": potentially_empty_folders,
        "total_files": len(files),
        "total_folders": len(potentially_empty_folders),
    }


def delete_orphans(orphan_paths: Set[str], project_root: Path) -> Dict[str, Any]:
    """Delete orphan files and empty folders.

    Args:
        orphan_paths: Set of relative paths to orphan files
        project_root: Root directory of project

    Returns:
        Dictionary with deletion statistics and errors
    """
    deleted_files = 0
    deleted_folders = 0
    errors: List[str] = []

    # Collect files to delete
    files_to_delete = []
    for rel_path in orphan_paths:
        full_path = project_root / rel_path
        if full_path.exists() and full_path.is_file():
            files_to_delete.append(full_path)

    # Delete files
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            deleted_files += 1
        except Exception as e:
            errors.append(f"Failed to delete {file_path}: {e}")

    # Collect parent folders
    folders_to_check: Set[Path] = set()
    for file_path in files_to_delete:
        folder = file_path.parent
        while folder != project_root and folder.parent != folder:
            folders_to_check.add(folder)
            folder = folder.parent

    # Delete empty folders (bottom-up)
    for folder in sorted(folders_to_check, key=lambda x: len(str(x)), reverse=True):
        if not folder.exists():
            continue

        try:
            contents = list(folder.iterdir())
            py_files = [f for f in contents if f.is_file() and f.suffix == ".py"]
            other_files = [f for f in contents if f.is_file() and f.suffix != ".py"]
            subdirs = [f for f in contents if f.is_dir()]

            if len(py_files) == 0 and len(other_files) == 0 and len(subdirs) == 0:
                os.rmdir(folder)
                deleted_folders += 1
        except Exception as e:
            errors.append(f"Failed to remove folder {folder}: {e}")

    return {
        "deleted_files": deleted_files,
        "deleted_folders": deleted_folders,
        "errors": errors,
    }
