// ============================================================================
// File Details - File selection and detail panel rendering
// ============================================================================

import { state, resetFileSelection } from './state.js';
import { previewChildren } from './children-preview.js';
import { formatPath } from './snapshot.js';

// Note: previewFrontend accessed via window.* to ensure it's available after module initialization

export function selectFile(data, row) {
    document.querySelectorAll('.tree-row.selected').forEach(r => r.classList.remove('selected'));
    row.classList.add('selected');
    state.selectedFile = data;

    // Reset selection state
    state.excludedChildren = new Set();
    state.childrenData = null;
    state.frontendTreeData = null;
    state.excludedFrontend = new Set();
    state.includeFrontend = false;

    const header = document.getElementById('detail-header');
    const content = document.getElementById('detail-content');

    header.style.display = 'block';
    document.getElementById('detail-title').textContent = data._path.split('/').pop();
    document.getElementById('detail-path').textContent = data._path;

    const copyControlsHtml = `
        <div class="copy-controls">
            <h3>Copy Snapshot</h3>
            <div class="copy-toggles">
                <div class="toggle-item">
                    <span class="toggle-label">Parent Depth:</span>
                    <input type="number" id="input-parent-depth" value="${state.parentDepth}" min="0" max="10"
                           style="width:50px;padding:4px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#c9d1d9;"
                           onchange="window.state.parentDepth=parseInt(this.value)||0">
                </div>
                <div class="toggle-item">
                    <div class="toggle-switch ${state.includeChain ? 'active' : ''}" id="toggle-chain" onclick="toggleChain()"></div>
                    <span class="toggle-label">Chain</span>
                    <input type="number" id="input-chain-length" value="${state.chainLength}" min="0" max="20"
                           style="width:40px;padding:4px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#c9d1d9;margin-left:4px;"
                           onchange="window.state.chainLength=parseInt(this.value)||0" title="0 = full chain">
                </div>
            </div>
            <div class="copy-toggles" style="margin-top:8px;">
                <div class="toggle-item">
                    <span class="toggle-label">Child Depth:</span>
                    <input type="number" id="input-child-depth" value="${state.childDepth}" min="0" max="20"
                           style="width:50px;padding:4px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#c9d1d9;"
                           onchange="window.state.childDepth=parseInt(this.value)||0" title="0 = all children">
                </div>
                <div class="toggle-item">
                    <span class="toggle-label">Max Tokens:</span>
                    <input type="number" id="input-child-tokens" value="${state.childMaxTokens}" min="0" step="1000"
                           style="width:70px;padding:4px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#c9d1d9;"
                           onchange="window.state.childMaxTokens=parseInt(this.value)||0" title="0 = no limit">
                </div>
            </div>
            <div id="children-preview"></div>
            <div id="frontend-section" class="frontend-toggle-section" style="display:none;">
                <div class="frontend-toggle-header">
                    <span class="frontend-toggle-label">Front-End Dependencies</span>
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
                        <input type="checkbox" id="include-frontend-check" onchange="toggleFrontendInclude()">
                        <span style="font-size:11px;color:#8b949e;">Include in snapshot</span>
                    </label>
                </div>
                <div id="frontend-preview"></div>
            </div>
            <div class="copy-btn-row" style="margin-top:8px;">
                <button class="btn primary" onclick="copySnapshot()">📋 Copy</button>
                <button class="btn" onclick="openFullscreenViewer()">⛶ Full View</button>
                <button class="btn chat-btn" onclick="openChatModal()">💬 Chat</button>
                <span class="copy-metrics" id="copy-metrics"></span>
            </div>
            <div class="copy-status" id="copy-status"></div>
        </div>
    `;

    // Add Entry Point button (always shown)
    const addEntryBtnHtml = `
        <div style="margin-bottom: 16px;">
            <button class="btn primary" onclick="promptAddEntryPoint('${data._path}')" style="width: 100%;">
                ➕ Add as Entry Point
            </button>
        </div>
    `;

    if (data._orphan) {
        content.innerHTML = addEntryBtnHtml + copyControlsHtml + `
            <div class="detail-section">
                <h3>Status</h3>
                <div class="connection-card">
                    <div class="label">
                        <div class="label-dot" style="background: #f85149;"></div>
                        <div class="label-text" style="color: #f85149;">ORPHAN</div>
                    </div>
                    <p style="color: #8b949e; font-size: 13px;">
                        This file is not reachable from any entry point.
                    </p>
                </div>
            </div>
        `;
    } else {
        let html = addEntryBtnHtml + copyControlsHtml + '<div class="detail-section"><h3>Connected To</h3>';
        for (const [label, pathInfo] of Object.entries(data._connection_paths)) {
            const ep = state.treeData.entry_points[label];
            const color = ep ? ep.color : '#8b949e';
            const typeBadge = pathInfo.type !== 'static' && pathInfo.type !== 'entry'
                ? `<span class="type-badge ${pathInfo.type}">${pathInfo.type}</span>` : '';

            html += `
                <div class="connection-card">
                    <div class="label">
                        <div class="label-dot" style="background: ${color};"></div>
                        <div class="label-text">${label}</div>
                        ${typeBadge}
                    </div>
                    <div class="connection-path">${formatPath(pathInfo.path)}</div>
                </div>
            `;
        }
        html += '</div>';
        content.innerHTML = html;
    }

    // Auto-load dependency tree
    previewChildren();
    if (window.previewFrontend) window.previewFrontend();
}
