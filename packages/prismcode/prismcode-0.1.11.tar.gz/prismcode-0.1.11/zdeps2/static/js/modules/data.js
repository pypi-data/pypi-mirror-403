// ============================================================================
// Data - Data loading and UI updates
// ============================================================================

import { state } from './state.js';
import { renderTree } from './tree.js';

export function loadData() {
    document.getElementById('tree').innerHTML = '<div class="loading"><div class="spinner"></div> Loading...</div>';
    fetch('/api/data')
        .then(r => r.json())
        .then(data => {
            state.treeData = data;
            state.availableColors = data.config.available_colors || [];
            updateStats(data.stats);
            updateFilters(data.entry_points);
            updateLegend(data.entry_points);
            renderTree(data.tree);
        });
}

export function refresh() {
    fetch('/api/refresh')
        .then(() => loadData());
}

function updateStats(stats) {
    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-connected').textContent = stats.connected;
    document.getElementById('stat-orphans').textContent = stats.orphans;
}

function updateFilters(entryPoints) {
    const container = document.getElementById('filters');
    let html = `
        <button class="filter-btn active" data-filter="all">All</button>
        <button class="filter-btn" data-filter="connected">Connected</button>
        <button class="filter-btn orphan-filter" data-filter="orphan">Orphans</button>
    `;
    for (const [label, info] of Object.entries(entryPoints)) {
        html += `<button class="filter-btn" data-filter="${label}">${info.emoji} ${label}</button>`;
    }
    container.innerHTML = html;

    container.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentFilter = btn.dataset.filter;
            renderTree(state.treeData.tree);
        });
    });
}

function updateLegend(entryPoints) {
    const container = document.getElementById('legend');
    let html = '';
    for (const [label, info] of Object.entries(entryPoints)) {
        html += `<div class="legend-item">${info.emoji} ${label}</div>`;
    }
    html += '<div class="legend-item">🔴 ORPHAN</div>';
    container.innerHTML = html;
}

// Make functions available globally
window.loadData = loadData;
window.refresh = refresh;
