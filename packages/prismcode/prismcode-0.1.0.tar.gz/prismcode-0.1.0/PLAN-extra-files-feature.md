# Extra Files & Code Size Bars Feature

## Summary
Add checkboxes to the sidebar file tree for selecting "extra files" to include in snapshots (independent of dependencies), and add universal code size bars (0-2000 lines scale, green→red gradient) to both the sidebar and dependency preview panels.

## Files to Modify

### Frontend
- `zdeps2/static/js/modules/state.js` - Add `extraFiles` Set
- `zdeps2/static/js/modules/tree.js` - Add checkboxes and code size bars to file rows
- `zdeps2/static/js/modules/children-preview.js` - Replace token-based bars with line-based bars
- `zdeps2/static/js/modules/frontend-preview.js` - Same bar change
- `zdeps2/static/js/modules/snapshot.js` - Include extra files in API call
- `zdeps2/static/css/style.css` - Add checkbox styles, color gradient bars

### Backend
- `prism/models.py` - Add `extra_files` to `SnapshotConfig`
- `prism/snapshot.py` - Add "EXTRA FILES" section to snapshot output
- `zdeps2/api/routes_prism.py` - Accept `extra_files` parameter
- `prism/adapter.py` - Pass `extra_files` to snapshot builder, **add `_lines` to tree nodes**

---

## Implementation Steps

### 1. State Management (`state.js`)
Add new state property:
```javascript
extraFiles: new Set(),  // Paths of manually selected extra files
```

### 2. Sidebar Tree Checkboxes & Bars (`tree.js`)

Modify `renderTree()` file row to include checkbox + size bar:

```javascript
// File row template - add checkbox before toggle, add size bar before badges
<input type="checkbox" class="extra-file-checkbox"
       onclick="event.stopPropagation(); toggleExtraFile('${data._path}')"
       ${state.extraFiles.has(data._path) ? 'checked' : ''}>
...
${getCodeSizeBar(data._lines)}
```

Add helper functions:
```javascript
function getCodeSizeBar(lines) {
    const maxLines = 2000;
    const pct = Math.min((lines / maxLines) * 100, 100);
    const color = getLineCountColor(lines);
    return `<span class="code-size-bar" title="${lines} lines">
        <span class="code-size-fill" style="width:${pct}%;background:${color}"></span>
    </span>`;
}

function getLineCountColor(lines) {
    if (lines < 1000) return '#3fb950';  // green
    if (lines >= 2000) return '#f85149'; // red
    // Gradient: green(1000) → orange(1500) → red(2000)
    const ratio = (lines - 1000) / 1000;
    if (ratio < 0.5) {
        return `rgb(${Math.round(63 + 192 * ratio * 2)}, ${Math.round(185 - 50 * ratio * 2)}, 80)`;
    } else {
        return `rgb(255, ${Math.round(135 - 100 * (ratio - 0.5) * 2)}, ${Math.round(80 - 31 * (ratio - 0.5) * 2)})`;
    }
}

export function toggleExtraFile(path) {
    if (state.extraFiles.has(path)) {
        state.extraFiles.delete(path);
    } else {
        state.extraFiles.add(path);
    }
    renderTree(state.treeData.tree);
}
window.toggleExtraFile = toggleExtraFile;
```

### 3. Dependency Preview Bars (`children-preview.js`)

Replace token-based scaling with fixed 2000-line scale:

```javascript
// Line ~249-252 - change from token-based to line-based
const maxLines = 2000;
const pctBarWidth = Math.min((node.lines || 0) / maxLines * 100, 100);
const barColor = getLineCountColor(node.lines || 0);
```

Update bar HTML to use dynamic color:
```javascript
<span class="pct-fill" style="width:${pctBarWidth}%;background:${barColor}"></span>
```

Remove `totalTokens` parameter from `renderTreeNode()` signature and calls.

### 4. Frontend Preview Bars (`frontend-preview.js`)

Same changes as children-preview.js.

### 5. Snapshot API Call (`snapshot.js`)

Add extra files to request body in `copySnapshot()` and `generateSnapshotForChat()`:
```javascript
extra_files: Array.from(state.extraFiles)
```

### 6. Backend: SnapshotConfig (`prism/models.py`)

Add field:
```python
extra_files: Set[str] = field(default_factory=set)
```

### 7. Backend: Snapshot Builder (`prism/snapshot.py`)

In `build_snapshot()`, after frontend section (~line 183):

```python
# Get extra files
extra_nodes = []
if config.extra_files:
    for extra_path in config.extra_files:
        extra_full = self.project_root / extra_path
        extra_node = graph.get_node(extra_full)
        if extra_node:
            extra_nodes.append(extra_node)

if extra_nodes:
    output_parts.append("# " + "=" * 68)
    output_parts.append("# EXTRA FILES (MANUALLY SELECTED)")
    output_parts.append("# " + "=" * 68)
    output_parts.append("")

    for node in extra_nodes:
        content = self._read_file(node.path)
        total_lines += node.lines
        file_metrics.append({
            "path": node.relative_path,
            "lines": node.lines,
            "type": "extra"
        })
        output_parts.append(f"# --- START FILE: {node.relative_path} ({node.lines} lines) ---")
        output_parts.append(content)
        output_parts.append(f"# --- END FILE: {node.relative_path} ---")
        output_parts.append("")
```

Update `_build_header()` to include extra files:
```python
if extra_nodes:
    lines.append(f"Extra Files: {len(extra_nodes)} files")
```

### 8. Backend: Routes (`zdeps2/api/routes_prism.py`)

Add to options dict (~line 191):
```python
"extra_files": set(data.get("extra_files", [])),
```

### 9. Backend: Adapter (`prism/adapter.py`)

In `generate_snapshot_prism()`, add to SnapshotConfig:
```python
extra_files=set(options.get("extra_files", [])),
```

### 10. CSS Styles (`zdeps2/static/css/style.css`)

```css
/* Extra file checkbox in sidebar */
.extra-file-checkbox {
    width: 14px;
    height: 14px;
    margin-right: 4px;
    cursor: pointer;
    accent-color: #238636;
    flex-shrink: 0;
}

/* Code size bar (universal 0-2000 lines) */
.code-size-bar {
    width: 40px;
    height: 6px;
    background: #21262d;
    border-radius: 3px;
    overflow: hidden;
    margin-left: 8px;
    flex-shrink: 0;
}

.code-size-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.2s ease;
}
```

---

### 11. Add `_lines` to Tree Nodes (`prism/adapter.py`)

In `build_file_tree_compat()` function (~line 253), add `_lines`:

```python
current[filename] = {
    "_type": "file",
    "_path": node.relative_path,
    "_lines": node.lines,  # ADD THIS
    "_orphan": is_orphan,
    "_entry_point": is_entry,
    "_connections": connections,
    "_connection_paths": connection_paths,
}
```

---

## Notes
- Color gradient: green (#3fb950) → orange (#ff8c00) → red (#f85149)
