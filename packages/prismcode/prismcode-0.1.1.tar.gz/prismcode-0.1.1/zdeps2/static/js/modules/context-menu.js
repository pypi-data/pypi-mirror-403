// ============================================================================
// Context Menu - Right-click context menu
// ============================================================================

import { state } from './state.js';
import { promptAddEntryPoint } from './settings.js';

export function showContextMenu(e, data) {
    e.preventDefault();
    state.contextMenuFile = data;
    const menu = document.getElementById('context-menu');
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
    menu.classList.add('visible');
}

export function initContextMenuListener() {
    document.addEventListener('click', () => {
        document.getElementById('context-menu').classList.remove('visible');
    });
}

export function addAsEntryPoint() {
    if (state.contextMenuFile) {
        promptAddEntryPoint(state.contextMenuFile._path);
    }
}

export function copyPath() {
    if (state.contextMenuFile) {
        navigator.clipboard.writeText(state.contextMenuFile._path);
    }
}

// Make functions available globally for onclick handlers
window.addAsEntryPoint = addAsEntryPoint;
window.copyPath = copyPath;
