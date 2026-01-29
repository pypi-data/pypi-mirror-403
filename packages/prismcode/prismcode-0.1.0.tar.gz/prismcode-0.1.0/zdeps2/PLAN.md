# ZDEPS2 Implementation Plan

## CRITICAL RULES
1. **DO NOT STOP** until all tasks are marked complete
2. At each checkpoint: RE-READ this plan AND the original `dependency_viewer.py`
3. Test each module before moving to the next
4. The UI must function EXACTLY as the original
5. API should be simplified - backend does heavy lifting, frontend just renders

---

## Phase 1: Foundation & Core Data Structures

### 1.1 Create Directory Structure
- [ ] Create `zdeps/zdeps2/` directory
- [ ] Create `zdeps/zdeps2/core/` for core modules
- [ ] Create `zdeps/zdeps2/api/` for Flask routes
- [ ] Create `zdeps/zdeps2/ui/` for templates
- [ ] Create `zdeps/zdeps2/__init__.py`
- [ ] Create `zdeps/zdeps2/core/__init__.py`
- [ ] Create `zdeps/zdeps2/api/__init__.py`

### 1.2 Config Module (`core/config.py`)
- [ ] Define `DEFAULT_CONFIG` dict (copy from original lines 32-90)
- [ ] Define `CONFIG_FILE` and `PROJECT_ROOT` paths
- [ ] Implement `load_config()` function
- [ ] Implement `save_config()` function
- [ ] Test: config loads and saves correctly

### 1.3 Tokenizer Module (`core/tokenizer.py`)
- [ ] Implement `count_tokens(text)` using tiktoken
- [ ] Implement `count_lines(filepath)` 
- [ ] Implement `read_file_content(filepath)`
- [ ] Test: token counting matches original

**CHECKPOINT 1**: Re-read PLAN.md and original dependency_viewer.py lines 1-250

---

## Phase 2: Scanner & Parser

### 2.1 Scanner Module (`core/scanner.py`)
- [ ] Implement `get_git_submodules(project_root)`
- [ ] Implement `detect_project_packages(project_root)`
- [ ] Implement `should_exclude(path, exclude_patterns, exclude_files)`
- [ ] Implement `scan_all_python_files(project_root, config)` - returns set of resolved paths
- [ ] Add multiprocessing for large directories
- [ ] Test: scans project correctly, excludes properly

### 2.2 Parser Module (`core/parser.py`)
- [ ] Copy `ImportExtractor` class (lines 120-182)
- [ ] Implement `get_all_imports(filepath, project_packages)` - returns (static, dynamic, potential)
- [ ] Implement `module_to_possible_paths(module, source_file, project_root)`
- [ ] Implement `expand_init_imports(init_path, project_packages)`
- [ ] Add caching with `@lru_cache` for repeated file parsing
- [ ] Test: import extraction matches original behavior

**CHECKPOINT 2**: Re-read PLAN.md and original dependency_viewer.py lines 200-400

---

## Phase 3: Core Tracing Engine

### 3.1 Tracer Module (`core/tracer.py`)
- [ ] Implement `trace_dependencies(entry_point, all_py_files, project_root, project_packages)`
  - Returns: (visited_set, connection_paths_dict, import_types_dict)
- [ ] Use BFS with deque (same as original)
- [ ] Track import types (static, dynamic, string_ref)
- [ ] Add parallel tracing for multiple entry points using ProcessPoolExecutor
- [ ] Test: tracing matches original results

### 3.2 Index Builder (`core/index.py`)
- [ ] Implement `build_reverse_index(all_py_files, project_packages)` 
  - Pre-computes "who imports X" for all files
  - Returns dict: {file_path: set(importers)}
- [ ] Implement `build_forward_index(all_py_files, project_packages)`
  - Pre-computes "what does X import" for all files
  - Returns dict: {file_path: set(imports)}
- [ ] Use multiprocessing for index building
- [ ] Test: indexes are correct and fast

**CHECKPOINT 3**: Re-read PLAN.md and original dependency_viewer.py lines 279-450

---

## Phase 4: Parent, Child, Chain Finding

### 4.1 Parents Module (`core/parents.py`)
- [ ] Implement `find_immediate_parents(target_path, reverse_index, connected_files=None)`
  - Uses pre-built reverse index (instant lookup)
- [ ] Implement `find_parents_to_depth(target_path, reverse_index, connected_files, depth)`
  - BFS traversal up to N levels
- [ ] Test: parent finding matches original, but faster

### 4.2 Children Module (`core/children.py`)
- [ ] Implement `find_children(target_path, forward_index)`
  - Uses pre-built forward index (instant lookup)
- [ ] Implement `get_all_children_recursive(target_path, forward_index, visited=None)`
- [ ] Implement `get_children_by_depth(target_path, forward_index, max_depth=None)`
  - Returns dict: {depth: [files]}
- [ ] Implement `get_children_with_token_limit(target_path, forward_index, max_tokens, excluded=None)`
- [ ] Implement `build_children_tree(target_path, forward_index)` - for UI preview
- [ ] Test: children finding matches original, but faster

### 4.3 Chains Module (`core/chains.py`)
- [ ] Implement `get_chain_to_entry_points(target_path, entry_points, connection_paths_cache)`
  - Uses cached connection paths from tracer
- [ ] Support `max_depth` truncation
- [ ] Test: chains match original

**CHECKPOINT 4**: Re-read PLAN.md and original dependency_viewer.py lines 2247-2400

---

## Phase 5: Snapshot Generator

### 5.1 Snapshot Module (`core/snapshot.py`)
- [ ] Implement `generate_snapshot(target_path, options)` where options includes:
  - parent_depth
  - include_chain
  - chain_length
  - child_depth
  - child_max_tokens
  - excluded_children
- [ ] Generate header section with summary
- [ ] Generate PARENTS section
- [ ] Generate TARGET section
- [ ] Generate CHILDREN section
- [ ] Generate footer with metrics
- [ ] Return: {content: str, metrics: dict}
- [ ] Test: output format matches original exactly

**CHECKPOINT 5**: Re-read PLAN.md and original dependency_viewer.py lines 2470-2700

---

## Phase 6: Tree Builder for UI

### 6.1 Tree Module (`core/tree.py`)
- [ ] Implement `build_file_tree(all_py_files, file_connections, project_root)`
  - Returns nested dict matching original structure
- [ ] Implement `calculate_folder_contents(node)` 
  - Aggregates badges up to folders
- [ ] Implement `flatten_tree_with_totals(tree_node)`
- [ ] Test: tree structure matches original JSON output

**CHECKPOINT 6**: Re-read PLAN.md and original dependency_viewer.py lines 400-500

---

## Phase 7: Analysis Orchestrator

### 7.1 Analyzer Module (`core/analyzer.py`)
- [ ] Implement `AnalysisCache` class to hold:
  - all_py_files
  - project_packages
  - reverse_index
  - forward_index
  - entry_point_traces (connection_paths per entry point)
  - file_tree
- [ ] Implement `run_full_analysis(config)` - builds everything
- [ ] Implement `get_cached_analysis()` - returns cached data
- [ ] Implement `invalidate_cache()` - for refresh
- [ ] Use ProcessPoolExecutor for parallel entry point tracing
- [ ] Test: full analysis completes and caches properly

**CHECKPOINT 7**: Re-read PLAN.md and original dependency_viewer.py lines 338-492

---

## Phase 8: API Layer

### 8.1 API Routes (`api/routes.py`)
- [ ] Implement `GET /` - serve HTML template
- [ ] Implement `GET /api/data` - return full analysis JSON
- [ ] Implement `GET /api/refresh` - invalidate cache, re-run analysis
- [ ] Implement `POST /api/entry-points` - add entry point
- [ ] Implement `DELETE /api/entry-points` - remove entry point
- [ ] Implement `GET /api/config` - return config
- [ ] Implement `POST /api/copy-snapshot` - generate snapshot
- [ ] Implement `POST /api/preview-children` - get children tree
- [ ] Test: all endpoints return correct data

### 8.2 Flask App (`api/app.py`)
- [ ] Create Flask app instance
- [ ] Register all routes
- [ ] Add CORS if needed
- [ ] Test: app starts and serves correctly

**CHECKPOINT 8**: Re-read PLAN.md and original dependency_viewer.py lines 2150-2210, 2472-2810

---

## Phase 9: UI (Copy Exactly)

### 9.1 HTML Template (`ui/template.html`)
- [ ] Copy entire HTML_TEMPLATE from original (lines 503-2148)
- [ ] Keep ALL styling exactly the same
- [ ] Keep ALL JavaScript exactly the same
- [ ] Only change: API endpoints if paths changed
- [ ] Test: UI renders identically to original

**CHECKPOINT 9**: Re-read PLAN.md and original dependency_viewer.py lines 503-2148

---

## Phase 10: Main Entry Point

### 10.1 Main Script (`__main__.py` or `server.py`)
- [ ] Import Flask app from api/app.py
- [ ] Add startup banner (same as original)
- [ ] Configure host/port
- [ ] Start server
- [ ] Test: `python -m zdeps.zdeps2` starts server

**CHECKPOINT 10**: Re-read PLAN.md and original dependency_viewer.py lines 2810-2819

---

## Phase 11: Performance Optimization

### 11.1 Multiprocessing
- [ ] Verify scanner uses multiprocessing for file discovery
- [ ] Verify parser uses process pool for AST parsing
- [ ] Verify index builder uses process pool
- [ ] Verify tracer uses process pool for multiple entry points
- [ ] Benchmark: measure time vs original

### 11.2 Caching
- [ ] Add LRU cache to frequently called functions
- [ ] Add file hash tracking for incremental updates
- [ ] Test: repeated requests are instant

**CHECKPOINT 11**: Run both original and zdeps2, compare speed

---

## Phase 12: Final Testing

### 12.1 Functional Tests
- [ ] Test: Select file, verify connections match original
- [ ] Test: Copy snapshot, verify output matches original format
- [ ] Test: Add entry point via UI
- [ ] Test: Remove entry point via UI
- [ ] Test: Search filtering works
- [ ] Test: Filter by entry point works
- [ ] Test: Filter by orphan works
- [ ] Test: Children preview shows correct tree
- [ ] Test: Excluding children works
- [ ] Test: Parent depth slider works
- [ ] Test: Chain toggle works
- [ ] Test: Token limit works

### 12.2 Performance Tests
- [ ] Benchmark: Initial load time
- [ ] Benchmark: Refresh time
- [ ] Benchmark: Snapshot generation time
- [ ] Compare all benchmarks to original

**CHECKPOINT 12**: Full comparison test - original vs zdeps2

---

## Phase 13: Cleanup

### 13.1 Code Quality
- [ ] Add docstrings to all public functions
- [ ] Add type hints to all functions
- [ ] Remove any debug prints
- [ ] Ensure consistent code style

### 13.2 Documentation
- [ ] Create README.md for zdeps2
- [ ] Document API endpoints
- [ ] Document module responsibilities

---

## COMPLETION CHECKLIST

Before marking complete, verify ALL of the following:

- [ ] All 13 phases complete
- [ ] All checkpoints passed
- [ ] UI looks identical to original
- [ ] UI functions identical to original
- [ ] Performance is equal or better than original
- [ ] All API endpoints work
- [ ] Snapshot output format matches original exactly
- [ ] No regressions from original functionality

---

## Current Status

**Phase**: Not Started
**Last Checkpoint**: None
**Blockers**: None

---

## Notes

(Add notes during implementation)

