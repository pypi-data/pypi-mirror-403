# Multi-Project & SSH Implementation Plan

## Overview

This document provides a comprehensive, step-by-step implementation plan for adding multi-project and SSH support to Mobius. Each phase includes specific files to focus, detailed checklists, and testing requirements.

**Goal:** Transform Mobius into a multi-project workspace that can seamlessly work with local and remote (SSH) projects from a single interface.

**Estimated Effort:** 4-6 focused sessions across 6 phases.

---

## Pre-Implementation Checklist

Before starting, ensure:
- [ ] All existing tests pass
- [ ] Current session/history functionality works correctly
- [ ] SSH access to at least one test server is available
- [ ] `~/.ssh/config` has at least one configured host for testing

---

## Phase 1: FileSystem Abstraction (Foundation)

**Purpose:** Create an abstract filesystem interface that all tools will use, making them agnostic to local vs remote operations.

### Files to Focus
```
focus core/signella.py
focus tools/tools.py
focus core/agent.py
```

### Step 1.1: Create FileSystem Protocol

**Create:** `core/filesystem.py`

- [x] Define `FileSystem` Protocol class with all required methods:
  - [x] `root` property (returns project root path)
  - [x] `read(path: str) -> str`
  - [x] `write(path: str, content: str) -> None`
  - [x] `delete(path: str) -> None`
  - [x] `rename(old_path: str, new_path: str) -> None`
  - [x] `exists(path: str) -> bool`
  - [x] `is_file(path: str) -> bool`
  - [x] `is_dir(path: str) -> bool`
  - [x] `ls(path: str) -> List[dict]` (returns name, is_dir, size)
  - [x] `mkdir(path: str, parents: bool) -> None`
  - [x] `exec(command: str, cwd: str, timeout: int) -> Tuple[str, int]`
  - [x] `walk(path: str) -> Iterator[Tuple[str, List[str], List[str]]]`

- [x] Add type hints and docstrings for each method
- [x] Export from `core/__init__.py`

### Step 1.2: Implement LocalFileSystem

**In:** `core/filesystem.py`

- [x] Create `LocalFileSystem` class implementing `FileSystem`
- [x] Constructor takes `root: Path` parameter
- [x] Implement `_resolve(path: str) -> Path` helper to handle relative paths
- [x] Implement all protocol methods using `pathlib` and `subprocess`
- [x] Add proper error handling (FileNotFoundError, IOError, etc.)
- [x] Ensure all paths stay within project root (security)

### Step 1.3: Add FileSystem State Management

**In:** `core/filesystem.py`

- [ ] Create module-level `_filesystems: Dict[str, FileSystem]` cache
- [ ] Implement `get_current_filesystem() -> FileSystem`:
  - [ ] Get current session ID from Signella
  - [ ] Get project ID for session from Signella (default: 'local')
  - [ ] Return cached filesystem or create new one
- [ ] Implement `set_current_project(session_id: str, project_id: str)`:
  - [ ] Update Signella with new project ID
  - [ ] Clear cached filesystem for that project
  - [ ] Call `close()` on old filesystem if it has that method
- [ ] Implement `get_project(project_id: str) -> Project` (stub for now, returns local)

### Step 1.4: Refactor Tools to Use FileSystem

**In:** `tools/tools.py`

- [ ] Import `get_current_filesystem` from `core.filesystem`
- [ ] Refactor `read_file()`:
  - [ ] Replace `Path` operations with `fs.read()`
  - [ ] Keep existing error handling pattern
- [ ] Refactor `create_file()`:
  - [ ] Use `fs.exists()` to check for existing file
  - [ ] Use `fs.write()` to create file
- [ ] Refactor `edit_file()`:
  - [ ] Use `fs.read()` to get content
  - [ ] Keep `FileEditor` logic for fuzzy matching (operates on content string)
  - [ ] Use `fs.write()` to save result
- [ ] Refactor `rename_file()`:
  - [ ] Use `fs.exists()` and `fs.rename()`
- [ ] Refactor `delete_file()`:
  - [ ] Use `fs.exists()`, `fs.is_dir()`, `fs.delete()`
- [ ] Refactor `ls()`:
  - [ ] Use `fs.exists()`, `fs.is_dir()`, `fs.ls()`
  - [ ] Format output consistently
- [ ] Refactor `bash()`:
  - [ ] Use `fs.exec()` instead of `subprocess.run()`
  - [ ] Handle return code and output formatting
- [ ] Update `focus()` and `unfocus()`:
  - [ ] Paths should be resolved relative to `fs.root`
  - [ ] Store absolute paths in Signella

### Step 1.5: Update FileEditor

**In:** `core/code_edit.py`

- [x] Add `str_replace_content(content: str, old_str: str, new_str: str) -> EditResult`:
  - [x] Extract fuzzy matching logic from `str_replace()`
  - [x] Operate on content string instead of file
  - [x] Return `EditResult` with `new_content` field
- [x] Keep existing `str_replace()` for backward compatibility
- [x] Have `str_replace()` call `str_replace_content()` internally

### Step 1.6: Testing Phase 1

- [ ] Run all existing tests
- [ ] Manually test each tool function:
  - [ ] `read_file` on existing file
  - [ ] `create_file` new file
  - [ ] `edit_file` with exact match
  - [ ] `edit_file` with fuzzy match
  - [ ] `rename_file`
  - [ ] `delete_file`
  - [ ] `ls` on directory
  - [ ] `bash` command execution
  - [ ] `focus` and `unfocus`
- [ ] Verify Signella state is correct after operations
- [ ] Test that HUD still shows focused files

---

## Phase 2: Project Model & Management

**Purpose:** Define the Project data structure and create a manager for CRUD operations on projects.

### Files to Focus
```
focus core/filesystem.py
focus core/signella.py
focus core/history.py
focus run_web.py
```

### Step 2.1: Create Project Model

**Create:** `core/project.py`

- [x] Define `Project` dataclass:
  - [x] `id: str` - unique identifier (slug format)
  - [x] `name: str` - display name
  - [x] `type: Literal["local", "ssh"]`
  - [x] `path: str` - root path on filesystem
  - [x] `color: str = "#ff6b2b"` - UI accent color
  - [x] `host: Optional[str] = None` - SSH hostname or config alias
  - [x] `user: Optional[str] = None` - SSH username
  - [x] `port: int = 22` - SSH port
  - [x] `created_at: Optional[str] = None` - ISO timestamp
  - [x] `last_accessed: Optional[str] = None` - ISO timestamp
- [x] Add `get_filesystem() -> FileSystem` method
- [x] Add `to_dict() -> dict` for serialization
- [x] Add `@classmethod from_dict(data: dict) -> Project`
- [x] Add validation in `__post_init__`:
  - [x] Validate `id` is slug-safe (alphanumeric + hyphens)
  - [x] Validate `type` is valid
  - [x] If type is "ssh", require `host`

### Step 2.2: Create ProjectManager

**Create:** `core/project_manager.py`

- [x] Define storage paths:
  - [x] `PROJECTS_PATH = ~/.mobius/projects.json`
  - [x] `SESSIONS_INDEX_PATH = ~/.mobius/sessions.json`
- [x] Implement `ProjectManager` class:
  - [x] `__init__()` - load from disk
  - [x] `_load()` - parse projects.json
  - [x] `_save()` - write projects.json with proper formatting
  - [x] `list() -> List[Project]` - all projects
  - [x] `get(project_id: str) -> Optional[Project]`
  - [x] `add(project: Project) -> None` - add and save
  - [x] `update(project: Project) -> None` - update existing
  - [x] `remove(project_id: str) -> bool` - remove and save
  - [x] `get_default() -> Project` - return default local project
  - [x] `set_default(project_id: str) -> None`
  - [x] `test_connection(project: Project) -> Tuple[bool, str]` - verify access
  - [x] `touch_accessed(project_id: str)` - update last_accessed timestamp

### Step 2.3: Create Session Index Manager

**In:** `core/project_manager.py` or separate `core/session_index.py`

- [x] Implement `SessionIndex` class:
  - [x] Track `original_project_id` per session
  - [x] Track `current_project_id` per session
  - [x] `get_sessions_for_project(project_id: str) -> List[str]`
  - [x] `set_session_project(session_id: str, project_id: str, is_original: bool)`
  - [x] `get_session_info(session_id: str) -> dict`
  - [x] Persist to `sessions.json`

### Step 2.4: Auto-Create Default Local Project

**In:** `core/project_manager.py`

- [ ] On first load, if no projects exist:
  - [ ] Create default project with `id="local"`, `name="Local"`, `type="local"`, `path=cwd`
  - [ ] Save to projects.json
- [ ] Migration: handle existing sessions without project assignment

### Step 2.5: Integrate with Filesystem Module

**In:** `core/filesystem.py`

- [ ] Update `get_project(project_id: str)`:
  - [ ] Use `ProjectManager` to fetch project
  - [ ] Return default local project if not found
- [ ] Update `get_current_filesystem()`:
  - [ ] Call `get_project()` to get full project details
  - [ ] Call `project.get_filesystem()` to get appropriate implementation

### Step 2.6: Export from Core

**In:** `core/__init__.py`

- [ ] Export `Project`
- [ ] Export `ProjectManager`
- [ ] Export `SessionIndex`
- [ ] Export `FileSystem`, `LocalFileSystem`, `get_current_filesystem`

### Step 2.7: Testing Phase 2

- [ ] Test ProjectManager CRUD operations
- [ ] Verify projects.json is created correctly
- [ ] Test session index tracking
- [ ] Verify default project creation on fresh install
- [ ] Test `get_current_filesystem()` returns correct type

---

## Phase 3: SSH FileSystem Implementation

**Purpose:** Implement the SSH filesystem using system `ssh` command to leverage existing SSH config.

### Files to Focus
```
focus core/filesystem.py
focus core/project.py
focus core/project_manager.py
```

### Step 3.1: Implement SSHFileSystem

**In:** `core/filesystem.py`

- [x] Create `SSHFileSystem` class implementing `FileSystem`
- [x] Constructor parameters:
  - [x] `host: str` - hostname or SSH config alias
  - [x] `root: str` - remote project root path
  - [x] `user: Optional[str]` - username (optional if in config)
  - [x] `port: int = 22`
- [x] Build SSH command components:
  - [x] `_dest` - user@host or just host
  - [x] `_ssh_opts` - list of SSH options:
    - [x] `-o BatchMode=yes` (no password prompts)
    - [x] `-o ConnectTimeout=10`
    - [x] `-o StrictHostKeyChecking=accept-new`
    - [x] `-p {port}` if not 22
- [x] Implement `_ssh_cmd(remote_command: str, timeout: int) -> Tuple[str, int]`:
  - [x] Build full command: `ssh {opts} {dest} {remote_command}`
  - [x] Run via `subprocess.run()`
  - [x] Return stdout+stderr and exit code
  - [x] Handle `TimeoutExpired` exception
- [x] Implement `_remote_path(path: str) -> str`:
  - [x] Convert relative path to absolute using `self._root`

### Step 3.2: Implement SSHFileSystem Methods

**In:** `core/filesystem.py` (SSHFileSystem class)

- [x] `read(path)`:
  - [x] Use `cat '{remote_path}'`
  - [x] Raise `FileNotFoundError` on non-zero exit
- [x] `write(path, content)`:
  - [x] Create parent dir with `mkdir -p`
  - [x] Pipe content via stdin: `cat > '{remote_path}'`
  - [x] Use `subprocess.run(input=content)`
- [x] `delete(path)`:
  - [x] Use `rm '{remote_path}'`
- [x] `rename(old, new)`:
  - [x] Create parent of new path
  - [x] Use `mv '{old}' '{new}'`
- [x] `exists(path)`:
  - [x] Use `test -e '{path}'`
  - [x] Return `code == 0`
- [x] `is_file(path)`:
  - [x] Use `test -f '{path}'`
- [x] `is_dir(path)`:
  - [x] Use `test -d '{path}'`
- [x] `ls(path)`:
  - [x] Use `ls -la '{path}'`
  - [x] Parse output to extract name, is_dir, size
  - [x] Skip `.` and `..` entries
  - [x] Sort directories first
- [x] `mkdir(path, parents)`:
  - [x] Use `mkdir -p` or `mkdir` based on parents flag
- [x] `exec(command, cwd, timeout)`:
  - [x] Wrap command: `cd '{cwd}' && {command}`
  - [x] Return output and exit code
- [x] `walk(path)`:
  - [x] Use `find '{path}' -type f -o -type d`
  - [x] Parse output and yield like `os.walk`
  - [x] Consider implementing simpler version first

### Step 3.3: Add SSH Connection Pooling

**In:** `core/filesystem.py` (SSHFileSystem class)

- [x] Add ControlMaster support:
  - [x] Generate unique control path: `/tmp/mobius-ssh-{host}-{pid}`
  - [x] Add to `_ssh_opts`:
    - [x] `-o ControlPath={path}`
    - [x] `-o ControlMaster=auto`
    - [x] `-o ControlPersist=600` (10 min)
- [x] Implement `close()` method:
  - [x] Send exit command: `ssh -O exit -o ControlPath={path} {dest}`
  - [x] Clean up control socket file
- [x] Consider adding `__enter__` and `__exit__` for context manager support

### Step 3.4: SSH Error Handling

**In:** `core/filesystem.py`

- [ ] Create custom exceptions:
  - [ ] `SSHConnectionError` - cannot connect
  - [ ] `SSHAuthenticationError` - auth failed
  - [ ] `SSHTimeoutError` - operation timed out
  - [ ] `SSHPermissionError` - permission denied on remote
- [ ] Parse SSH error output to raise appropriate exceptions
- [ ] Add retry logic for transient failures (optional)

### Step 3.5: Update Project.get_filesystem()

**In:** `core/project.py`

- [ ] Import `LocalFileSystem` and `SSHFileSystem`
- [ ] In `get_filesystem()`:
  - [ ] If `type == "local"`: return `LocalFileSystem(Path(self.path))`
  - [ ] If `type == "ssh"`: return `SSHFileSystem(host, path, user, port)`

### Step 3.6: Add Connection Test to ProjectManager

**In:** `core/project_manager.py`

- [ ] Implement `test_connection(project: Project) -> Tuple[bool, str]`:
  - [ ] Get filesystem from project
  - [ ] Try `fs.ls(".")`
  - [ ] Return `(True, "Connected")` or `(False, error_message)`
  - [ ] Handle timeout gracefully
  - [ ] Close filesystem after test

### Step 3.7: Testing Phase 3

- [ ] Test SSH connection to configured host
- [ ] Test each SSHFileSystem method:
  - [ ] `ls` on remote directory
  - [ ] `read` remote file
  - [ ] `write` new remote file
  - [ ] `exists`, `is_file`, `is_dir`
  - [ ] `rename` and `delete`
  - [ ] `exec` command
  - [ ] `mkdir`
- [ ] Test connection pooling (multiple operations should reuse connection)
- [ ] Test error handling (wrong host, wrong path, permission denied)
- [ ] Test timeout behavior
- [ ] Verify `close()` cleans up properly

---

## Phase 4: Agent Integration & Project Switching

**Purpose:** Integrate project context into the Agent and enable mid-session project switching.

### Files to Focus
```
focus core/agent.py
focus core/filesystem.py
focus core/project.py
focus core/project_manager.py
focus HUD/file_tree.py
focus tools/prism_tools.py
```

### Step 4.1: Update Agent Constructor

**In:** `core/agent.py`

- [x] Add `project: Optional[Project] = None` parameter
- [x] In `__init__`:
  - [x] If no project provided, get default from `ProjectManager`
  - [x] Store `self.project`
  - [x] Save project ID to Signella: `_store.set('session', session_id, 'project_id', project.id)`
- [ ] Update `load_session()`:
  - [ ] Load project ID from Signella for that session
  - [ ] Load project from `ProjectManager`
  - [ ] Update `self.project`

### Step 4.2: Implement Project Switching

**In:** `core/agent.py`

- [ ] Add `switch_project(project: Project) -> None`:
  - [ ] Store old project reference
  - [ ] Update `self.project` and `self._filesystem`
  - [ ] Update Signella with new project ID
  - [ ] Add system message to history noting the switch
  - [ ] Clear focused files (they won't exist in new project)
  - [ ] Reset Prism session (set `_session = None` in prism_tools)
  - [ ] Close old filesystem if it has `close()` method

### Step 4.3: Update HUD Building

**In:** `core/agent.py`

- [ ] Update `_build_hud()`:
  - [ ] Add project context header:
    - [ ] Project name
    - [ ] Project type (local/ssh)
    - [ ] Project root path
    - [ ] Host (if SSH)
  - [ ] File tree should use `self._filesystem` for remote projects
  - [ ] Focused files should be relative to project root

### Step 4.4: Update FileTree for Remote Projects

**In:** `HUD/file_tree.py`

- [ ] Add optional `filesystem: FileSystem` parameter to `FileTree.__init__`
- [ ] If filesystem provided:
  - [ ] Use `fs.exec("git ls-files")` instead of `subprocess.run`
  - [ ] Handle case where git is not available on remote
  - [ ] Fallback to `fs.walk()` if git unavailable
- [ ] Keep backward compatibility (default to local behavior)

### Step 4.5: Update Prism Tools for Remote

**In:** `tools/prism_tools.py`

- [ ] Update `_get_prism_session()`:
  - [ ] Get current project from filesystem module
  - [ ] If project changed, create new session
  - [ ] Pass project root to PrismSession
- [ ] For SSH projects, use `RemotePrismSession` (Phase 5)
- [ ] For now, disable Prism for SSH projects with helpful message

### Step 4.6: Add Project Context to History Entries

**In:** `core/context_management/ground_truth.py`

- [ ] Update `Entry` meta to include:
  - [ ] `project_id: str`
  - [ ] `project_type: str`
  - [ ] `project_path: str`
- [ ] Update `HistoryManager.add_*` methods:
  - [ ] Accept optional `project_id` parameter
  - [ ] Default to current project from Signella

### Step 4.7: Testing Phase 4

- [ ] Test Agent creation with default project
- [ ] Test Agent creation with explicit project
- [ ] Test `switch_project()`:
  - [ ] Verify Signella is updated
  - [ ] Verify focus is cleared
  - [ ] Verify history entry is added
- [ ] Test HUD shows correct project info
- [ ] Test file operations work after project switch
- [ ] Test session loading preserves project context

---

## Phase 5: Prism Over SSH

**Purpose:** Enable dependency analysis for remote projects with caching to minimize SSH operations.

### Files to Focus
```
focus prism/session.py
focus prism/scanner.py
focus prism/parsers.py
focus prism/graph.py
focus tools/prism_tools.py
```

### Step 5.1: Create RemotePrismSession

**Create:** `prism/remote_session.py`

- [x] Import `SSHFileSystem` from core
- [x] Create `RemotePrismSession` class:
  - [x] Constructor takes `Project`
  - [x] Sets up filesystem and cache path
  - [x] Cache path: `~/.mobius/prism_cache/{project_id}.json`

### Step 5.2: Implement Cached Scanning

**In:** `prism/remote_session.py`

- [x] Implement `scan(force: bool = False) -> dict`:
  - [x] Check cache freshness (< 1 hour old)
  - [x] If cache valid and not force, load from cache
  - [x] Otherwise, perform full scan:
    - [x] Discover files
    - [x] Batch read contents
    - [x] Build graph
    - [x] Save to cache
  - [x] Return stats dict

### Step 5.3: Implement Batch File Discovery

**In:** `prism/remote_session.py`

- [x] Implement `_discover_files() -> List[str]`:
  - [x] Use single SSH command with `find`:
    ```
    find . -type f \( -name "*.py" -o -name "*.html" -o -name "*.js" -o -name "*.css" \)
        -not -path "*/.venv/*"
        -not -path "*/__pycache__/*"
        -not -path "*/node_modules/*"
    ```
  - [x] Parse output into list of paths
  - [x] Return relative paths

### Step 5.4: Implement Batch File Reading

**In:** `prism/remote_session.py`

- [x] Implement `_batch_read(files: List[str]) -> Dict[str, str]`:
  - [x] Process in batches of 100 files
  - [x] For each batch:
    - [x] Create tar archive on remote: `tar -cf - file1 file2 ... | base64`
    - [x] Transfer via SSH
    - [x] Decode base64 and extract tar locally
    - [x] Read contents from tar members
  - [x] Return dict of path -> content
  - [x] Handle encoding errors gracefully
  - [x] Fallback to individual reads if tar fails

### Step 5.5: Build Graph from Cached Content

**In:** `prism/remote_session.py`

- [x] Implement `_build_graph(files, contents) -> SimpleGraph`:
  - [x] Create nodes for each file
  - [x] Parse Python imports using AST
  - [x] Build edges based on imports
  - [x] Return populated graph

### Step 5.6: Implement Cache Persistence

**In:** `prism/remote_session.py`

- [x] Implement `_save_cache()`:
  - [x] Serialize graph to JSON
  - [x] Include timestamp
  - [x] Save to cache path
- [x] Implement `_load_cache() -> dict`:
  - [x] Load JSON from cache path
  - [x] Deserialize graph
  - [x] Return stats

### Step 5.7: Update Prism Tools

**In:** `tools/prism_tools.py`

- [x] Update `_get_prism_session()`:
  - [x] Get current project
  - [x] If `project.type == "ssh"`, use `RemotePrismSession`
  - [x] If `project.type == "local"`, use `PrismSession`
- [x] Add `rescan_project()` enhancement:
  - [x] Pass `force=True` to clear cache for remote projects

### Step 5.8: Testing Phase 5

- [x] Test file discovery on remote project (754 files found)
- [x] Test batch reading (754 files read via tar+base64)
- [x] Test cache creation and loading (221KB cache file)
- [x] Test cache invalidation with `rescan_project(force=True)`
- [x] Test graph building (imports resolved correctly)
- [x] Test dependency queries (`find_entry_points`, `get_dependency_info`, `trace_entry_point`)
- [x] Measure performance (0.01s from cache vs ~10s fresh scan)

---

## Phase 6: API & UI Integration

**Purpose:** Add REST API endpoints and update the web UI to support project management.

### Files to Focus
```
focus run_web.py
focus static/js/app.js
focus static/workspace/js/components/settings.js
focus static/workspace/js/core/workspace.js
focus static/workspace/css/variables.css
focus templates/index.html
focus templates/workspace.html
```

### Step 6.1: Add Project API Endpoints

**In:** `run_web.py`

- [ ] Import `ProjectManager` and `Project`
- [ ] Update `/api/projects`:
  - [ ] Return full project list with current project ID
  - [ ] Include connection status for SSH projects
- [ ] Add `POST /api/projects`:
  - [ ] Create new project from request body
  - [ ] Test connection before saving
  - [ ] Return created project or error
- [ ] Add `PUT /api/projects/<id>`:
  - [ ] Update existing project
  - [ ] Test connection if SSH settings changed
- [ ] Add `DELETE /api/projects/<id>`:
  - [ ] Prevent deleting default project
  - [ ] Remove project from storage
- [ ] Add `POST /api/projects/<id>/test`:
  - [ ] Test connection to specific project
  - [ ] Return success/failure with message
- [ ] Add `POST /api/projects/switch`:
  - [ ] Switch current session to different project
  - [ ] Call `agent.switch_project()`
  - [ ] Return new project details

### Step 6.2: Update Session API

**In:** `run_web.py`

- [ ] Update `/api/sessions`:
  - [ ] Include project info for each session
  - [ ] Add filter parameter: `?project=<id>`
- [ ] Update `/api/current-session`:
  - [ ] Include current project details
- [ ] Update session loading:
  - [ ] Load project context when loading session

### Step 6.3: Update SocketIO Events

**In:** `run_web.py`

- [ ] Add `project_switched` event:
  - [ ] Emit when project changes
  - [ ] Include new project details
- [ ] Update `focused_files_updated`:
  - [ ] Include project context
- [ ] Add connection status events for SSH projects:
  - [ ] `ssh_connected`
  - [ ] `ssh_disconnected`
  - [ ] `ssh_error`

### Step 6.4: Create Project Bar Component

**Create:** `static/workspace/js/components/project-bar.js`

- [ ] Replace Mobius logo area with project bar
- [ ] Show colored boxes for each open project: `[🟠 Mobius] [🔵 Agentech] [+]`
- [ ] Each box shows:
  - [ ] Project color as background/border
  - [ ] Project name (truncated if long)
- [ ] Active project is highlighted (brighter/border)
- [ ] Click box → switch to that project
- [ ] Click [+] → open "Add Project" menu
- [ ] Add Project menu (placeholder for now):
  - [ ] "Open Local Folder..."
  - [ ] "Connect via SSH..."
- [ ] When switching projects:
  - [ ] Update accent color throughout UI
  - [ ] Filter sessions sidebar to that project

### Step 6.5: Create Project Settings Panel

**Update:** `static/workspace/js/components/settings.js`

- [ ] Add "Projects" section
- [ ] List all projects with:
  - [ ] Edit button
  - [ ] Delete button (except default)
  - [ ] Test connection button (SSH only)
- [ ] Add "Add Project" button opening modal
- [ ] Project form fields:
  - [ ] Name (required)
  - [ ] Type (local/ssh radio)
  - [ ] Path (required)
  - [ ] For SSH:
    - [ ] Host (required)
    - [ ] User (optional, uses SSH config)
    - [ ] Port (optional, default 22)
  - [ ] Color picker

### Step 6.6: Update Workspace Layout

**In:** `static/workspace/js/core/workspace.js`

- [ ] Add project switcher to toolbar
- [ ] Update status bar with project info
- [ ] Handle `project_switched` event:
  - [ ] Update UI accent color
  - [ ] Clear chat messages (optional, configurable)
  - [ ] Refresh file tree
  - [ ] Update session list filter

### Step 6.7: Dynamic Color Theming

**In:** `static/workspace/css/variables.css`

- [ ] Add `--project-color` CSS variable
- [ ] Update components to use `--project-color`:
  - [ ] Sidebar accent
  - [ ] Toolbar project button
  - [ ] Focus bar
  - [ ] Active states
- [ ] Add project-specific color presets

**In:** `static/workspace/js/core/workspace.js`

- [ ] Update `setProject()`:
  - [ ] Set CSS variable: `document.documentElement.style.setProperty('--project-color', color)`

### Step 6.8: SSH Connection Indicators

**In:** `static/workspace/css/components/toolbar.css`

- [ ] Add styles for connection status:
  - [ ] `.connected` - green dot
  - [ ] `.disconnected` - red dot
  - [ ] `.connecting` - yellow pulsing dot

**In:** `static/workspace/js/components/project-switcher.js`

- [ ] Show connection status for SSH projects
- [ ] Update status on socket events

### Step 6.9: Update Legacy UI

**In:** `static/js/app.js` and `templates/index.html`

- [ ] Add project switcher to legacy interface
- [ ] Mirror functionality from workspace UI
- [ ] Ensure both UIs work consistently

### Step 6.10: Testing Phase 6

- [ ] Test all API endpoints with curl/Postman
- [ ] Test project creation flow in UI
- [ ] Test project switching:
  - [ ] Verify color changes
  - [ ] Verify file operations work
  - [ ] Verify focus is cleared
- [ ] Test SSH project:
  - [ ] Create new SSH project
  - [ ] Test connection
  - [ ] Switch to SSH project
  - [ ] Run file operations
- [ ] Test session filtering by project
- [ ] Test error states (connection failed, timeout)

---

## Phase 7: Accurate Token Counting

**Purpose:** Fix token counting discrepancy - our counter underestimates by ~25% compared to Anthropic's actual usage.

### Problem
- Current: Character-based estimation (chars ÷ 3.3)
- Observed: We report ~150k when Anthropic says ~200k
- Risk: Context overflow if we think we have room but don't

### Tasks
- [ ] Investigate proper tokenization for Claude (tiktoken doesn't work for Claude)
- [ ] Consider using Anthropic's token counting API if available
- [ ] Or calibrate our char-based counter with a better ratio
- [ ] Add proactive consolidation when approaching 80% of actual limit
- [ ] Verify counting matches API response token counts
- [ ] Ensure we never hit max context - trigger compaction before overflow

---

## Phase 8: Background Agents (Optional)

**Purpose:** Allow agents to continue processing after browser disconnect.

### Files to Focus
```
focus run_web.py
focus core/agent.py
```

### Step 7.1: Create AgentRunner

**Create:** `core/agent_runner.py`

- [ ] Implement `AgentRunner` class:
  - [ ] `_threads: Dict[str, Thread]` - active agent threads
  - [ ] `_queues: Dict[str, Queue]` - message queues per session
  - [ ] `_results: Dict[str, List]` - accumulated results
  - [ ] `start_background(session_id, message)` - start processing
  - [ ] `get_pending_results(session_id)` - get accumulated results
  - [ ] `is_running(session_id)` - check if processing
  - [ ] `cancel(session_id)` - stop processing

### Step 7.2: Implement Background Processing

**In:** `core/agent_runner.py`

- [ ] Implement `_run_agent(session_id, message)`:
  - [ ] Get or create agent for session
  - [ ] Process initial message, accumulate events
  - [ ] Process queued messages
  - [ ] Handle cancellation gracefully
  - [ ] Store final state

### Step 7.3: Integrate with Web Server

**In:** `run_web.py`

- [ ] Create global `AgentRunner` instance
- [ ] Update `send_message` handler:
  - [ ] If `background=True`, use `AgentRunner`
  - [ ] Otherwise, use existing synchronous flow
- [ ] Add reconnection handling:
  - [ ] On connect, check for pending results
  - [ ] Emit accumulated events
- [ ] Add status endpoint:
  - [ ] `GET /api/agent/status` - is agent running?

### Step 7.4: UI Integration

**In:** `static/workspace/js/components/chat.js`

- [ ] Handle reconnection:
  - [ ] On socket connect, request pending results
  - [ ] Render accumulated messages
- [ ] Show "processing in background" indicator
- [ ] Allow queuing messages while disconnected

### Step 7.5: Testing Phase 7

- [ ] Test background processing start
- [ ] Test message queuing
- [ ] Test reconnection and result retrieval
- [ ] Test cancellation
- [ ] Test concurrent agents in different sessions

---

## Post-Implementation Checklist

### Documentation
- [ ] Update CLAUDE.md with new architecture
- [ ] Document all new API endpoints
- [ ] Add SSH setup guide
- [ ] Document project configuration format
- [ ] Add troubleshooting guide for SSH issues

### Testing
- [ ] All unit tests pass
- [ ] Manual testing of all features
- [ ] Test with multiple SSH hosts
- [ ] Test error recovery scenarios
- [ ] Performance testing with large remote projects

### Cleanup
- [ ] Remove any debug logging
- [ ] Remove unused imports
- [ ] Run linter on all modified files
- [ ] Update requirements.txt if needed

### Security Review
- [ ] Verify paths are properly escaped in SSH commands
- [ ] Verify no credentials are logged
- [ ] Verify SSH key handling is secure
- [ ] Review timeout handling
- [ ] Check for command injection vulnerabilities

---

## Quick Reference: Focus Commands by Phase

```bash
# Phase 1: FileSystem Abstraction
focus core/signella.py
focus tools/tools.py
focus core/agent.py
focus core/code_edit.py

# Phase 2: Project Management
focus core/filesystem.py
focus core/signella.py
focus core/history.py
focus run_web.py

# Phase 3: SSH FileSystem
focus core/filesystem.py
focus core/project.py
focus core/project_manager.py

# Phase 4: Agent Integration
focus core/agent.py
focus core/filesystem.py
focus core/project.py
focus core/project_manager.py
focus HUD/file_tree.py
focus tools/prism_tools.py

# Phase 5: Prism Over SSH
focus prism/session.py
focus prism/scanner.py
focus prism/parsers.py
focus prism/graph.py
focus tools/prism_tools.py

# Phase 6: API & UI
focus run_web.py
focus static/js/app.js
focus static/workspace/js/components/settings.js
focus static/workspace/js/core/workspace.js
focus static/workspace/css/variables.css
focus templates/index.html
focus templates/workspace.html

# Phase 7: Background Agents
focus run_web.py
focus core/agent.py
```

---

## Rollback Plan

If issues arise during implementation:

1. **Phase 1 issues:** Revert `tools/tools.py` to use `Path` directly
2. **Phase 3 issues:** Disable SSH projects, keep local-only
3. **Phase 5 issues:** Disable Prism for SSH projects
4. **Phase 6 issues:** Hide project UI, use default project only

Each phase is designed to be independently revertable without breaking other functionality.
