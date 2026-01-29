// ============================================================================
// UI - Search and resizer functionality
// ============================================================================

import { state } from './state.js';
import { renderTree } from './tree.js';

export function initSearch() {
    document.getElementById('search').addEventListener('input', (e) => {
        state.searchQuery = e.target.value;
        renderTree(state.treeData.tree);
    });

    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            document.getElementById('search').focus();
        }
    });
}

export function initResizer() {
    const resizer = document.getElementById('resizer');
    const sidebar = document.querySelector('.sidebar');
    let isResizing = false;

    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        resizer.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const newWidth = e.clientX;
        const minWidth = 300;
        const maxWidth = window.innerWidth * 0.8;
        if (newWidth >= minWidth && newWidth <= maxWidth) {
            sidebar.style.width = newWidth + 'px';
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            resizer.classList.remove('dragging');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}
