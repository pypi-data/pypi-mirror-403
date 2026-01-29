# ZDEPS/Prism - Python Dependency Analyzer & Visualizer

A web-based tool for analyzing Python project dependencies, visualizing file relationships, identifying orphaned code, and generating context snapshots for LLMs.

## Core Concept

You define **entry points** (main.py, api.py, etc.) and the tool traces all imports recursively to show which files are connected. Files not reachable from any entry point are "orphans" - potentially dead code.

## Key Features

- **Dependency tree visualization** with collapsible folders
- **Entry point tracing** - see how files connect to your main scripts
- **Orphan detection** - find unreachable/dead code
- **Frontend tracking** - follows Python → HTML templates → JS/CSS
- **Snapshot generation** - bundle a file + its dependencies for LLM context
- **Token counting** - know how much context you're using
- **Chat integration** - talk to Claude about the code with dependency context

---

## Architecture

Two layers: **Prism** (core analysis engine) and **zdeps2** (Flask web UI).

### Entry Point
| File | Purpose |
|------|---------|
| `run_prism.py` | Starts the web server on port 5052 |

### Prism Core (Analysis Engine)

| File | Purpose |
|------|---------|
| `prism/session.py` | Main controller - orchestrates scanning, parsing, graph building. One session per project. |
| `prism/scanner.py` | File discovery - walks directories, respects excludes, finds templates/static folders, detects git submodules |
| `prism/parsers.py` | AST-based Python parser + regex parsers for HTML/JS/CSS. Extracts imports, render_template() calls, script tags, etc. |
| `prism/graph.py` | Adjacency list graph with forward/reverse indexes. BFS tracing, orphan detection, entry point suggestions |
| `prism/snapshot.py` | Generates formatted text dumps of file + dependencies for clipboard/LLM |
| `prism/models.py` | Data classes: Node, Edge, EntryPoint, SnapshotConfig. EdgeType enum (IMPORT, TEMPLATE, SCRIPT, etc.) |
| `prism/config.py` | JSON config management - multi-project support, recent projects, entry points per project |
| `prism/adapter.py` | Bridges Prism to the Flask API. Converts between Prism objects and JSON-friendly dicts |
| `prism/cleaner.py` | Orphan deletion - removes unreachable files and empty folders |

### Web UI (Flask + Vanilla JS)

| File | Purpose |
|------|---------|
| `zdeps2/__main_prism__.py` | Flask app bootstrap |
| `zdeps2/api/app_prism.py` | Flask app factory |
| `zdeps2/api/routes_prism.py` | All API endpoints - /api/data, /api/copy-snapshot, /api/preview-children, /api/chat, etc. |
| `zdeps2/core/config.py` | Duplicate of prism/config.py (legacy, being phased out) |
| `zdeps2/templates/index.html` | Single-page app shell |

### Frontend Modules (ES6)

| File | Purpose |
|------|---------|
| `static/js/app-modular.js` | Module loader - imports and initializes everything |
| `static/js/modules/state.js` | Global state object (selectedFile, excludedChildren, filters, etc.) |
| `static/js/modules/data.js` | Fetches /api/data, updates stats/legend/filters |
| `static/js/modules/tree.js` | Renders sidebar file tree with badges and expand/collapse |
| `static/js/modules/file-details.js` | Right panel - shows connections, copy controls when file selected |
| `static/js/modules/children-preview.js` | Dependency tree with checkboxes for selective inclusion |
| `static/js/modules/frontend-preview.js` | HTML/JS/CSS dependency tree |
| `static/js/modules/snapshot.js` | Calls /api/copy-snapshot, copies to clipboard |
| `static/js/modules/settings.js` | Entry point management, project switching, submodule toggles |
| `static/js/modules/context-menu.js` | Right-click "Add as Entry Point" |
| `static/js/modules/ui.js` | Search box, sidebar resizer |
| `static/css/style.css` | All styling (dark theme, tree nodes, modals) |

### Utilities

| File | Purpose |
|------|---------|
| `claude_api.py` | Anthropic API wrapper for chat feature |

---

## Data Flow

1. **Scan**: `FileScanner` walks project, finds all .py/.html/.js/.css files
2. **Parse**: Each file parsed for imports → list of (reference, EdgeType) tuples
3. **Resolve**: References resolved to actual file paths
4. **Graph**: Nodes (files) and Edges (imports) added to `DependencyGraph`
5. **Trace**: BFS from entry points marks connected files, builds connection paths
6. **Render**: Flask serves JSON, frontend builds interactive tree

## Key Concepts to Understand

- **Connection paths**: The chain of imports from entry point → target file (e.g., main.py → api.py → routes.py → database.py)
- **Edge types**: IMPORT (static), DYNAMIC_IMPORT (importlib), STRING_REF (string that looks like module), TEMPLATE (render_template), SCRIPT/STYLESHEET (HTML refs)
- **Excluded children**: When generating snapshots, you can uncheck files to exclude them. Excluding a parent auto-excludes all its children (inherited exclusion)
- **Token budget**: Snapshot generator can limit children by token count, prioritizing by depth

## Config Storage

`zdeps2/zdeps2_config.json` stores:
- Current project path
- Recent projects list
- Per-project entry points (path, label, color, emoji, enabled)
- Per-project excluded submodules
- Global exclude patterns (\_\_pycache\_\_, .venv, etc.)