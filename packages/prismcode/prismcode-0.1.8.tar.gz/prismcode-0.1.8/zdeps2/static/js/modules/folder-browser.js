// ============================================================================
// Folder Browser - Project folder navigation modal
// ============================================================================

import { state } from './state.js';

// Note: changeProjectRoot accessed via window.* to avoid circular deps

export function openFolderBrowser() {
    fetch('/api/config')
        .then(r => r.json())
        .then(config => {
            state.currentBrowsePath = config.project_root || '';
            document.getElementById('folder-path-input').value = state.currentBrowsePath;
            navigateToFolder(state.currentBrowsePath);
            loadRecentProjects();
            document.getElementById('folder-browser-modal').classList.add('visible');
        });
}

export function closeFolderBrowser() {
    document.getElementById('folder-browser-modal').classList.remove('visible');
    document.getElementById('autocomplete-dropdown').classList.remove('visible');
}

export function navigateToFolder(path) {
    state.currentBrowsePath = path;
    document.getElementById('folder-path-input').value = path;

    fetch('/api/browse-directory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path })
    })
    .then(r => r.json())
    .then(data => {
        state.currentBrowsePath = data.current;
        document.getElementById('folder-path-input').value = data.current;
        renderBreadcrumbs(data.current);
        renderFolderList(data);
    });
}

function renderBreadcrumbs(path) {
    const container = document.getElementById('breadcrumbs');
    const parts = path.split('/').filter(p => p);
    let html = '<span class="breadcrumb" onclick="navigateToFolder(\'/\')">🏠</span>';

    let currentPath = '';
    for (let i = 0; i < parts.length; i++) {
        currentPath += '/' + parts[i];
        const safePath = currentPath.replace(/'/g, "\\'");
        html += '<span class="breadcrumb-separator">/</span>';
        html += `<span class="breadcrumb" onclick="navigateToFolder('${safePath}')">${parts[i]}</span>`;
    }
    container.innerHTML = html;
}

function renderFolderList(data) {
    const container = document.getElementById('folder-list');
    let html = '';

    if (data.parent) {
        const safeParent = data.parent.replace(/'/g, "\\'");
        html += `<div class="folder-item parent-folder-item" onclick="navigateToFolder('${safeParent}')">
            <span class="folder-icon">📁</span>
            <span class="folder-name">..</span>
        </div>`;
    }

    for (const folder of data.folders) {
        const safePath = folder.path.replace(/'/g, "\\'");
        html += `<div class="folder-item" onclick="navigateToFolder('${safePath}')">
            <span class="folder-icon">📁</span>
            <span class="folder-name">${folder.name}</span>
        </div>`;
    }

    if (data.folders.length === 0 && !data.parent) {
        html += '<div style="padding: 20px; text-align: center; color: #6e7681;">No folders found</div>';
    }

    container.innerHTML = html;
}

function loadRecentProjects() {
    fetch('/api/recent-projects')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('recent-projects-list');
            if (!data.projects || data.projects.length === 0) {
                container.innerHTML = '<div style="padding: 12px; color: #6e7681; font-size: 11px;">No recent projects</div>';
                return;
            }

            let html = '';
            for (const project of data.projects) {
                const safePath = project.path.replace(/'/g, "\\'");
                const validClass = project.exists ? '' : ' invalid';
                html += `<div class="recent-project-item${validClass}" onclick="selectRecentProject('${safePath}')">
                    <div class="project-name">${project.name}</div>
                    <div class="project-path" title="${project.path}">${project.path}</div>
                </div>`;
            }
            container.innerHTML = html;
        });
}

export function selectRecentProject(path) {
    closeFolderBrowser();
    window.changeProjectRoot(path);
}

export function selectCurrentFolder() {
    if (!state.currentBrowsePath) return;
    closeFolderBrowser();
    window.changeProjectRoot(state.currentBrowsePath);
}

export function handlePathInput() {
    clearTimeout(state.autocompleteTimeout);
    state.autocompleteTimeout = setTimeout(() => {
        const input = document.getElementById('folder-path-input');
        const value = input.value.trim();

        if (!value) {
            document.getElementById('autocomplete-dropdown').classList.remove('visible');
            return;
        }

        fetch('/api/autocomplete-path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: value })
        })
        .then(r => r.json())
        .then(data => {
            const dropdown = document.getElementById('autocomplete-dropdown');
            if (!data.suggestions || data.suggestions.length === 0) {
                dropdown.classList.remove('visible');
                return;
            }

            let html = '';
            for (const s of data.suggestions) {
                const safePath = s.path.replace(/'/g, "\\'");
                html += `<div class="autocomplete-item" onclick="selectAutocompletePath('${safePath}')">
                    <span class="folder-icon">📁</span>
                    <span>${s.name}</span>
                </div>`;
            }
            dropdown.innerHTML = html;
            dropdown.classList.add('visible');
        });
    }, 150);
}

export function handlePathKeydown(e) {
    if (e.key === 'Enter') {
        document.getElementById('autocomplete-dropdown').classList.remove('visible');
        navigateToFolder(document.getElementById('folder-path-input').value);
    }
}

export function selectAutocompletePath(path) {
    document.getElementById('autocomplete-dropdown').classList.remove('visible');
    navigateToFolder(path);
}

// Make functions available globally for onclick handlers
window.openFolderBrowser = openFolderBrowser;
window.closeFolderBrowser = closeFolderBrowser;
window.navigateToFolder = navigateToFolder;
window.selectRecentProject = selectRecentProject;
window.selectCurrentFolder = selectCurrentFolder;
window.handlePathInput = handlePathInput;
window.handlePathKeydown = handlePathKeydown;
window.selectAutocompletePath = selectAutocompletePath;
