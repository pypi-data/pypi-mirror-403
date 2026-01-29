// ============================================================================
// Settings - Entry points, submodules, and project configuration
// ============================================================================

import { state } from './state.js';

// Note: loadData and refresh are accessed via window.loadData/window.refresh
// to avoid circular dependencies

export function promptAddEntryPoint(path) {
    document.getElementById('entry-path').value = path;
    document.getElementById('entry-label').value = path.split('/').pop().replace('.py', '').toUpperCase();

    const picker = document.getElementById('color-picker');
    picker.innerHTML = '';
    state.selectedColor = state.availableColors[0];

    for (const color of state.availableColors) {
        const opt = document.createElement('div');
        opt.className = 'color-option' + (color === state.selectedColor ? ' selected' : '');
        opt.style.background = color.hex;
        opt.textContent = color.emoji;
        opt.onclick = () => {
            picker.querySelectorAll('.color-option').forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            state.selectedColor = color;
        };
        picker.appendChild(opt);
    }

    document.getElementById('add-entry-modal').classList.add('visible');
}

export function closeAddEntry() {
    document.getElementById('add-entry-modal').classList.remove('visible');
}

export function saveEntryPoint() {
    const path = document.getElementById('entry-path').value;
    const label = document.getElementById('entry-label').value.trim().toUpperCase();

    if (!label) {
        alert('Please enter a label');
        return;
    }

    fetch('/api/entry-points', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            path: path,
            label: label,
            color: state.selectedColor.hex,
            emoji: state.selectedColor.emoji
        })
    }).then(() => {
        closeAddEntry();
        window.refresh();
    });
}

export function openSettings() {
    fetch('/api/config')
        .then(r => r.json())
        .then(config => {
            document.getElementById('current-root').textContent = 'Current: ' + (config.project_root || 'Not set');
        });

    const list = document.getElementById('entry-point-list');
    list.innerHTML = '';

    const eps = state.treeData.config.entry_points || [];
    if (eps.length === 0) {
        list.innerHTML = '<p style="color: #6e7681; font-size: 13px;">No entry points configured. Right-click a file to add one.</p>';
    } else {
        for (const ep of eps) {
            const isEnabled = ep.enabled !== false;
            const safePath = ep.path.replace(/'/g, "\\'");
            const item = document.createElement('div');
            item.className = 'entry-point-item' + (isEnabled ? '' : ' disabled');
            item.innerHTML = `
                <div class="toggle-container">
                    <div class="entry-point-toggle ${isEnabled ? 'enabled' : ''}" onclick="toggleEntryPoint('${safePath}')"></div>
                </div>
                <div class="emoji">${ep.emoji || '🔵'}</div>
                <div class="info">
                    <div class="name">${ep.label}</div>
                    <div class="path">${ep.path}</div>
                </div>
                <button class="remove-btn" onclick="removeEntryPoint('${safePath}')">✕</button>
            `;
            list.appendChild(item);
        }
    }

    document.getElementById('suggestion-list').innerHTML = '<p style="color: #6e7681; font-size: 12px;">Click "Scan Project" to find potential entry points.</p>';

    loadSubmodules();

    document.getElementById('settings-modal').classList.add('visible');
}

export function toggleEntryPoint(path) {
    fetch('/api/entry-points/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path })
    })
    .then(r => r.json())
    .then(() => {
        closeSettings();
        window.refresh();
    });
}

export function changeProjectRoot(newRoot) {
    if (!newRoot) return;

    fetch('/api/project-root', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: newRoot })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        document.getElementById('current-root').textContent = 'Current: ' + data.project_root;
        closeSettings();
        window.loadData();
    })
    .catch(err => alert('Error: ' + err));
}

export function loadSuggestions() {
    const list = document.getElementById('suggestion-list');
    const countEl = document.getElementById('suggestion-count');
    const includeTests = document.getElementById('include-tests').checked;

    list.innerHTML = '<div class="loading" style="padding: 20px;"><div class="spinner"></div> Scanning all files...</div>';
    countEl.textContent = '';

    fetch(`/api/suggest-entry-points?limit=500&include_tests=${includeTests}`)
        .then(r => r.json())
        .then(data => {
            if (!data.suggestions || data.suggestions.length === 0) {
                list.innerHTML = '<p style="color: #6e7681; font-size: 12px;">No entry points found.</p>';
                countEl.textContent = '(0 found)';
                return;
            }

            countEl.textContent = `(${data.count} found)`;
            list.innerHTML = '';

            for (const s of data.suggestions) {
                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.innerHTML = `
                    <div class="info">
                        <div class="name">${s.name}</div>
                        <div class="path">${s.path}</div>
                    </div>
                    <div class="metrics">
                        <span class="metric children">${s.deps} deps</span>
                    </div>
                `;
                item.onclick = () => {
                    closeSettings();
                    promptAddEntryPoint(s.path);
                };
                list.appendChild(item);
            }
        })
        .catch(err => {
            list.innerHTML = '<p style="color: #f85149; font-size: 12px;">Error loading suggestions: ' + err + '</p>';
        });
}

export function closeSettings() {
    document.getElementById('settings-modal').classList.remove('visible');
}

export function loadSubmodules() {
    const list = document.getElementById('submodule-list');
    list.innerHTML = '<div class="no-submodules">Loading submodules...</div>';

    fetch('/api/submodules')
        .then(r => r.json())
        .then(data => {
            if (!data.submodules || data.submodules.length === 0) {
                list.innerHTML = '<div class="no-submodules">No git submodules found in this project.</div>';
                return;
            }

            list.innerHTML = '';
            for (const sub of data.submodules) {
                const safePath = sub.path.replace(/'/g, "\\'");
                const item = document.createElement('div');
                item.className = 'submodule-item' + (sub.included ? '' : ' excluded');
                item.innerHTML = `
                    <div class="submodule-icon">📦</div>
                    <div class="submodule-info">
                        <div class="submodule-path">${sub.path}</div>
                    </div>
                    <div class="submodule-toggle ${sub.included ? 'included' : ''}" onclick="toggleSubmodule('${safePath}')"></div>
                `;
                list.appendChild(item);
            }
        })
        .catch(() => {
            list.innerHTML = '<div class="no-submodules">Error loading submodules.</div>';
        });
}

export function toggleSubmodule(path) {
    fetch('/api/submodules/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path })
    })
    .then(r => r.json())
    .then(() => {
        loadSubmodules();
        window.refresh();
    });
}

export function removeEntryPoint(path) {
    if (confirm('Remove this entry point?')) {
        fetch('/api/entry-points', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        }).then(() => {
            closeSettings();
            window.refresh();
        });
    }
}

// Make functions available globally for onclick handlers
window.promptAddEntryPoint = promptAddEntryPoint;
window.closeAddEntry = closeAddEntry;
window.saveEntryPoint = saveEntryPoint;
window.openSettings = openSettings;
window.toggleEntryPoint = toggleEntryPoint;
window.changeProjectRoot = changeProjectRoot;
window.loadSuggestions = loadSuggestions;
window.closeSettings = closeSettings;
window.toggleSubmodule = toggleSubmodule;
window.removeEntryPoint = removeEntryPoint;
