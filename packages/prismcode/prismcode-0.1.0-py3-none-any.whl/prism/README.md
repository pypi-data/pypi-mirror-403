# Prism - Clean Dependency Analysis Engine

Prism is a modular, session-based dependency analysis engine for Python projects with support for frontend files (HTML, JS, CSS).

## Architecture Philosophy

### Key Improvements Over `zdeps2`

1. **No Global State**: Each `PrismSession` is independent and can analyze different projects simultaneously
2. **Unified Graph**: Python, HTML, JS, and CSS files are all nodes in a single graph structure
3. **On-Demand Analysis**: No aggressive pre-caching; analysis happens when you request it
4. **Clean Separation**: Scanner, Parser, Graph, and Snapshot Builder are independent components
5. **Strategy Pattern**: Different file types use different parsing strategies, but share the same interface

## Module Overview

### `models.py` - Data Structures
- `Node`: Represents a file in the graph (Python, HTML, JS, CSS)
- `Edge`: Represents a dependency relationship between two nodes
- `NodeType`: Enum for file types (PYTHON, HTML, JAVASCRIPT, CSS, etc.)
- `EdgeType`: Enum for dependency types (IMPORT, TEMPLATE, SCRIPT, etc.)
- `EntryPoint`: Configuration for project entry points
- `SnapshotConfig`: Configuration for snapshot generation

### `scanner.py` - File Discovery
- `FileScanner`: Scans project directories for relevant files
  - Supports parallel scanning for large projects
  - Handles exclude patterns and git submodules
  - Auto-detects template and static folders

### `parsers.py` - Dependency Extraction
- `ParserStrategy`: Abstract base class for file parsers
- `PythonParser`: AST-based Python import extraction
  - Detects static imports (`import`, `from ... import`)
  - Detects dynamic imports (`importlib.import_module`, `__import__`)
  - Detects Flask/FastAPI template references (`render_template`)
- `HTMLParser`: Regex-based HTML/Jinja2 parsing
  - Extracts `<script>` and `<link>` tags
  - Extracts Jinja2 `{% include %}` and `{% extends %}`
  - Handles Flask `url_for('static')` references
- `JavaScriptParser`: ES6 and CommonJS import extraction
- `CSSParser`: CSS `@import` extraction
- `PathResolver`: Resolves reference strings to actual file paths

### `graph.py` - Dependency Graph
- `DependencyGraph`: Core graph data structure
  - Maintains forward index (node → children)
  - Maintains reverse index (node → parents)
  - BFS-based tracing from entry points
  - Orphan detection
  - Entry point suggestion based on tree size

### `snapshot.py` - Formatted Output
- `SnapshotBuilder`: Generates formatted dependency snapshots
  - Includes parents, target, children, and frontend files
  - Supports chain tracing to entry points
  - Token-limited child selection
  - Metrics generation (lines, tokens, file counts)

### `session.py` - Main Interface
- `PrismSession`: The primary API for users
  - `scan()`: Build the dependency graph
  - `get_entry_points()`: Suggest entry points
  - `get_dependency_graph()`: Get parents/children for a file
  - `create_snapshot()`: Generate formatted snapshot
  - `trace_from_entry_point()`: Trace all dependencies
  - `get_orphans()`: Find unconnected files

## Usage Examples

### Basic Analysis

```python
from prism import PrismSession

# Create a session for your project
session = PrismSession("/path/to/project")

# Scan and build the dependency graph
stats = session.scan()
print(f"Scanned {stats['total_files']} files")

# Get suggested entry points
entry_points = session.get_entry_points(top_n=10)
for ep in entry_points:
    print(f"{ep['path']} - {ep['deps']} dependencies")

# Get dependency info for a specific file
deps = session.get_dependency_graph(
    target_file="backend/api/routes.py",
    parent_depth=2,
    child_depth=3
)
print(f"Parents: {len(deps['parents'])}")
print(f"Children: {len(deps['children'])}")
```

### Snapshot Generation

```python
from prism import PrismSession, SnapshotConfig

session = PrismSession("/path/to/project")
session.scan()

# Create a snapshot with custom configuration
config = SnapshotConfig(
    target_path="backend/api/app.py",
    parent_depth=1,
    child_depth=2,
    include_frontend=True
)

snapshot = session.create_snapshot(config)
print(snapshot['content'])  # Formatted snapshot text
print(f"Total tokens: {snapshot['metrics']['token_estimate']}")
```

### Multi-Project Support

```python
from prism import PrismSession

# Analyze multiple projects simultaneously
project1 = PrismSession("/path/to/project1")
project2 = PrismSession("/path/to/project2")

project1.scan()
project2.scan()

# Each session maintains its own state
stats1 = project1.get_stats()
stats2 = project2.get_stats()
```

### Entry Point Tracing

```python
from prism import PrismSession

session = PrismSession("/path/to/project")
session.scan()

# Trace all dependencies from an entry point
trace = session.trace_from_entry_point("main.py")
print(f"Connected files: {trace['total_connected']}")

# Find orphan files
orphans = session.get_orphans([
    {"path": "main.py", "label": "Main", "enabled": True}
])
print(f"Orphan files: {orphans['total_orphans']}")
```

## Design Patterns Used

### Strategy Pattern
Different file types use different parsing strategies (`PythonParser`, `HTMLParser`, etc.), but all implement the same `ParserStrategy` interface.

### Builder Pattern
`SnapshotBuilder` constructs complex formatted output step by step.

### Graph Pattern
`DependencyGraph` uses adjacency lists (forward/reverse indexes) for efficient graph traversal.

### Session Pattern
`PrismSession` encapsulates all state for a single project analysis, preventing global state pollution.

## Comparison with zdeps2

| Aspect | zdeps2 | Prism |
|--------|--------|-------|
| State Management | Global `_cache` variable | Session-based (per project) |
| Multi-Project | No (singleton cache) | Yes (multiple sessions) |
| Graph Structure | Separate Python/Frontend indexes | Unified graph for all file types |
| Parser Design | Procedural functions | Strategy pattern with classes |
| Dependency Tracing | Scattered across modules | Centralized in `DependencyGraph` |
| API Surface | Mix of functions and cache access | Clean `PrismSession` interface |
| Testing | Difficult (global state) | Easy (isolated sessions) |

## Performance Considerations

1. **Parallel Scanning**: Large projects (>50 files, >4 directories) use parallel processing
2. **Lazy Analysis**: Graph is built on `scan()`, not at session creation
3. **No Aggressive Caching**: Results are computed on-demand
4. **Token Counting**: Uses tiktoken for accurate token estimates

## Future Extensions

The modular architecture makes it easy to add:
- New file types (e.g., TypeScript, Vue, Svelte)
- New parsers (e.g., better JS/CSS analysis)
- New output formats (JSON, GraphML, DOT)
- Incremental updates (re-scan only changed files)
- MCP (Model Context Protocol) integration
