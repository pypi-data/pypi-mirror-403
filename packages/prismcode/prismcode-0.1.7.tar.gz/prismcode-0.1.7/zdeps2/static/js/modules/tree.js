// ============================================================================
// Tree Rendering - Sidebar file tree display
// ============================================================================

import { state } from './state.js';
import { selectFile } from './file-details.js';
import { showContextMenu } from './context-menu.js';

export function renderTree(tree, container = null, depth = 0) {
    if (!container) {
        container = document.getElementById('tree');
        container.innerHTML = '';
    }

    const entries = Object.entries(tree).sort((a, b) => {
        const aIsFolder = a[1]._type === 'folder';
        const bIsFolder = b[1]._type === 'folder';
        if (aIsFolder && !bIsFolder) return -1;
        if (!aIsFolder && bIsFolder) return 1;
        return a[0].localeCompare(b[0]);
    });

    for (const [name, data] of entries) {
        if (name.startsWith('_')) continue;

        const item = document.createElement('div');
        item.className = 'tree-item';

        if (data._type === 'folder') {
            const hasVisibleChildren = checkFolderVisibility(data._children);
            if (!hasVisibleChildren) continue;

            const contains = data._contains || [];
            const isOrphanOnly = contains.length === 1 && contains[0] === 'ORPHAN';
            const folderBadges = getFolderBadges(contains);
            const nameClass = isOrphanOnly ? 'tree-name orphan-folder' : 'tree-name';

            item.innerHTML = `
                <div class="tree-row folder-row">
                    ${getIndent(depth)}
                    <div class="tree-toggle">▶</div>
                    <div class="tree-icon">📁</div>
                    <div class="${nameClass}">${name}</div>
                    <div class="tree-badges">${folderBadges}</div>
                </div>
                <div class="tree-children"></div>
            `;

            const row = item.querySelector('.folder-row');
            const toggle = item.querySelector('.tree-toggle');
            const children = item.querySelector('.tree-children');

            row.addEventListener('click', () => {
                toggle.classList.toggle('expanded');
                children.classList.toggle('expanded');
            });

            if (depth === 0) {
                toggle.classList.add('expanded');
                children.classList.add('expanded');
            }

            container.appendChild(item);
            renderTree(data._children, children, depth + 1);
        } else {
            if (!shouldShowFile(data)) continue;

            const badges = getBadges(data);
            const nameClass = data._orphan ? 'tree-name orphan-text' : 'tree-name';
            const isExtraSelected = state.extraFiles.has(data._path);
            const safePath = data._path.replace(/'/g, "\\'");
            const lines = data._lines || 0;

            item.innerHTML = `
                <div class="tree-row file-row" data-path="${data._path}">
                    ${getIndent(depth)}
                    <input type="checkbox" class="extra-file-checkbox"
                           ${isExtraSelected ? 'checked' : ''}
                           onclick="event.stopPropagation(); toggleExtraFile('${safePath}')">
                    <div class="tree-toggle hidden">▶</div>
                    <div class="tree-icon">📄</div>
                    <div class="${nameClass}">${name}</div>
                    ${getCodeSizeBar(lines)}
                    <div class="tree-badges">${badges}</div>
                </div>
            `;

            const row = item.querySelector('.file-row');
            row.addEventListener('click', () => selectFile(data, row));
            row.addEventListener('contextmenu', (e) => showContextMenu(e, data));

            container.appendChild(item);
        }
    }
}

function checkFolderVisibility(children) {
    for (const [name, data] of Object.entries(children)) {
        if (name.startsWith('_')) continue;
        if (data._type === 'folder') {
            if (checkFolderVisibility(data._children)) return true;
        } else {
            if (shouldShowFile(data)) return true;
        }
    }
    return false;
}

function shouldShowFile(data) {
    if (state.searchQuery && !data._path.toLowerCase().includes(state.searchQuery.toLowerCase())) {
        return false;
    }

    if (state.currentFilter === 'orphan') return data._orphan;
    if (state.currentFilter === 'connected') return !data._orphan;
    if (state.currentFilter === 'all') return true;

    return data._connections.some(c => c.label === state.currentFilter);
}

function getIndent(depth) {
    return '<span class="tree-indent"></span>'.repeat(depth);
}

export function getBadges(data) {
    let badges = '';
    if (data._entry_point) badges += '<span class="badge" style="background:#f0f6fc22;color:#f0f6fc;border:1px solid #f0f6fc44;">ENTRY</span>';
    if (data._orphan) {
        badges += '<span class="badge orphan">ORPHAN</span>';
    } else {
        for (const conn of data._connections) {
            badges += `<span class="badge" style="background:${conn.color}22;color:${conn.color};border:1px solid ${conn.color}44;">${conn.label}</span>`;
        }
    }
    return badges;
}

function getFolderBadges(contains) {
    if (!contains || contains.length === 0) return '';
    let badges = '';
    for (const label of contains) {
        if (label === 'ORPHAN') {
            badges += '<span class="badge orphan">ORPHAN</span>';
        } else {
            const ep = state.treeData.entry_points[label];
            if (ep) {
                badges += `<span class="badge" style="background:${ep.color}22;color:${ep.color};border:1px solid ${ep.color}44;">${label}</span>`;
            }
        }
    }
    return badges;
}

// Code size bar helper - universal scale 0-2000 lines
export function getCodeSizeBar(lines) {
    const maxLines = 2000;
    const pct = Math.min((lines / maxLines) * 100, 100);
    const color = getLineCountColor(lines);
    return `<span class="code-size-bar" title="${lines} lines">
        <span class="code-size-fill" style="width:${pct}%;background:${color}"></span>
    </span>`;
}

// Color gradient: green (<1000) → orange (1000-1500) → red (>1500-2000)
export function getLineCountColor(lines) {
    if (lines < 1000) return '#3fb950';  // green
    if (lines >= 2000) return '#f85149'; // red
    // Gradient from green → orange → red
    const ratio = (lines - 1000) / 1000; // 0 to 1 as lines go 1000→2000
    if (ratio < 0.5) {
        // green to orange (ratio 0-0.5)
        const r = Math.round(63 + 192 * ratio * 2);  // 63 → 255
        const g = Math.round(185 - 50 * ratio * 2);  // 185 → 135
        return `rgb(${r}, ${g}, 80)`;
    } else {
        // orange to red (ratio 0.5-1)
        const g = Math.round(135 - 100 * (ratio - 0.5) * 2);  // 135 → 35
        const b = Math.round(80 - 31 * (ratio - 0.5) * 2);    // 80 → 49
        return `rgb(255, ${g}, ${b})`;
    }
}

// Toggle extra file selection
export function toggleExtraFile(path) {
    if (state.extraFiles.has(path)) {
        state.extraFiles.delete(path);
    } else {
        state.extraFiles.add(path);
    }
    // Re-render tree to update checkbox state
    if (state.treeData && state.treeData.tree) {
        renderTree(state.treeData.tree);
    }
}

// Make toggle function available globally for onclick handlers
window.toggleExtraFile = toggleExtraFile;
