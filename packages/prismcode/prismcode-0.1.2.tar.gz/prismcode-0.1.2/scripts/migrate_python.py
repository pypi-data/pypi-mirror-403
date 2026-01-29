#!/usr/bin/env python3
"""
File Migration Script
Moves Python files to new locations and updates all references across the project.
"""

import json
import os
import shutil
import re
from typing import List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()


def load_migrations(json_path: str) -> List[dict]:
    """Load migration mappings from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def path_to_module(file_path: str) -> str:
    """Convert file path to Python module path."""
    # Remove .py extension and convert slashes to dots
    module = file_path.replace('.py', '').replace('/', '.')
    return module


def find_all_python_files(root_dir: str = '.') -> List[str]:
    """Find all Python files in the project."""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def get_import_patterns(old_module: str) -> List[Tuple[re.Pattern, str]]:
    """Generate regex patterns to find imports of the old module."""
    patterns = []

    # Pattern 1: from old.module import something
    patterns.append(
        (re.compile(rf'from\s+{re.escape(old_module)}\s+import\s+'), 'from_import')
    )

    # Pattern 2: import old.module
    patterns.append(
        (re.compile(rf'\b import\s+{re.escape(old_module)}\b'), 'direct_import')
    )

    # Pattern 3: import old.module as alias
    patterns.append(
        (re.compile(rf'\b import\s+{re.escape(old_module)}\s+as\s+'), 'import_as')
    )

    return patterns


def update_imports_in_file(file_path: str, old_module: str, new_module: str) -> int:
    """Update imports in a single file. Returns number of changes made."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        # Silently skip files we can't read
        return 0

    original_content = content

    # Use regex to only match actual import statements, not variable names
    # Pattern 1: from old_module import ...
    content = re.sub(
        rf'^(\s*from\s+){re.escape(old_module)}(\s+import\s+)',
        rf'\g<1>{new_module}\g<2>',
        content,
        flags=re.MULTILINE
    )

    # Pattern 2: import old_module (with word boundary to avoid partial matches)
    content = re.sub(
        rf'^(\s*import\s+){re.escape(old_module)}\b',
        rf'\g<1>{new_module}',
        content,
        flags=re.MULTILINE
    )

    # Pattern 3: from parent import module_name (for dotted modules)
    if '.' in old_module:
        old_parent, module_name = old_module.rsplit('.', 1)
        new_parent = new_module.rsplit('.', 1)[0]

        content = re.sub(
            rf'^(\s*from\s+){re.escape(old_parent)}(\s+import\s+{re.escape(module_name)})\b',
            rf'\g<1>{new_parent}\g<2>',
            content,
            flags=re.MULTILINE
        )

    # Only replace explicit file path strings (must end in .py)
    old_path = old_module.replace('.', '/')
    new_path = new_module.replace('.', '/')
    content = re.sub(
        rf'(["\']){re.escape(old_path)}\.py(["\'])',
        rf'\g<1>{new_path}.py\g<2>',
        content
    )

    changes = 0
    if content != original_content:
        changes = len(re.findall(rf'\b{re.escape(new_module)}\b', content)) - \
                  len(re.findall(rf'\b{re.escape(new_module)}\b', original_content))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return max(changes, 1) if content != original_content else 0


def move_file(source: str, destination_dir: str) -> Tuple[bool, str]:
    """Move file to new location. Returns (success, new_path)."""
    if not os.path.exists(source):
        return False, f"Source file does not exist: {source}"

    # Get the filename
    filename = os.path.basename(source)

    # Create destination directory if it doesn't exist
    os.makedirs(destination_dir, exist_ok=True)

    # Full destination path
    dest_path = os.path.join(destination_dir, filename)

    # Check if destination already exists
    if os.path.exists(dest_path):
        return False, f"Destination already exists: {dest_path}"

    try:
        shutil.move(source, dest_path)
        return True, dest_path
    except Exception as e:
        return False, str(e)


def main():
    # Header
    header = Panel.fit(
        "[bold cyan]File Migration Script[/bold cyan]\n"
        "[dim]Moves files and updates all references across the project[/dim]",
        box=box.DOUBLE,
        padding=(1, 2)
    )
    console.print(header)
    console.print()

    # Load migrations
    json_path = 'migrate.json'
    if not os.path.exists(json_path):
        console.print(f"[red]Error: {json_path} not found[/red]")
        return

    migrations = load_migrations(json_path)
    console.print(f"[cyan]Loaded {len(migrations)} migrations from {json_path}[/cyan]")
    console.print()

    # Find all Python files
    console.print("[cyan]Scanning project for Python files...[/cyan]")
    python_files = find_all_python_files()
    console.print(f"[green]Found {len(python_files)} Python files[/green]")
    console.print()

    # Confirmation
    console.print("[yellow]This will move files and update imports across the project.[/yellow]")
    response = input("Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        console.print("[red]Aborted[/red]")
        return
    console.print()

    # PHASE 1: Update all imports first
    console.print("[bold cyan]Phase 1: Updating all imports...[/bold cyan]")
    import_updates = {}

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("[cyan]Updating imports...", total=len(migrations))

        for migration in migrations:
            source = migration['source']
            dest_dir = migration['destination']

            # Convert paths to module names
            old_module = path_to_module(source)
            filename = os.path.basename(source)
            new_file_path = os.path.join(dest_dir, filename)
            new_module = path_to_module(new_file_path)

            progress.update(task, description=f"[cyan]Updating imports for {os.path.basename(source)}...")

            # Update imports in all Python files
            files_updated = 0
            for py_file in python_files:
                changes = update_imports_in_file(py_file, old_module, new_module)
                if changes > 0:
                    files_updated += 1

            import_updates[source] = files_updated
            progress.advance(task)

    console.print("[green]✓ All imports updated[/green]\n")

    # PHASE 2: Move all files
    console.print("[bold cyan]Phase 2: Moving files...[/bold cyan]")
    results_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    results_table.add_column("Source", style="cyan")
    results_table.add_column("Destination", style="green")
    results_table.add_column("Files Updated", style="yellow")
    results_table.add_column("Status", style="blue")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("[cyan]Moving files...", total=len(migrations))

        for migration in migrations:
            source = migration['source']
            dest_dir = migration['destination']
            filename = os.path.basename(source)
            new_file_path = os.path.join(dest_dir, filename)

            progress.update(task, description=f"[cyan]Moving {os.path.basename(source)}...")

            # Move the file
            success, result = move_file(source, dest_dir)

            status = "[green]✓ Success[/green]" if success else f"[red]✗ {result}[/red]"
            results_table.add_row(
                source,
                new_file_path if success else dest_dir,
                str(import_updates.get(source, 0)),
                status
            )

            progress.advance(task)

    console.print()
    console.print(results_table)
    console.print()
    console.print("[bold green]Migration complete![/bold green]")


if __name__ == '__main__':
    main()
