# Project Settings UI

This document describes the floating preferences modal and project management interface.

## Overview

The project settings UI is a Mac-style floating modal that allows users to:
- Add/edit/delete projects (local folders or SSH remotes)
- Browse local folders with VS Code-style autocomplete
- Manage SSH connection profiles
- Configure project colors for visual identification

## Key Files

### Frontend (Focus these)

| File | Purpose |
|------|---------|
| `static/workspace/js/components/preferences/index.js` | Modal container, tab switching, show/hide logic |
| `static/workspace/js/components/preferences/projects-pane.js` | **Main UI** - folder browser, SSH form, project list |
| `static/workspace/css/components/preferences.css` | All styling for the modal and projects pane |
| `static/workspace/js/components/project-bar.js` | Top bar with project boxes and `+` button |

### Backend (Need connection work)

| File | Purpose |
|------|---------|
| `run_web.py` | API endpoints (`/api/projects`, `/api/folders`, etc.) |
| `core/project_manager.py` | Project CRUD operations, persistence |
| `core/project.py` | Project model/dataclass |
| `core/filesystem.py` | Filesystem abstraction (local vs SSH) |

## Current State

### ✅ Implemented (Frontend)

1. **Floating Modal**
   - Opens via `+` button in project bar or `⚙` settings button
   - Keyboard shortcut: `⌘,` (Cmd+Comma)
   - Close via `✕`, click outside, or `Escape`
   - Size: 95% width, 90% height (max 1100x800px)

2. **Projects Pane Layout**
   - Left sidebar: existing projects list + SSH profiles
   - Right main area: add/edit form with Local/SSH tabs

3. **Local Folder Tab**
   - Path input with autocomplete dropdown
   - Breadcrumb navigation (click to go up)
   - Arrow key navigation in dropdown
   - Recent locations (stored in localStorage)
   - Project name (auto-fills from folder name)
   - Color picker (8 preset colors)

4. **SSH Remote Tab**
   - Quick connect from saved profiles
   - Full connection form (host, port, user, auth method)
   - SSH key path or password input
   - Test Connection button with loading state
   - Save as profile toggle
   - Project name and color

5. **API Endpoints**
   - `GET /api/folders?path=...` - returns directory listing
   - `GET /api/projects` - returns projects, ssh_profiles, home_dir
   - `POST /api/projects` - (partially implemented)
   - `DELETE /api/projects/<id>` - (not implemented)

### ✅ Now Connected (Backend)

1. **Project CRUD in `project_manager.py`**
   ```python
   pm = ProjectManager()
   pm.add(project)           # Create new project
   pm.update(project)        # Update existing project  
   pm.remove(project_id)     # Delete project
   pm.list_ssh_profiles()    # List saved SSH connection templates
   pm.save_ssh_profile(data) # Save SSH profile for reuse
   pm.get_ssh_profile(id)    # Get SSH profile by ID
   pm.delete_ssh_profile(id) # Delete SSH profile
   ```

2. **API Routes in `run_web.py`**
   ```python
   # POST /api/projects - create or update project
   @app.route('/api/projects', methods=['POST'])
   
   # DELETE /api/projects/<id> - delete project
   @app.route('/api/projects/<project_id>', methods=['DELETE'])
   
   # POST /api/ssh/test - test SSH connection
   @app.route('/api/ssh/test', methods=['POST'])
   
   # GET /api/folders?path=... - browse local folders
   @app.route('/api/folders')
   ```

3. **SSH Connection Testing**
   - Uses `SSHFileSystem` from `core/filesystem.py`
   - Tests by listing the remote directory
   - Returns success/failure with error message

4. **Project Persistence**
   - Projects saved to `~/.mobius/projects.json`
   - SSH profiles saved to `~/.mobius/ssh_profiles.json`

## Data Flow

```
User clicks "+" in project bar
        │
        ▼
bus.emit('open-preferences', {pane: 'projects'})
        │
        ▼
app.js listens, calls preferences.show()
        │
        ▼
ProjectsPane.load() fetches /api/projects
        │
        ▼
ProjectsPane.render() builds the UI
        │
        ▼
User types in path input
        │
        ▼
fetch('/api/folders?path=...') 
        │
        ▼
Dropdown shows folder contents
        │
        ▼
User clicks "Add Project"
        │
        ▼
fetch('/api/projects', {method: 'POST', body: {...}})
        │
        ▼
ProjectManager.add() saves to disk
        │
        ▼
UI refreshes, project appears in sidebar
```

## Frontend Events

| Event | Emitter | Listener | Purpose |
|-------|---------|----------|---------|
| `open-preferences` | project-bar.js | app.js | Open modal on specific pane |
| `project-switched` | project-bar.js | workspace.js | Update UI when project changes |

## localStorage Keys

| Key | Purpose |
|-----|---------|
| `mobius_recent_paths` | Array of recent folder paths `[{path, name, timestamp}]` |

## CSS Classes (for styling reference)

```css
/* Modal structure */
.prefs-overlay          /* Dark backdrop */
.prefs-modal            /* White modal box */
.prefs-header           /* Title bar */
.prefs-body             /* Content area */
.prefs-sidebar          /* Left nav tabs */
.prefs-content          /* Right content pane */

/* Projects pane */
.projects-layout        /* Two-column grid */
.projects-sidebar       /* Left: project list */
.projects-main          /* Right: form */
.project-type-tabs      /* Local/SSH switcher */

/* Folder browser */
.path-input-wrapper     /* Input container */
.path-input             /* Text input */
.path-browse-btn        /* Browse button */
.folder-dropdown        /* Autocomplete dropdown */
.folder-item            /* Single folder row */
.path-breadcrumbs       /* Clickable path */

/* SSH form */
.ssh-form-grid          /* Two-column form */
.ssh-profile-card       /* Saved profile box */
.test-connection-btn    /* Test button */
.connection-status      /* Success/error message */
```

## Implementation Status

All core features are now implemented:

1. ✅ **Project CRUD** - add, update, delete projects
2. ✅ **Local folder browser** - VS Code-style with path autocomplete
3. ✅ **SSH host detection** - reads from `~/.ssh/config`
4. ✅ **SSH command parsing** - paste `ssh -p 3333 user@host` and it auto-parses
5. ✅ **SSH folder browsing** - navigate remote folders after connecting
6. ✅ **Connection testing** - test SSH before adding project
7. ✅ **Project persistence** - saved to `~/.mobius/projects.json`

## New API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ssh/hosts` | GET | Get hosts from `~/.ssh/config` |
| `/api/ssh/parse` | POST | Parse SSH command string |
| `/api/ssh/test` | POST | Test SSH connection |
| `/api/ssh/browse` | POST | Browse remote folders |
| `/api/folders` | GET | Browse local folders |
