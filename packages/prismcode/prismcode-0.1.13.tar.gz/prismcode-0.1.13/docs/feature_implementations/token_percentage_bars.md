# Token Percentage Bars - Feature Requirements

## Overview
Visual percentage bars showing relative token distribution across dependency tree files.

## Requirements

### 1. Relative Scaling (Not Absolute)
- **Current behavior**: Each file's bar shows its percentage of total tokens (e.g., 20 files = ~5% each = tiny bars)
- **Desired behavior**: Bars should be scaled relative to the largest file in the selection
- **Example**: If 5 files each have 20% of tokens, all bars should be full (100% width) since they're equal
- **Implementation**: Find the max token count among visible files, then scale each bar as `(file_tokens / max_tokens) * 100`

### 2. Unified Total Across Backend and Frontend Trees
- **Current behavior**: Backend dependencies and frontend dependencies calculate separate token totals
- **Desired behavior**: Both trees should share the same total token count
- **Implementation**: Calculate combined total from both `childrenTreeData` and `frontendTreeData`, pass this unified total to both render functions

### 3. Excluded Files Remove Tokens from Total
- **Current behavior**: When a file is deselected/excluded, the bar remains but is visually marked as excluded
- **Desired behavior**: Excluded files should:
  - Have their tokens removed from the total calculation
  - Have their percentage bar disabled/hidden or show 0%
  - Recalculate remaining files' percentages based on new total
- **Implementation**: Filter out excluded files when calculating totals, re-render bars when exclusion state changes

## Relevant Files

### JavaScript (UI Logic)
- `zdeps2/static/js/app.js`
  - `calculateAllTreeTokens()` - Line ~415 - Calculates total tokens for a tree
  - `calculateAllFrontendTokens()` - Line ~748 - Calculates total tokens for frontend tree
  - `renderChildrenPreview()` - Line ~372 - Renders backend dependency tree
  - `renderFrontendPreview()` - Line ~720 - Renders frontend dependency tree
  - `renderTreeNode()` - Line ~513 - Renders individual tree nodes with percentage bars
  - `renderFrontendTreeNode()` - Line ~765 - Renders frontend tree nodes with percentage bars
  - `excludedChildren` - Set tracking excluded backend files
  - `excludedFrontend` - Set tracking excluded frontend files

### CSS (Styling)
- `zdeps2/static/css/style.css`
  - `.tree-node-pct-bar` - Line ~1280 - Bar container styles
  - `.tree-node-pct-bar .pct-fill` - Line ~1290 - Bar fill styles

### Backend (Data Source)
- `prism/adapter.py`
  - `_build_children_tree_recursive()` - Line ~725 - Builds tree with token counts
  - Tree node structure includes: `path`, `name`, `lines`, `tokens`, `depth`, `children`, `connections`

## Implementation Notes

### For Relative Scaling
```javascript
// Instead of:
const pctBarWidth = (node.tokens / totalTokens) * 100;

// Use:
const maxTokens = findMaxTokensInTree(tree); // New function needed
const pctBarWidth = (node.tokens / maxTokens) * 100;
```

### For Unified Totals
```javascript
// In renderChildrenPreview and renderFrontendPreview:
const backendTokens = calculateAllTreeTokens(childrenTreeData);
const frontendTokens = includeFrontend ? calculateAllFrontendTokens(frontendTreeData) : 0;
const unifiedTotal = backendTokens + frontendTokens;
```

### For Exclusion Affecting Totals
```javascript
// Modify calculateAllTreeTokens to accept exclusion set:
function calculateAllTreeTokens(node, excludedPaths = new Set()) {
    let total = 0;
    if (!node.is_root && !excludedPaths.has(node.path)) {
        total += node.tokens || 0;
    }
    // ... recurse children
}
```
