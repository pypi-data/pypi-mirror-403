// ============================================================================
// Delete Orphans - Orphan file deletion modal
// ============================================================================

import { state } from './state.js';

// Note: closeSettings and refresh are accessed via window.* to avoid circular deps

export function openDeleteOrphansModal() {
    document.getElementById('delete-orphans-modal').classList.add('visible');
    document.getElementById('delete-orphans-footer').style.display = 'none';
    document.getElementById('delete-orphans-body').innerHTML = '<div class="loading"><div class="spinner"></div> Loading orphan files...</div>';

    fetch('/api/orphans/preview-delete', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            state.orphanDeleteData = data;
            renderDeleteOrphansPreview(data);
        })
        .catch(err => {
            document.getElementById('delete-orphans-body').innerHTML = `<div style="color: #f85149; padding: 20px;">Error: ${err}</div>`;
        });
}

export function closeDeleteOrphansModal() {
    document.getElementById('delete-orphans-modal').classList.remove('visible');
    state.orphanDeleteData = null;
}

function renderDeleteOrphansPreview(data) {
    const body = document.getElementById('delete-orphans-body');

    if (!data.files || data.files.length === 0) {
        body.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #3fb950;">
                <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
                <p style="font-size: 14px;">No orphan files found!</p>
                <p style="font-size: 12px; color: #6e7681; margin-top: 8px;">All Python files are reachable from your entry points.</p>
            </div>
        `;
        return;
    }

    let filesHtml = '';
    for (const f of data.files.slice(0, 100)) {
        filesHtml += `<div class="orphan-preview-item">
            <span class="file-icon">📄</span>
            <span class="file-path" title="${f.path}">${f.path}</span>
        </div>`;
    }
    if (data.files.length > 100) {
        filesHtml += `<div class="orphan-preview-item" style="color: #6e7681; font-style: italic;">... and ${data.files.length - 100} more files</div>`;
    }

    let foldersHtml = '';
    if (data.folders && data.folders.length > 0) {
        for (const f of data.folders.slice(0, 20)) {
            foldersHtml += `<div class="orphan-preview-item folder">
                <span class="file-icon">📁</span>
                <span class="file-path" title="${f}">${f}</span>
            </div>`;
        }
        if (data.folders.length > 20) {
            foldersHtml += `<div class="orphan-preview-item folder" style="font-style: italic;">... and ${data.folders.length - 20} more folders</div>`;
        }
    }

    body.innerHTML = `
        <div class="delete-warning">
            <h4>⚠️ Warning: This action is IRREVERSIBLE</h4>
            <p>The following files will be <span class="warning-text">permanently deleted</span> from your filesystem.</p>
            <p class="warning-text">Make sure your project is backed up before proceeding!</p>
        </div>

        <div class="delete-stats">
            <div class="delete-stat">
                <span>Files to delete:</span>
                <span class="stat-value">${data.files.length}</span>
            </div>
            <div class="delete-stat folders">
                <span>Empty folders to remove:</span>
                <span class="stat-value">${data.folders ? data.folders.length : 0}</span>
            </div>
        </div>

        <div class="orphan-preview-list">
            ${filesHtml}
            ${foldersHtml}
        </div>

        <div class="delete-confirmation">
            <label>Type <strong>DELETE</strong> to confirm:</label>
            <input type="text" id="delete-confirm-input" oninput="validateDeleteConfirmation()" placeholder="Type DELETE here" autocomplete="off">
        </div>
    `;

    document.getElementById('delete-orphans-footer').style.display = 'flex';
    document.getElementById('confirm-delete-btn').disabled = true;
}

export function validateDeleteConfirmation() {
    const input = document.getElementById('delete-confirm-input');
    const btn = document.getElementById('confirm-delete-btn');
    const isValid = input.value === 'DELETE';

    btn.disabled = !isValid;
    input.classList.toggle('valid', isValid);
}

export function executeOrphanDeletion() {
    const input = document.getElementById('delete-confirm-input');
    if (input.value !== 'DELETE') return;

    document.getElementById('delete-orphans-body').innerHTML = '<div class="delete-progress"><div class="spinner"></div> Deleting files...</div>';
    document.getElementById('delete-orphans-footer').style.display = 'none';

    fetch('/api/orphans/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmation: 'DELETE' })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            document.getElementById('delete-orphans-body').innerHTML = `
                <div class="delete-results error">
                    <h4>❌ Error</h4>
                    <p>${data.error}</p>
                </div>
            `;
        } else {
            document.getElementById('delete-orphans-body').innerHTML = `
                <div class="delete-results success">
                    <h4>✅ Deletion Complete</h4>
                    <p>Deleted ${data.deleted_files} files and removed ${data.deleted_folders} empty folders.</p>
                </div>
            `;
            setTimeout(() => {
                closeDeleteOrphansModal();
                window.closeSettings();
                window.refresh();
            }, 2000);
        }
    })
    .catch(err => {
        document.getElementById('delete-orphans-body').innerHTML = `
            <div class="delete-results error">
                <h4>❌ Error</h4>
                <p>${err}</p>
            </div>
        `;
    });
}

// Make functions available globally for onclick handlers
window.openDeleteOrphansModal = openDeleteOrphansModal;
window.closeDeleteOrphansModal = closeDeleteOrphansModal;
window.validateDeleteConfirmation = validateDeleteConfirmation;
window.executeOrphanDeletion = executeOrphanDeletion;
