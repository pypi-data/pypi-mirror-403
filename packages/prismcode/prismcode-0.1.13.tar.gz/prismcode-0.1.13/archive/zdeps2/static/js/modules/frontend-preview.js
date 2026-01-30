// ============================================================================
// Frontend Preview - Frontend dependency tree (HTML/JS/CSS)
// ============================================================================

import { state } from './state.js';
import { getLineCountColor } from './tree.js';

// Note: findMaxTokensInTree and renderBothPreviews accessed via window.*
// to avoid circular dependency with children-preview.js

export function previewFrontend() {
    if (!state.selectedFile) return;
    const sectionEl = document.getElementById('frontend-section');
    const previewEl = document.getElementById('frontend-preview');
    const checkEl = document.getElementById('include-frontend-check');

    // Reset state
    if (checkEl) checkEl.checked = false;
    state.includeFrontend = false;

    fetch('/api/preview-frontend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: state.selectedFile._path })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            sectionEl.style.display = 'none';
            return;
        }
        state.frontendTreeData = data.tree;
        if (state.frontendTreeData && state.frontendTreeData.children && state.frontendTreeData.children.length > 0) {
            sectionEl.style.display = 'block';
            renderFrontendPreview();
        } else {
            sectionEl.style.display = 'none';
        }
    })
    .catch(() => {
        sectionEl.style.display = 'none';
    });
}

export function toggleFrontendInclude() {
    const checkEl = document.getElementById('include-frontend-check');
    state.includeFrontend = checkEl ? checkEl.checked : false;
}

export function renderFrontendPreview() {
    const previewEl = document.getElementById('frontend-preview');
    if (!state.frontendTreeData || !state.frontendTreeData.children || state.frontendTreeData.children.length === 0) {
        previewEl.innerHTML = '';
        return;
    }

    const totals = calculateFrontendTotals(state.frontendTreeData);

    let html = `<div class="frontend-tree-box">
        <div class="frontend-tree-header">
            <div class="children-tree-header-row">
                <h4>Front-End Files</h4>
                <span class="frontend-tree-totals">${totals.included}/${totals.total} files | ${totals.lines.toLocaleString()} L | ${totals.tokens.toLocaleString()} T</span>
                <span class="code-size-label">Code Size</span>
            </div>
            <div class="children-tree-header-row">
                <div class="children-tree-controls">
                    <button class="tree-control-btn" onclick="selectAllFrontend()">✓ All</button>
                    <button class="tree-control-btn" onclick="selectNoneFrontend()">✗ None</button>
                </div>
            </div>
        </div>
        <div class="children-tree-content">
            ${renderFrontendTreeNodes(state.frontendTreeData.children, [], false)}
        </div>
    </div>`;

    previewEl.innerHTML = html;
}

export function calculateAllFrontendTokens(node, excludedPaths = new Set(), ancestorExcluded = false) {
    let total = 0;
    const isExcluded = excludedPaths.has(node.path) || ancestorExcluded;
    if (!node.is_root && !isExcluded) {
        total += node.tokens || 0;
    }
    for (const child of (node.children || [])) {
        total += calculateAllFrontendTokens(child, excludedPaths, isExcluded);
    }
    return total;
}

export function findMaxTokensInFrontendTree(node, excludedPaths = new Set(), ancestorExcluded = false) {
    let maxTokens = 0;
    const isExcluded = excludedPaths.has(node.path) || ancestorExcluded;
    if (!node.is_root && !isExcluded) {
        maxTokens = node.tokens || 0;
    }
    for (const child of (node.children || [])) {
        const childMax = findMaxTokensInFrontendTree(child, excludedPaths, isExcluded);
        if (childMax > maxTokens) maxTokens = childMax;
    }
    return maxTokens;
}

function renderFrontendTreeNodes(nodes, guides, ancestorExcluded) {
    if (!nodes || nodes.length === 0) return '';
    return nodes.map((node, index) => {
        const isLast = index === nodes.length - 1;
        return renderFrontendTreeNode(node, guides, isLast, ancestorExcluded);
    }).join('');
}

function renderFrontendTreeNode(node, guides, isLastSibling, ancestorExcluded) {
    const isExcluded = state.excludedFrontend.has(node.path);
    const isInheritedExcluded = ancestorExcluded && !state.excludedFrontend.has(node.path);
    const effectiveExcluded = isExcluded || ancestorExcluded;

    const fileType = node.file_type || 'unknown';
    const icon = fileType === 'html' ? '📄' : fileType === 'js' || fileType === 'ts' ? '📜' : fileType === 'css' ? '🎨' : '📁';

    let guideHtml = '';
    for (let i = 0; i < guides.length; i++) {
        guideHtml += `<span class="tree-guide" style="left:${i * 20 + 12}px;${guides[i] ? '' : 'display:none;'}"></span>`;
    }

    const depth = guides.length;
    const connectorLeft = depth * 20;
    const connector = depth > 0 ? `<span class="tree-connector" style="left:${connectorLeft - 8}px;width:12px;"></span>` : '';

    const hasChildren = node.children && node.children.length > 0;
    const toggleIcon = hasChildren ? '▼' : '';
    const toggleCls = hasChildren ? '' : 'hidden';

    const checkCls = isExcluded ? '' : (isInheritedExcluded ? 'inherited-unchecked' : 'checked');
    const rowCls = effectiveExcluded ? 'excluded' : '';
    const nameCls = isInheritedExcluded ? 'inherited-excluded' : (isExcluded ? 'excluded' : '');

    const typeBadge = `<span class="frontend-file-type ${fileType}">${fileType.toUpperCase()}</span>`;

    // Build connection dots HTML for frontend files
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
    const pctBarWidth = effectiveExcluded ? 0 : Math.min((lines / maxLines) * 100, 100);
    const barColor = getLineCountColor(lines);

    // Get parent folder path
    const pathParts = node.path.split('/');
    const folderPath = pathParts.length > 1 ? pathParts.slice(0, -1).join('/') : '';

    let html = `
        <div class="tree-node">
            <div class="tree-node-row ${rowCls}" style="padding-left:${depth * 20 + 8}px;" onclick="toggleFrontendCascade('${node.path}')">
                ${guideHtml}
                ${connector}
                <span class="tree-node-toggle ${toggleCls}" onclick="event.stopPropagation();toggleFrontendNodeCollapse(this)">${toggleIcon}</span>
                <span class="tree-node-checkbox ${checkCls}">✓</span>
                <span class="tree-node-icon">${icon}</span>
                <span class="tree-node-name ${nameCls}">${node.name}</span>
                <span class="tree-node-folder-path" title="${node.path}">${folderPath}</span>
                ${connectionDots}
                ${typeBadge}
                <span class="tree-node-metrics">${node.lines || 0} L</span>
                <span class="tree-node-pct-bar ${effectiveExcluded ? 'excluded' : ''}" title="${lines} lines">
                    <span class="pct-fill" style="width:${pctBarWidth}%;background:${barColor}"></span>
                </span>
            </div>`;

    if (hasChildren) {
        const newGuides = [...guides, !isLastSibling];
        html += `<div class="tree-node-children expanded">
            ${renderFrontendTreeNodes(node.children, newGuides, effectiveExcluded)}
        </div>`;
    }

    html += '</div>';
    return html;
}

export function toggleFrontendNodeCollapse(toggleEl) {
    const nodeEl = toggleEl.closest('.tree-node');
    const childrenEl = nodeEl.querySelector(':scope > .tree-node-children');
    if (childrenEl) {
        const isCollapsed = !childrenEl.classList.contains('expanded');
        childrenEl.classList.toggle('expanded', isCollapsed);
        toggleEl.style.transform = isCollapsed ? '' : 'rotate(-90deg)';
    }
}

export function toggleFrontendCascade(path) {
    const wasExcluded = state.excludedFrontend.has(path);

    function findNode(node, targetPath) {
        if (node.path === targetPath) return node;
        for (const child of (node.children || [])) {
            const found = findNode(child, targetPath);
            if (found) return found;
        }
        return null;
    }

    function getAllDescendantPaths(node) {
        const paths = [node.path];
        for (const child of (node.children || [])) {
            paths.push(...getAllDescendantPaths(child));
        }
        return paths;
    }

    const targetNode = findNode(state.frontendTreeData, path);
    if (!targetNode) return;

    const allPaths = getAllDescendantPaths(targetNode);

    if (wasExcluded) {
        // Re-include this and remove explicit exclusions from descendants
        allPaths.forEach(p => state.excludedFrontend.delete(p));
    } else {
        // Exclude this node
        state.excludedFrontend.add(path);
        // Remove explicit exclusions from descendants (they inherit)
        allPaths.slice(1).forEach(p => state.excludedFrontend.delete(p));
    }

    if (window.renderBothPreviews) window.renderBothPreviews();
}

export function selectAllFrontend() {
    state.excludedFrontend = new Set();
    if (window.renderBothPreviews) window.renderBothPreviews();
}

export function selectNoneFrontend() {
    function collectPaths(node) {
        const paths = [];
        if (!node.is_root) paths.push(node.path);
        for (const child of (node.children || [])) {
            paths.push(...collectPaths(child));
        }
        return paths;
    }
    state.excludedFrontend = new Set(collectPaths(state.frontendTreeData));
    if (window.renderBothPreviews) window.renderBothPreviews();
}

function calculateFrontendTotals(tree) {
    let total = 0, included = 0, lines = 0, tokens = 0;

    function traverse(node, ancestorExcluded) {
        if (node.is_root) {
            for (const child of (node.children || [])) {
                traverse(child, false);
            }
            return;
        }

        total++;
        const isExcluded = state.excludedFrontend.has(node.path) || ancestorExcluded;
        if (!isExcluded) {
            included++;
            lines += node.lines || 0;
            tokens += node.tokens || 0;
        }
        for (const child of (node.children || [])) {
            traverse(child, isExcluded);
        }
    }

    traverse(tree, false);
    return { total, included, lines, tokens };
}

export function getAllExcludedFrontendPaths() {
    const allExcluded = new Set();
    function collectExcluded(node, ancestorExcluded) {
        if (node.is_root) {
            for (const child of (node.children || [])) {
                collectExcluded(child, false);
            }
            return;
        }

        const isDirectlyExcluded = state.excludedFrontend.has(node.path);
        const isExcluded = isDirectlyExcluded || ancestorExcluded;

        if (isExcluded) {
            allExcluded.add(node.path);
        }

        for (const child of (node.children || [])) {
            collectExcluded(child, isExcluded);
        }
    }
    if (state.frontendTreeData) {
        collectExcluded(state.frontendTreeData, false);
    }
    return Array.from(allExcluded);
}

// Make functions available globally for onclick handlers and cross-module access
window.previewFrontend = previewFrontend;
window.selectAllFrontend = selectAllFrontend;
window.selectNoneFrontend = selectNoneFrontend;
window.toggleFrontendInclude = toggleFrontendInclude;
window.toggleFrontendNodeCollapse = toggleFrontendNodeCollapse;
window.toggleFrontendCascade = toggleFrontendCascade;
window.renderFrontendPreview = renderFrontendPreview;
window.findMaxTokensInFrontendTree = findMaxTokensInFrontendTree;
