// ============================================================================
// Children Preview - Dependency tree preview in detail panel
// ============================================================================

import { state } from './state.js';
import { getLineCountColor } from './tree.js';

// Note: renderFrontendPreview and findMaxTokensInFrontendTree accessed via window.*
// to avoid circular dependency with frontend-preview.js

export function previewChildren() {
    if (!state.selectedFile) return;
    const previewEl = document.getElementById('children-preview');
    previewEl.innerHTML = '<div class="children-tree-loading">Loading...</div>';

    fetch('/api/preview-children', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: state.selectedFile._path })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            previewEl.innerHTML = `<div class="children-tree-empty" style="color:#f85149;">${data.error}</div>`;
            return;
        }
        state.childrenData = data.children;
        state.childrenTreeData = data.tree;
        renderChildrenPreview();
    });
}

export function renderChildrenPreview() {
    const previewEl = document.getElementById('children-preview');
    if (!state.childrenTreeData || !state.childrenTreeData.children || state.childrenTreeData.children.length === 0) {
        previewEl.innerHTML = '<div class="children-tree-empty">No children found</div>';
        return;
    }

    const totals = calculateTreeTotals(state.childrenTreeData);
    const maxDepth = getMaxDepth(state.childrenTreeData);

    // Build depth buttons
    let depthBtns = '<span class="depth-btns"><span style="font-size:10px;color:#6e7681;margin-right:4px;">Depth:</span>';
    for (let d = 1; d <= Math.min(maxDepth, 6); d++) {
        depthBtns += `<button class="depth-btn" onclick="selectToDepth(${d})" title="Select only depth 1-${d}">${d}</button>`;
    }
    if (maxDepth > 6) {
        depthBtns += `<button class="depth-btn" onclick="selectToDepth(${maxDepth})" title="Select all depths">∞</button>`;
    }
    depthBtns += '</span>';

    let html = `<div class="children-tree-box">
        <div class="children-tree-header">
            <div class="children-tree-header-row">
                <h4>Dependencies Tree</h4>
                <span class="children-tree-totals">${totals.included}/${totals.total} files | ${totals.lines.toLocaleString()} lines | ${totals.tokens.toLocaleString()} tokens</span>
                <span class="code-size-label">Code Size</span>
            </div>
            <div class="children-tree-header-row">
                <div class="children-tree-controls">
                    <button class="tree-control-btn" onclick="selectAllChildren()">✓ All</button>
                    <button class="tree-control-btn" onclick="selectNoneChildren()">✗ None</button>
                    ${depthBtns}
                </div>
            </div>
        </div>
        <div class="children-tree-content">
            ${renderTreeNode(state.childrenTreeData, [], true, false, false)}
        </div>
    </div>`;

    previewEl.innerHTML = html;
}

export function calculateAllTreeTokens(node, excludedPaths = new Set(), ancestorExcluded = false) {
    let total = 0;
    const isExcluded = excludedPaths.has(node.path) || ancestorExcluded;
    if (!node.is_root && !isExcluded) {
        total += node.tokens || 0;
    }
    for (const child of (node.children || [])) {
        total += calculateAllTreeTokens(child, excludedPaths, isExcluded);
    }
    return total;
}

export function findMaxTokensInTree(node, excludedPaths = new Set(), ancestorExcluded = false) {
    let maxTokens = 0;
    const isExcluded = excludedPaths.has(node.path) || ancestorExcluded;
    if (!node.is_root && !isExcluded) {
        maxTokens = node.tokens || 0;
    }
    for (const child of (node.children || [])) {
        const childMax = findMaxTokensInTree(child, excludedPaths, isExcluded);
        if (childMax > maxTokens) maxTokens = childMax;
    }
    return maxTokens;
}

export function getMaxDepth(node, currentMax = 0) {
    if (!node.is_root && node.depth > currentMax) {
        currentMax = node.depth;
    }
    for (const child of (node.children || [])) {
        currentMax = getMaxDepth(child, currentMax);
    }
    return currentMax;
}

export function selectAllChildren() {
    state.excludedChildren = new Set();
    renderBothPreviews();
}

export function selectNoneChildren() {
    if (!state.childrenTreeData) return;
    state.excludedChildren = new Set();
    collectAllPaths(state.childrenTreeData, state.excludedChildren);
    renderBothPreviews();
}

export function selectToDepth(maxDepth) {
    if (!state.childrenTreeData) return;
    state.excludedChildren = new Set();
    collectPathsBeyondDepth(state.childrenTreeData, maxDepth, state.excludedChildren);
    renderBothPreviews();
}

export function collectAllPaths(node, paths) {
    if (!node.is_root && node.path) {
        paths.add(node.path);
    }
    for (const child of (node.children || [])) {
        collectAllPaths(child, paths);
    }
}

export function collectPathsBeyondDepth(node, maxDepth, paths) {
    if (!node.is_root && node.depth > maxDepth) {
        paths.add(node.path);
    }
    for (const child of (node.children || [])) {
        collectPathsBeyondDepth(child, maxDepth, paths);
    }
}

export function getDescendantPaths(node) {
    const paths = [];
    for (const child of (node.children || [])) {
        if (child.path) paths.push(child.path);
        paths.push(...getDescendantPaths(child));
    }
    return paths;
}

export function findNodeByPath(node, targetPath) {
    if (node.path === targetPath) return node;
    for (const child of (node.children || [])) {
        const found = findNodeByPath(child, targetPath);
        if (found) return found;
    }
    return null;
}

export function calculateTreeTotals(node, totals = null, ancestorExcluded = false) {
    if (!totals) totals = { total: 0, included: 0, lines: 0, tokens: 0 };

    const isDirectlyExcluded = state.excludedChildren.has(node.path);
    const isExcluded = isDirectlyExcluded || ancestorExcluded;

    if (!node.is_root) {
        totals.total++;
        if (!isExcluded) {
            totals.included++;
            totals.lines += node.lines || 0;
            totals.tokens += node.tokens || 0;
        }
    }

    for (const child of (node.children || [])) {
        calculateTreeTotals(child, totals, isExcluded);
    }

    return totals;
}

export function renderTreeNode(node, guides = [], isRoot = false, isLastSibling = false, ancestorExcluded = false) {
    if (isRoot) {
        let html = '';
        const children = node.children || [];
        children.forEach((child, idx) => {
            const isLast = idx === children.length - 1;
            html += renderTreeNode(child, [], false, isLast, false);
        });
        return html;
    }

    const isDirectlyExcluded = state.excludedChildren.has(node.path);
    const isInheritedExcluded = ancestorExcluded && !isDirectlyExcluded;
    const isExcluded = isDirectlyExcluded || ancestorExcluded;
    const hasChildren = node.children && node.children.length > 0;
    const nodeId = 'node-' + node.path.replace(/[^a-zA-Z0-9]/g, '-');

    let rowClass = 'tree-node-row';
    if (isDirectlyExcluded) {
        rowClass += ' excluded';
    } else if (isInheritedExcluded) {
        rowClass += ' inherited-excluded';
    }

    // Checkbox state
    let checkboxClass = 'tree-node-checkbox';
    let checkboxContent = '';
    if (isDirectlyExcluded) {
        checkboxContent = '';  // unchecked
    } else if (isInheritedExcluded) {
        checkboxClass += ' inherited-unchecked';
        checkboxContent = '';
    } else {
        checkboxClass += ' checked';
        checkboxContent = '✓';
    }

    let guidesHtml = '';
    for (const g of guides) {
        guidesHtml += `<span class="tree-node-guide ${g}"></span>`;
    }

    // Safe path for onclick (escape quotes)
    const safePath = node.path.replace(/'/g, "\\'");

    // Build connection dots HTML
    let connectionDots = '';
    if (node.connections && node.connections.length > 0) {
        connectionDots = '<span class="tree-node-connections">';
        for (const conn of node.connections) {
            connectionDots += `<span class="connection-dot" style="background:${conn.color};" title="${conn.label}"></span>`;
        }
        connectionDots += '</span>';
    }

    // Calculate percentage relative to 2000 lines (universal scale)
    const maxLines = 2000;
    const lines = node.lines || 0;
    const pctBarWidth = isExcluded ? 0 : Math.min((lines / maxLines) * 100, 100);
    const barColor = getLineCountColor(lines);

    // Get parent folder path (everything except filename)
    const pathParts = node.path.split('/');
    const folderPath = pathParts.length > 1 ? pathParts.slice(0, -1).join('/') : '';

    let html = `<div class="tree-node" id="${nodeId}">
        <div class="${rowClass}" onclick="toggleChildCascade('${safePath}')">
            <span class="tree-node-indent">${guidesHtml}<span class="tree-node-connector ${isLastSibling ? 'last' : ''}"></span></span>
            <span class="tree-node-toggle ${hasChildren ? '' : 'leaf'}" onclick="event.stopPropagation(); toggleTreeNode('${nodeId}')">▼</span>
            <span class="${checkboxClass}">${checkboxContent}</span>
            <span class="tree-node-icon">📄</span>
            <span class="tree-node-name" title="${node.path}">${node.name}</span>
            <span class="tree-node-folder-path" title="${node.path}">${folderPath}</span>
            ${connectionDots}
            <span class="tree-node-metrics">${node.lines} L</span>
            <span class="tree-node-pct-bar ${isExcluded ? 'excluded' : ''}" title="${lines} lines">
                <span class="pct-fill" style="width:${pctBarWidth}%;background:${barColor}"></span>
            </span>
        </div>`;

    if (hasChildren) {
        html += `<div class="tree-node-children" id="${nodeId}-children">`;
        const children = node.children;
        children.forEach((child, idx) => {
            const isLast = idx === children.length - 1;
            const newGuides = [...guides, isLastSibling ? 'empty' : '', isLast ? 'last' : ''];
            html += renderTreeNode(child, newGuides.filter(g => g), false, isLast, isExcluded);
        });
        html += '</div>';
    }

    html += '</div>';
    return html;
}

export function toggleTreeNode(nodeId) {
    const children = document.getElementById(nodeId + '-children');
    const toggle = document.querySelector(`#${nodeId} > .tree-node-row .tree-node-toggle`);
    if (children && toggle) {
        children.classList.toggle('collapsed');
        toggle.classList.toggle('collapsed');
    }
}

export function toggleChild(path) {
    if (state.excludedChildren.has(path)) {
        state.excludedChildren.delete(path);
    } else {
        state.excludedChildren.add(path);
    }
    renderBothPreviews();
}

export function toggleChildCascade(path) {
    // Find the node to get its descendants
    const node = findNodeByPath(state.childrenTreeData, path);
    if (!node) {
        toggleChild(path);
        return;
    }

    const isCurrentlyExcluded = state.excludedChildren.has(path);
    const descendants = getDescendantPaths(node);

    if (isCurrentlyExcluded) {
        // Include this node and all descendants
        state.excludedChildren.delete(path);
        for (const desc of descendants) {
            state.excludedChildren.delete(desc);
        }
    } else {
        // Exclude this node (descendants will be inherited-excluded automatically)
        state.excludedChildren.add(path);
        // Also remove any explicit exclusions on descendants (they inherit from parent)
        for (const desc of descendants) {
            state.excludedChildren.delete(desc);
        }
    }
    renderBothPreviews();
}

export function renderBothPreviews() {
    renderChildrenPreview();
    if (state.frontendTreeData && state.frontendTreeData.children && state.frontendTreeData.children.length > 0) {
        if (window.renderFrontendPreview) {
            window.renderFrontendPreview();
        }
    }
}

export function getAllExcludedPaths() {
    // Collect all paths that are excluded (directly or inherited)
    if (!state.childrenTreeData) return Array.from(state.excludedChildren);

    const allExcluded = new Set();
    function collectExcluded(node, ancestorExcluded) {
        const isDirectlyExcluded = state.excludedChildren.has(node.path);
        const isExcluded = isDirectlyExcluded || ancestorExcluded;

        if (!node.is_root && isExcluded) {
            allExcluded.add(node.path);
        }

        for (const child of (node.children || [])) {
            collectExcluded(child, isExcluded);
        }
    }
    collectExcluded(state.childrenTreeData, false);
    return Array.from(allExcluded);
}

// Make functions available globally for onclick handlers and cross-module access
window.selectAllChildren = selectAllChildren;
window.selectNoneChildren = selectNoneChildren;
window.selectToDepth = selectToDepth;
window.toggleTreeNode = toggleTreeNode;
window.toggleChildCascade = toggleChildCascade;
window.renderBothPreviews = renderBothPreviews;
window.findMaxTokensInTree = findMaxTokensInTree;
