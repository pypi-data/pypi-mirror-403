# ZDEPS2 JavaScript Modules

This document explains the modular JavaScript architecture for the ZDEPS2 dependency viewer.

## Architecture Overview

The application was refactored from a single 2,400-line `app.js` into 14 focused modules, each under 500 lines. All modules use ES6 imports/exports and share state through a central `state.js` module.

```
app-modular.js          <- Entry point, imports all modules
└── modules/
    ├── state.js        <- Shared state (imported by all)
    ├── data.js         <- API calls, data loading
    ├── tree.js         <- Sidebar file tree
    ├── file-details.js <- Detail panel rendering
    ├── context-menu.js <- Right-click menu
    ├── children-preview.js   <- Backend dependency tree
    ├── frontend-preview.js   <- Frontend dependency tree
    ├── snapshot.js     <- Copy to clipboard
    ├── settings.js     <- Settings modal
    ├── fullscreen-viewer.js  <- Full dependency modal
    ├── folder-browser.js     <- Folder picker modal
    ├── delete-orphans.js     <- Delete orphans modal
    ├── chat.js         <- Claude chat modal
    └── ui.js           <- Search, resizer
```

---

## Module Details

### `state.js` (60 lines)
**Purpose:** Central state store shared by all modules.

**Key State Variables:**
- `treeData` - Full tree data from `/api/data`
- `selectedFile` - Currently selected file in sidebar
- `currentFilter` / `searchQuery` - Sidebar filtering
- `excludedChildren` / `excludedFrontend` - Sets of paths excluded from snapshot
- `childrenTreeData` / `frontendTreeData` - Dependency tree data for preview
- `fullDepData` - Data for fullscreen viewer
- `chatHistory` - Chat message history

**Important:** All modules import `state` and read/write directly to it. This avoids prop drilling but means state mutations are not tracked.

---

### `data.js` (67 lines)
**Purpose:** Load data from API and update UI stats/filters.

**UI Components:**
- Stats bar (`.stats-bar`) - file counts
- Filter buttons (`.filters`) - All/Connected/Orphans + entry points
- Legend (`.legend`) - entry point colors

**Key Functions:**
| Function | Description |
|----------|-------------|
| `loadData()` | Fetches `/api/data`, updates stats, filters, renders tree |
| `refresh()` | Calls `/api/refresh` then `loadData()` |

**API Endpoints Used:**
- `GET /api/data` - Full tree structure

---

### `tree.js` (145 lines)
**Purpose:** Render the file tree in the sidebar.

**UI Components:**
- Tree container (`#tree`)
- Tree rows (`.tree-row`, `.file-row`, `.folder-row`)
- Badges showing entry point connections

**Key Functions:**
| Function | Description |
|----------|-------------|
| `renderTree(tree, container, depth)` | Recursively renders tree nodes |
| `getBadges(data)` | Returns HTML for connection badges |
| `shouldShowFile(data)` | Filter logic for search/filter |

**Important:** Tree rendering respects `state.searchQuery` and `state.currentFilter`. Folders auto-expand at depth 0.

---

### `file-details.js` (132 lines)
**Purpose:** Render the detail panel when a file is selected.

**UI Components:**
- Detail header (`#detail-header`)
- Detail content (`#detail-content`)
- Copy controls (`.copy-controls`)
- Connection cards showing import paths

**Key Functions:**
| Function | Description |
|----------|-------------|
| `selectFile(data, row)` | Called when file clicked, renders detail panel |

**Important:** Selecting a file triggers `previewChildren()` and `previewFrontend()` automatically.

---

### `context-menu.js` (37 lines)
**Purpose:** Right-click context menu on files.

**UI Components:**
- Context menu (`#context-menu`)
- Menu items for "Add as Entry Point" and "Copy Path"

**Key Functions:**
| Function | Description |
|----------|-------------|
| `showContextMenu(e, data)` | Positions and shows menu |
| `addAsEntryPoint()` | Opens add entry point modal |
| `copyPath()` | Copies file path to clipboard |

---

### `children-preview.js` (365 lines)
**Purpose:** Dependency tree preview in detail panel (Python backend files).

**UI Components:**
- Children preview container (`#children-preview`)
- Tree with checkboxes (`.tree-node`, `.tree-node-checkbox`)
- Depth buttons, Select All/None controls
- Percentage bars showing relative file size

**Key Functions:**
| Function | Description |
|----------|-------------|
| `previewChildren()` | Fetches `/api/preview-children`, renders tree |
| `renderTreeNode()` | Recursive tree node renderer with exclusion logic |
| `toggleChildCascade(path)` | Toggle file + all descendants |
| `selectToDepth(n)` | Exclude files beyond depth n |
| `getAllExcludedPaths()` | Returns all excluded paths (direct + inherited) |

**Important:** Exclusions cascade - excluding a parent automatically excludes all children visually (inherited exclusion). The `excludedChildren` Set only stores directly-excluded paths.

**API Endpoints Used:**
- `POST /api/preview-children` - Get dependency tree for a file

---

### `frontend-preview.js` (318 lines)
**Purpose:** Frontend file tree (HTML/JS/CSS referenced by Python templates).

**UI Components:**
- Frontend section (`#frontend-section`)
- Frontend preview (`#frontend-preview`)
- Include checkbox (`#include-frontend-check`)

**Key Functions:**
| Function | Description |
|----------|-------------|
| `previewFrontend()` | Fetches `/api/preview-frontend` |
| `toggleFrontendInclude()` | Toggle whether frontend included in snapshot |
| `getAllExcludedFrontendPaths()` | Returns excluded frontend paths |

**Important:** Frontend section only shows if the file has frontend dependencies. Must check "Include in snapshot" to include in copy.

**API Endpoints Used:**
- `POST /api/preview-frontend` - Get frontend dependencies

---

### `snapshot.js` (107 lines)
**Purpose:** Generate and copy code snapshots to clipboard.

**UI Components:**
- Copy button in detail panel
- Copy status (`#copy-status`)
- Copy metrics (`#copy-metrics`)

**Key Functions:**
| Function | Description |
|----------|-------------|
| `copySnapshot()` | Generates snapshot via API, copies to clipboard |
| `generateSnapshotForChat()` | Same as copy but returns content for chat |
| `toggleChain()` | Toggle chain inclusion |

**API Endpoints Used:**
- `POST /api/copy-snapshot` - Generate snapshot content

**Snapshot Parameters:**
- `parent_depth` - How many levels of parents to include
- `include_chain` - Include chain to entry points
- `child_depth` - Depth limit for children (0 = all)
- `excluded_children` - Paths to exclude
- `include_frontend` - Include frontend files

---

### `settings.js` (255 lines)
**Purpose:** Settings modal - entry points, submodules, project root.

**UI Components:**
- Settings modal (`#settings-modal`)
- Add entry point modal (`#add-entry-modal`)
- Entry point list (`#entry-point-list`)
- Suggestion list (`#suggestion-list`)
- Submodule list (`#submodule-list`)
- Color picker (`#color-picker`)

**Key Functions:**
| Function | Description |
|----------|-------------|
| `openSettings()` | Opens settings, loads entry points |
| `promptAddEntryPoint(path)` | Opens add entry modal |
| `saveEntryPoint()` | Saves new entry point |
| `toggleEntryPoint(path)` | Enable/disable entry point |
| `removeEntryPoint(path)` | Delete entry point |
| `loadSuggestions()` | Scan for potential entry points |
| `loadSubmodules()` | Load git submodules |
| `changeProjectRoot(path)` | Change project root directory |

**API Endpoints Used:**
- `GET /api/config` - Current config
- `POST /api/entry-points` - Add entry point
- `DELETE /api/entry-points` - Remove entry point
- `POST /api/entry-points/toggle` - Toggle entry point
- `GET /api/suggest-entry-points` - Scan for entry points
- `GET /api/submodules` - List submodules
- `POST /api/submodules/toggle` - Toggle submodule inclusion
- `POST /api/project-root` - Change project root

---

### `fullscreen-viewer.js` (467 lines)
**Purpose:** Full-screen dependency viewer with parents, chains, and children.

**UI Components:**
- Fullscreen overlay (`#fullscreen-viewer`)
- Target file info (`.dep-viewer-target`)
- Parents section with checkboxes
- Chain sections per entry point
- Children tree (reuses `renderTreeNode`)

**Key Functions:**
| Function | Description |
|----------|-------------|
| `openFullscreenViewer()` | Creates overlay, fetches full deps |
| `closeFullscreenViewer()` | Removes overlay |
| `fsSelectAll/None/ParentsOnly/ChildrenOnly()` | Bulk selection |
| `fsToggleParent/Chain/Children()` | Individual toggles |
| `copyFromFullscreen()` | Copy with current selections |

**API Endpoints Used:**
- `POST /api/full-dependencies` - Full dependency info

**Important:** This view shows ALL relationships - parents (who imports this), chains (path to entry points), and children (what this imports). Each section can be toggled independently.

---

### `folder-browser.js` (178 lines)
**Purpose:** Folder picker modal for changing project root.

**UI Components:**
- Folder browser modal (`#folder-browser-modal`)
- Path input with autocomplete (`#folder-path-input`)
- Breadcrumbs (`#breadcrumbs`)
- Folder list (`#folder-list`)
- Recent projects (`#recent-projects-list`)

**Key Functions:**
| Function | Description |
|----------|-------------|
| `openFolderBrowser()` | Opens modal at current project root |
| `navigateToFolder(path)` | Browse to directory |
| `handlePathInput()` | Autocomplete as user types |
| `selectCurrentFolder()` | Confirm selection |

**API Endpoints Used:**
- `POST /api/browse-directory` - List folder contents
- `POST /api/autocomplete-path` - Path autocomplete
- `GET /api/recent-projects` - Recent project history

---

### `delete-orphans.js` (159 lines)
**Purpose:** Dangerous action modal - delete orphan files.

**UI Components:**
- Delete modal (`#delete-orphans-modal`)
- Preview list of files to delete
- Confirmation input (type "DELETE")
- Progress/results display

**Key Functions:**
| Function | Description |
|----------|-------------|
| `openDeleteOrphansModal()` | Shows preview of orphan files |
| `validateDeleteConfirmation()` | Check if user typed DELETE |
| `executeOrphanDeletion()` | Actually delete files |

**API Endpoints Used:**
- `POST /api/orphans/preview-delete` - Preview what would be deleted
- `POST /api/orphans/delete` - Execute deletion

**Important:** This is DESTRUCTIVE and IRREVERSIBLE. Files are permanently deleted from disk. The confirmation "DELETE" must be typed exactly.

---

### `chat.js` (236 lines)
**Purpose:** Claude chat integration with code context.

**UI Components:**
- Chat modal (`#chat-modal`)
- Message container (`#chat-messages`)
- Input textarea (`#chat-input`)
- Context badge (`#chat-context-badge`)

**Key Functions:**
| Function | Description |
|----------|-------------|
| `openChatModal()` | Opens chat, generates snapshot for context |
| `sendChatMessage()` | Sends message with streaming response |
| `clearChatHistory()` | Reset conversation |
| `renderMarkdown(el, content)` | Render with syntax highlighting |

**API Endpoints Used:**
- `POST /api/chat` - Send message, receive streamed response

**Important:** Chat uses the current snapshot configuration as context. The snapshot is generated when modal opens. Supports SSE streaming for real-time responses.

**Dependencies:** Uses `marked` for markdown and `hljs` for syntax highlighting (loaded from CDN in HTML).

---

### `ui.js` (52 lines)
**Purpose:** Search and panel resizer functionality.

**UI Components:**
- Search input (`#search`)
- Resizer handle (`#resizer`)
- Sidebar (`.sidebar`)

**Key Functions:**
| Function | Description |
|----------|-------------|
| `initSearch()` | Setup search input listener |
| `initResizer()` | Setup drag-to-resize sidebar |

**Keyboard Shortcuts:**
- `Ctrl/Cmd + F` - Focus search input
- `Escape` - Close any open modal (handled in `fullscreen-viewer.js`)

---

## Global Window Functions

Many functions are exposed on `window` for inline `onclick` handlers in HTML:

```javascript
// From various modules - accessible globally
window.refresh()
window.loadData()
window.openSettings()
window.closeSettings()
window.copySnapshot()
window.openChatModal()
// ... etc
```

This is necessary because dynamically generated HTML (like tree nodes) can't import modules.

---

## State Flow

```
User clicks file in tree
    ↓
selectFile() sets state.selectedFile
    ↓
Renders detail panel with copy controls
    ↓
previewChildren() + previewFrontend() called
    ↓
API calls return dependency trees
    ↓
Trees rendered with checkboxes
    ↓
User toggles exclusions (updates state.excludedChildren)
    ↓
User clicks Copy
    ↓
copySnapshot() sends exclusions to API
    ↓
API returns formatted code
    ↓
Copied to clipboard
```

---

## Adding New Features

1. **New state:** Add to `state.js`
2. **New API call:** Add function to relevant module, update this README
3. **New modal:** Create new module, add open/close functions, expose on window
4. **New tree feature:** Likely goes in `children-preview.js` or `frontend-preview.js`

---

## Circular Dependency Handling

Some modules need to call functions from other modules that also depend on them. We resolve this by:

1. Functions that might cause cycles are accessed via `window.*` instead of imports
2. The main `app-modular.js` imports everything, ensuring all `window.*` assignments happen

Example: `delete-orphans.js` needs `closeSettings()` and `refresh()`, but importing from `settings.js` or `data.js` could cause cycles. Instead it uses `window.closeSettings()` and `window.refresh()`.

---

## Testing Changes

1. Update the HTML to load `app-modular.js` as a module:
   ```html
   <script type="module" src="/static/js/app-modular.js"></script>
   ```

2. Check browser console for import errors

3. Test each feature:
   - [ ] File tree loads and filters work
   - [ ] Clicking file shows detail panel
   - [ ] Dependency preview loads
   - [ ] Checkboxes toggle correctly
   - [ ] Copy to clipboard works
   - [ ] Settings modal opens/saves
   - [ ] Fullscreen viewer works
   - [ ] Chat sends/receives messages
   - [ ] Folder browser navigates
   - [ ] Search filters tree
   - [ ] Resizer drags correctly
