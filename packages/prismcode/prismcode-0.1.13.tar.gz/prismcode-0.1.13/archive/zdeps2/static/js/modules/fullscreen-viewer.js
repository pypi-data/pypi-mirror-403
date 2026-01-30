// ============================================================================
// Fullscreen Viewer - Full dependency viewer modal
// ============================================================================

import { state } from './state.js';
import { renderTreeNode, findMaxTokensInTree, getMaxDepth, collectAllPaths, collectPathsBeyondDepth, getAllExcludedPaths } from './children-preview.js';

// Note: close*Modal functions accessed via window.* to avoid circular deps

export function openFullscreenViewer() {
    if (!state.selectedFile) return;

    // Reset exclusions
    state.excludedParents = new Set();
    state.excludedChain = new Set();
    state.excludedChildren = new Set();

    // Create fullscreen container
    const viewer = document.createElement('div');
    viewer.className = 'dep-viewer-fullscreen';
    viewer.id = 'fullscreen-viewer';
    viewer.innerHTML = `
        <div class="dep-viewer-header">
            <div style="display:flex;align-items:center;">
                <span class="dep-viewer-title">📊 Dependency Viewer</span>
                <span class="dep-viewer-subtitle" id="fs-file-path">${state.selectedFile._path}</span>
            </div>
            <div style="display:flex;gap:8px;align-items:center;">
                <span id="fs-totals" style="font-size:11px;color:#3fb950;"></span>
                <button class="btn primary" onclick="copyFromFullscreen()">📋 Copy Selected</button>
                <button class="btn" onclick="closeFullscreenViewer()">✕ Close</button>
            </div>
        </div>
        <div class="dep-viewer-body" id="fs-body">
            <div class="loading"><div class="spinner"></div> Loading dependencies...</div>
        </div>
    `;
    document.body.appendChild(viewer);

    // Fetch full dependency info
    fetch('/api/full-dependencies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: state.selectedFile._path })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            document.getElementById('fs-body').innerHTML = `<div style="color:#f85149;padding:20px;">${data.error}</div>`;
            return;
        }
        state.fullDepData = data;
        renderFullscreenViewer();
    });
}

export function closeFullscreenViewer() {
    const viewer = document.getElementById('fullscreen-viewer');
    if (viewer) viewer.remove();
    state.fullDepData = null;
}

function renderFullscreenViewer() {
    if (!state.fullDepData) return;
    const body = document.getElementById('fs-body');

    // Calculate totals
    const totals = calculateFullTotals();
    document.getElementById('fs-totals').textContent =
        `${totals.included}/${totals.total} files | ${totals.lines.toLocaleString()} lines | ${totals.tokens.toLocaleString()} tokens`;

    let html = '';

    // Target file
    const t = state.fullDepData.target;
    html += `
        <div class="dep-viewer-target">
            <div class="target-icon">🎯</div>
            <div class="target-info">
                <div class="target-name">${t.name}</div>
                <div class="target-path">${t.path}</div>
            </div>
            <div class="target-metrics">${t.lines} lines | ${t.tokens} tokens</div>
        </div>
    `;

    // Controls row
    html += `
        <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
            <button class="tree-control-btn" onclick="fsSelectAll()">✓ Select All</button>
            <button class="tree-control-btn" onclick="fsSelectNone()">✗ Select None</button>
            <button class="tree-control-btn" onclick="fsSelectParentsOnly()">Parents Only</button>
            <button class="tree-control-btn" onclick="fsSelectChildrenOnly()">Children Only</button>
        </div>
    `;

    // Chain section (if any)
    if (state.fullDepData.chains && state.fullDepData.chains.length > 0) {
        for (const chain of state.fullDepData.chains) {
            if (chain.files.length === 0) continue;
            html += `
                <div class="dep-viewer-section">
                    <div class="dep-viewer-section-header">
                        <h4>${chain.emoji} Chain to ${chain.label}</h4>
                        <span class="section-badge chain">${chain.files.length} files</span>
                        <button class="tree-control-btn" style="margin-left:auto;" onclick="fsToggleChain('${chain.label}')">Toggle</button>
                    </div>
                    <div class="dep-viewer-section-content">
                        ${renderChainList(chain)}
                    </div>
                </div>
            `;
        }
    }

    // Parents section
    if (state.fullDepData.parents && state.fullDepData.parents.length > 0) {
        html += `
            <div class="dep-viewer-section">
                <div class="dep-viewer-section-header">
                    <h4>⬆️ Parents (files that import this)</h4>
                    <span class="section-badge parent">${state.fullDepData.parents.length} files</span>
                    <button class="tree-control-btn" style="margin-left:auto;" onclick="fsToggleAllParents()">Toggle All</button>
                </div>
                <div class="dep-viewer-section-content">
                    ${renderParentsList(state.fullDepData.parents)}
                </div>
            </div>
        `;
    }

    // Children section
    if (state.fullDepData.children_tree && state.fullDepData.children_tree.children && state.fullDepData.children_tree.children.length > 0) {
        const childCount = countTreeNodes(state.fullDepData.children_tree);
        const maxDepth = getMaxDepth(state.fullDepData.children_tree);
        const fsMaxTokens = findMaxTokensInTree(state.fullDepData.children_tree, state.excludedChildren);

        // Build depth buttons
        let depthBtns = '';
        for (let d = 1; d <= Math.min(maxDepth, 6); d++) {
            depthBtns += `<button class="depth-btn" onclick="fsSelectChildrenToDepth(${d})" title="Select depth 1-${d}">${d}</button>`;
        }
        if (maxDepth > 6) {
            depthBtns += `<button class="depth-btn" onclick="fsSelectChildrenToDepth(${maxDepth})" title="All depths">∞</button>`;
        }

        html += `
            <div class="dep-viewer-section">
                <div class="dep-viewer-section-header">
                    <h4>⬇️ Children (dependencies)</h4>
                    <span class="section-badge child">${childCount} files</span>
                    <span class="depth-btns" style="margin-left:8px;">Depth: ${depthBtns}</span>
                    <button class="tree-control-btn" style="margin-left:auto;" onclick="fsToggleAllChildren()">Toggle All</button>
                </div>
                <div class="dep-viewer-section-content">
                    ${renderTreeNode(state.fullDepData.children_tree, [], true, false, false, fsMaxTokens)}
                </div>
            </div>
        `;
    }

    if (!html.includes('dep-viewer-section')) {
        html += '<div style="color:#6e7681;padding:40px;text-align:center;">No dependencies found</div>';
    }

    body.innerHTML = html;
}

function renderParentsList(parents) {
    let html = '';
    for (const p of parents) {
        const isExcluded = state.excludedParents.has(p.path);
        const safePath = p.path.replace(/'/g, "\\'");
        const checkClass = isExcluded ? 'tree-node-checkbox' : 'tree-node-checkbox checked';
        const rowClass = isExcluded ? 'tree-node-row excluded' : 'tree-node-row';
        html += `
            <div class="${rowClass}" onclick="fsToggleParent('${safePath}')" style="padding-left:12px;">
                <span class="${checkClass}">${isExcluded ? '' : '✓'}</span>
                <span class="tree-node-icon">📄</span>
                <span class="tree-node-name" title="${p.path}">${p.name}</span>
                <span class="tree-node-metrics">${p.lines} L</span>
            </div>
        `;
    }
    return html || '<div style="color:#6e7681;padding:12px;">No parents</div>';
}

function renderChainList(chain) {
    let html = '';
    for (const f of chain.files) {
        const chainKey = `${chain.label}:${f.path}`;
        const isExcluded = state.excludedChain.has(chainKey);
        const safePath = f.path.replace(/'/g, "\\'");
        const checkClass = isExcluded ? 'tree-node-checkbox' : 'tree-node-checkbox checked';
        const rowClass = isExcluded ? 'tree-node-row excluded' : 'tree-node-row';
        html += `
            <div class="${rowClass}" onclick="fsToggleChainFile('${chain.label}', '${safePath}')" style="padding-left:12px;">
                <span class="${checkClass}">${isExcluded ? '' : '✓'}</span>
                <span class="tree-node-icon" style="color:${chain.color};">●</span>
                <span class="tree-node-name" title="${f.path}">${f.name}</span>
                <span class="tree-node-metrics">${f.lines} L</span>
            </div>
        `;
    }
    return html || '<div style="color:#6e7681;padding:12px;">No chain files</div>';
}

function countTreeNodes(node) {
    let count = 0;
    if (!node.is_root) count = 1;
    for (const child of (node.children || [])) {
        count += countTreeNodes(child);
    }
    return count;
}

function calculateFullTotals() {
    const totals = { total: 0, included: 0, lines: 0, tokens: 0 };
    if (!state.fullDepData) return totals;

    // Target always included
    totals.total++;
    totals.included++;
    totals.lines += state.fullDepData.target.lines || 0;
    totals.tokens += state.fullDepData.target.tokens || 0;

    // Parents
    for (const p of (state.fullDepData.parents || [])) {
        totals.total++;
        if (!state.excludedParents.has(p.path)) {
            totals.included++;
            totals.lines += p.lines || 0;
            totals.tokens += p.tokens || 0;
        }
    }

    // Chain files
    for (const chain of (state.fullDepData.chains || [])) {
        for (const f of (chain.files || [])) {
            totals.total++;
            const chainKey = `${chain.label}:${f.path}`;
            if (!state.excludedChain.has(chainKey)) {
                totals.included++;
                totals.lines += f.lines || 0;
                totals.tokens += f.tokens || 0;
            }
        }
    }

    // Children (recursive with inheritance)
    if (state.fullDepData.children_tree) {
        addChildTotals(state.fullDepData.children_tree, totals, false);
    }

    return totals;
}

function addChildTotals(node, totals, ancestorExcluded) {
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
        addChildTotals(child, totals, isExcluded);
    }
}

// Fullscreen toggle functions
export function fsToggleParent(path) {
    if (state.excludedParents.has(path)) {
        state.excludedParents.delete(path);
    } else {
        state.excludedParents.add(path);
    }
    renderFullscreenViewer();
}

export function fsToggleChainFile(label, path) {
    const key = `${label}:${path}`;
    if (state.excludedChain.has(key)) {
        state.excludedChain.delete(key);
    } else {
        state.excludedChain.add(key);
    }
    renderFullscreenViewer();
}

export function fsToggleChain(label) {
    if (!state.fullDepData) return;
    const chain = state.fullDepData.chains.find(c => c.label === label);
    if (!chain) return;

    const allExcluded = chain.files.every(f => state.excludedChain.has(`${label}:${f.path}`));

    for (const f of chain.files) {
        const key = `${label}:${f.path}`;
        if (allExcluded) {
            state.excludedChain.delete(key);
        } else {
            state.excludedChain.add(key);
        }
    }
    renderFullscreenViewer();
}

export function fsToggleAllParents() {
    if (!state.fullDepData) return;
    const allExcluded = state.fullDepData.parents.every(p => state.excludedParents.has(p.path));

    for (const p of state.fullDepData.parents) {
        if (allExcluded) {
            state.excludedParents.delete(p.path);
        } else {
            state.excludedParents.add(p.path);
        }
    }
    renderFullscreenViewer();
}

export function fsToggleAllChildren() {
    if (!state.fullDepData || !state.fullDepData.children_tree) return;

    const allPaths = new Set();
    collectAllPaths(state.fullDepData.children_tree, allPaths);

    const pathsArray = Array.from(allPaths);
    const allExcluded = pathsArray.length > 0 && pathsArray.every(p => state.excludedChildren.has(p));

    if (allExcluded) {
        state.excludedChildren = new Set();
    } else {
        state.excludedChildren = new Set(pathsArray);
    }
    renderFullscreenViewer();
}

export function fsSelectChildrenToDepth(maxDepth) {
    if (!state.fullDepData || !state.fullDepData.children_tree) return;
    state.excludedChildren = new Set();
    collectPathsBeyondDepth(state.fullDepData.children_tree, maxDepth, state.excludedChildren);
    renderFullscreenViewer();
}

export function fsSelectAll() {
    state.excludedParents = new Set();
    state.excludedChain = new Set();
    state.excludedChildren = new Set();
    renderFullscreenViewer();
}

export function fsSelectNone() {
    if (!state.fullDepData) return;

    // Exclude all parents
    for (const p of (state.fullDepData.parents || [])) {
        state.excludedParents.add(p.path);
    }

    // Exclude all chain files
    for (const chain of (state.fullDepData.chains || [])) {
        for (const f of (chain.files || [])) {
            state.excludedChain.add(`${chain.label}:${f.path}`);
        }
    }

    // Exclude all children
    if (state.fullDepData.children_tree) {
        const allChildPaths = new Set();
        collectAllPaths(state.fullDepData.children_tree, allChildPaths);
        state.excludedChildren = allChildPaths;
    }

    renderFullscreenViewer();
}

export function fsSelectParentsOnly() {
    fsSelectNone();
    state.excludedParents = new Set();
    renderFullscreenViewer();
}

export function fsSelectChildrenOnly() {
    fsSelectNone();
    state.excludedChildren = new Set();
    renderFullscreenViewer();
}

export function copyFromFullscreen() {
    if (!state.selectedFile || !state.fullDepData) return;

    const allExcludedChildren = getAllExcludedPaths();

    const statusEl = document.createElement('div');
    statusEl.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#238636;color:#fff;padding:12px 20px;border-radius:8px;z-index:4000;';
    statusEl.textContent = 'Generating snapshot...';
    document.body.appendChild(statusEl);

    fetch('/api/copy-snapshot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            path: state.selectedFile._path,
            parent_depth: state.excludedParents.size === 0 ? 10 : 0,
            include_chain: state.excludedChain.size === 0,
            child_depth: 0,
            child_max_tokens: 0,
            excluded_children: allExcludedChildren
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            statusEl.textContent = 'Error: ' + data.error;
            statusEl.style.background = '#f85149';
            setTimeout(() => statusEl.remove(), 3000);
            return;
        }

        navigator.clipboard.writeText(data.content).then(() => {
            const m = data.metrics;
            statusEl.textContent = `Copied! ${m.total_files} files | ${m.total_lines} lines | ~${m.token_estimate.toLocaleString()} tokens`;
            setTimeout(() => statusEl.remove(), 3000);
        }).catch(err => {
            statusEl.textContent = 'Copy failed: ' + err;
            statusEl.style.background = '#f85149';
            setTimeout(() => statusEl.remove(), 3000);
        });
    });
}

export function initEscapeListener() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const viewer = document.getElementById('fullscreen-viewer');
            if (viewer) closeFullscreenViewer();
            const folderBrowser = document.getElementById('folder-browser-modal');
            if (folderBrowser && folderBrowser.classList.contains('visible')) window.closeFolderBrowser();
            const deleteModal = document.getElementById('delete-orphans-modal');
            if (deleteModal && deleteModal.classList.contains('visible')) window.closeDeleteOrphansModal();
            const chatModal = document.getElementById('chat-modal');
            if (chatModal && chatModal.classList.contains('visible')) window.closeChatModal();
        }
    });
}

// Make functions available globally for onclick handlers
window.openFullscreenViewer = openFullscreenViewer;
window.closeFullscreenViewer = closeFullscreenViewer;
window.copyFromFullscreen = copyFromFullscreen;
window.fsSelectAll = fsSelectAll;
window.fsSelectNone = fsSelectNone;
window.fsSelectParentsOnly = fsSelectParentsOnly;
window.fsSelectChildrenOnly = fsSelectChildrenOnly;
window.fsToggleParent = fsToggleParent;
window.fsToggleChainFile = fsToggleChainFile;
window.fsToggleChain = fsToggleChain;
window.fsToggleAllParents = fsToggleAllParents;
window.fsToggleAllChildren = fsToggleAllChildren;
window.fsSelectChildrenToDepth = fsSelectChildrenToDepth;
