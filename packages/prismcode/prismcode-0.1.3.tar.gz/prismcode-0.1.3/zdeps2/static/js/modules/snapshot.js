// ============================================================================
// Snapshot - Copy code snapshot functionality
// ============================================================================

import { state } from './state.js';
import { getAllExcludedPaths } from './children-preview.js';
import { getAllExcludedFrontendPaths } from './frontend-preview.js';

export function copySnapshot() {
    if (!state.selectedFile) return;

    const statusEl = document.getElementById('copy-status');
    const metricsEl = document.getElementById('copy-metrics');
    statusEl.textContent = 'Generating...';
    statusEl.classList.remove('error');
    statusEl.classList.add('visible');

    // Get all excluded paths including inherited ones
    const allExcluded = getAllExcludedPaths();
    const allExcludedFrontend = getAllExcludedFrontendPaths();

    fetch('/api/copy-snapshot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            path: state.selectedFile._path,
            parent_depth: state.parentDepth,
            include_chain: state.includeChain,
            chain_length: state.chainLength > 0 ? state.chainLength : null,
            child_depth: state.childDepth,
            child_max_tokens: state.childMaxTokens,
            excluded_children: allExcluded,
            include_frontend: state.includeFrontend,
            excluded_frontend: allExcludedFrontend,
            extra_files: Array.from(state.extraFiles)
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            statusEl.textContent = data.error;
            statusEl.classList.add('error');
            return;
        }

        navigator.clipboard.writeText(data.content).then(() => {
            const m = data.metrics;
            metricsEl.textContent = `${m.total_files} files | ${m.total_lines} lines | ~${m.token_estimate.toLocaleString()} tokens`;
            statusEl.textContent = 'Copied!';
            setTimeout(() => statusEl.classList.remove('visible'), 2000);
        }).catch(err => {
            statusEl.textContent = 'Failed: ' + err;
            statusEl.classList.add('error');
        });
    })
    .catch(err => {
        statusEl.textContent = 'Error: ' + err;
        statusEl.classList.add('error');
    });
}

export function formatPath(pathArray) {
    return pathArray.map((p, i) => {
        const isLast = i === pathArray.length - 1;
        const cls = isLast ? 'current' : 'file';
        const arrow = i < pathArray.length - 1 ? '<span class="arrow">→</span>' : '';
        return `<span class="${cls}">${p.split('/').pop()}</span>${arrow}`;
    }).join('');
}

export function toggleChain() {
    state.includeChain = !state.includeChain;
    document.getElementById('toggle-chain').classList.toggle('active', state.includeChain);
}

export async function generateSnapshotForChat() {
    if (!state.selectedFile) return null;

    const allExcluded = getAllExcludedPaths();
    const allExcludedFrontend = getAllExcludedFrontendPaths();

    try {
        const response = await fetch('/api/copy-snapshot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: state.selectedFile._path,
                parent_depth: state.parentDepth,
                include_chain: state.includeChain,
                chain_length: state.chainLength > 0 ? state.chainLength : null,
                child_depth: state.childDepth,
                child_max_tokens: state.childMaxTokens,
                excluded_children: allExcluded,
                include_frontend: state.includeFrontend,
                excluded_frontend: allExcludedFrontend,
                extra_files: Array.from(state.extraFiles)
            })
        });
        const data = await response.json();
        return data.content || null;
    } catch (e) {
        console.error('Failed to generate snapshot:', e);
        return null;
    }
}

// Make functions available globally for onclick handlers
window.copySnapshot = copySnapshot;
window.toggleChain = toggleChain;
