        let treeData = null;
        let currentFilter = 'all';
        let searchQuery = '';
        let selectedFile = null;
        let contextMenuFile = null;
        let selectedColor = null;
        let availableColors = [];

        // Load data
        loadData();

        function loadData() {
            document.getElementById('tree').innerHTML = '<div class="loading"><div class="spinner"></div> Loading...</div>';
            fetch('/api/data')
                .then(r => r.json())
                .then(data => {
                    treeData = data;
                    availableColors = data.config.available_colors || [];
                    updateStats(data.stats);
                    updateFilters(data.entry_points);
                    updateLegend(data.entry_points);
                    renderTree(data.tree);
                });
        }

        function refresh() {
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
                    currentFilter = btn.dataset.filter;
                    renderTree(treeData.tree);
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

        function renderTree(tree, container = null, depth = 0) {
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

                    item.innerHTML = `
                        <div class="tree-row file-row" data-path="${data._path}">
                            ${getIndent(depth)}
                            <div class="tree-toggle hidden">▶</div>
                            <div class="tree-icon">📄</div>
                            <div class="${nameClass}">${name}</div>
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
            if (searchQuery && !data._path.toLowerCase().includes(searchQuery.toLowerCase())) {
                return false;
            }

            if (currentFilter === 'orphan') return data._orphan;
            if (currentFilter === 'connected') return !data._orphan;
            if (currentFilter === 'all') return true;

            return data._connections.some(c => c.label === currentFilter);
        }

        function getIndent(depth) {
            return '<span class="tree-indent"></span>'.repeat(depth);
        }

        function getBadges(data) {
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
                    const ep = treeData.entry_points[label];
                    if (ep) {
                        badges += `<span class="badge" style="background:${ep.color}22;color:${ep.color};border:1px solid ${ep.color}44;">${label}</span>`;
                    }
                }
            }
            return badges;
        }

        let parentDepth = 1;
        let includeChain = false;
        let chainLength = 0;
        let childDepth = 0;
        let childMaxTokens = 0;
        let excludedChildren = new Set();
        let excludedParents = new Set();
        let excludedChain = new Set();
        let childrenData = null;
        let childrenTreeData = null;
        let fullDepData = null;  // Full dependency info (parents, chains, children)
        // Frontend state
        let frontendTreeData = null;
        let excludedFrontend = new Set();
        let includeFrontend = false;

        function selectFile(data, row) {
            document.querySelectorAll('.tree-row.selected').forEach(r => r.classList.remove('selected'));
            row.classList.add('selected');
            selectedFile = data;
            excludedChildren = new Set();
            childrenData = null;
            // Reset frontend state
            frontendTreeData = null;
            excludedFrontend = new Set();
            includeFrontend = false;

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
                            <input type="number" id="input-parent-depth" value="${parentDepth}" min="0" max="10" 
                                   style="width:50px;padding:4px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#c9d1d9;"
                                   onchange="parentDepth=parseInt(this.value)||0">
                        </div>
                        <div class="toggle-item">
                            <div class="toggle-switch ${includeChain ? 'active' : ''}" id="toggle-chain" onclick="toggleChain()"></div>
                            <span class="toggle-label">Chain</span>
                            <input type="number" id="input-chain-length" value="${chainLength}" min="0" max="20" 
                                   style="width:40px;padding:4px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#c9d1d9;margin-left:4px;"
                                   onchange="chainLength=parseInt(this.value)||0" title="0 = full chain">
                        </div>
                    </div>
                    <div class="copy-toggles" style="margin-top:8px;">
                        <div class="toggle-item">
                            <span class="toggle-label">Child Depth:</span>
                            <input type="number" id="input-child-depth" value="${childDepth}" min="0" max="20"
                                   style="width:50px;padding:4px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#c9d1d9;"
                                   onchange="childDepth=parseInt(this.value)||0" title="0 = all children">
                        </div>
                        <div class="toggle-item">
                            <span class="toggle-label">Max Tokens:</span>
                            <input type="number" id="input-child-tokens" value="${childMaxTokens}" min="0" step="1000"
                                   style="width:70px;padding:4px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#c9d1d9;"
                                   onchange="childMaxTokens=parseInt(this.value)||0" title="0 = no limit">
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
                    const ep = treeData.entry_points[label];
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
            previewFrontend();
        }

        function toggleChain() {
            includeChain = !includeChain;
            document.getElementById('toggle-chain').classList.toggle('active', includeChain);
        }

        function previewChildren() {
            if (!selectedFile) return;
            const previewEl = document.getElementById('children-preview');
            previewEl.innerHTML = '<div class="children-tree-loading">Loading...</div>';
            
            fetch('/api/preview-children', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: selectedFile._path })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    previewEl.innerHTML = `<div class="children-tree-empty" style="color:#f85149;">${data.error}</div>`;
                    return;
                }
                childrenData = data.children;
                childrenTreeData = data.tree;
                renderChildrenPreview();
            });
        }

        function renderChildrenPreview() {
            const previewEl = document.getElementById('children-preview');
            if (!childrenTreeData || !childrenTreeData.children || childrenTreeData.children.length === 0) {
                previewEl.innerHTML = '<div class="children-tree-empty">No children found</div>';
                return;
            }

            const totals = calculateTreeTotals(childrenTreeData);
            const maxDepth = getMaxDepth(childrenTreeData);

            // Calculate unified max tokens across both trees (for relative scaling)
            const backendMaxTokens = findMaxTokensInTree(childrenTreeData, excludedChildren);
            const frontendMaxTokens = (frontendTreeData && includeFrontend)
                ? findMaxTokensInFrontendTree(frontendTreeData, excludedFrontend)
                : 0;
            const unifiedMaxTokens = Math.max(backendMaxTokens, frontendMaxTokens);

            // Build depth buttons
            let depthBtns = '<span class="depth-btns"><span style="font-size:10px;color:#6e7681;margin-right:4px;">Depth:</span>';
            for (let d = 1; d <= Math.min(maxDepth, 6); d++) {
                depthBtns += `<button class="depth-btn" onclick="selectToDepth(${d})" title="Select only depth 1-${d}">${d}</button>`;
            }
            if (maxDepth > 6) {
                depthBtns += `<button class="depth-btn" onclick="selectToDepth(${maxDepth})" title="Select all depths">∞</button>`;
            }
            depthBtns += '</span>';

            let html = `<div class="children-tree-box">
                <div class="children-tree-header">
                    <div class="children-tree-header-row">
                        <h4>Dependencies Tree</h4>
                        <span class="children-tree-totals">${totals.included}/${totals.total} files | ${totals.lines.toLocaleString()} lines | ${totals.tokens.toLocaleString()} tokens</span>
                        <span class="code-size-label">Code Size</span>
                    </div>
                    <div class="children-tree-header-row">
                        <div class="children-tree-controls">
                            <button class="tree-control-btn" onclick="selectAllChildren()">✓ All</button>
                            <button class="tree-control-btn" onclick="selectNoneChildren()">✗ None</button>
                            ${depthBtns}
                        </div>
                    </div>
                </div>
                <div class="children-tree-content">
                    ${renderTreeNode(childrenTreeData, [], true, false, false, unifiedMaxTokens)}
                </div>
            </div>`;

            previewEl.innerHTML = html;
        }

        function calculateAllTreeTokens(node, excludedPaths = new Set(), ancestorExcluded = false) {
            let total = 0;
            const isExcluded = excludedPaths.has(node.path) || ancestorExcluded;
            if (!node.is_root && !isExcluded) {
                total += node.tokens || 0;
            }
            for (const child of (node.children || [])) {
                total += calculateAllTreeTokens(child, excludedPaths, isExcluded);
            }
            return total;
        }

        function findMaxTokensInTree(node, excludedPaths = new Set(), ancestorExcluded = false) {
            let maxTokens = 0;
            const isExcluded = excludedPaths.has(node.path) || ancestorExcluded;
            if (!node.is_root && !isExcluded) {
                maxTokens = node.tokens || 0;
            }
            for (const child of (node.children || [])) {
                const childMax = findMaxTokensInTree(child, excludedPaths, isExcluded);
                if (childMax > maxTokens) maxTokens = childMax;
            }
            return maxTokens;
        }

        function getMaxDepth(node, currentMax = 0) {
            if (!node.is_root && node.depth > currentMax) {
                currentMax = node.depth;
            }
            for (const child of (node.children || [])) {
                currentMax = getMaxDepth(child, currentMax);
            }
            return currentMax;
        }

        function selectAllChildren() {
            excludedChildren = new Set();
            renderBothPreviews();
        }

        function selectNoneChildren() {
            if (!childrenTreeData) return;
            excludedChildren = new Set();
            collectAllPaths(childrenTreeData, excludedChildren);
            renderBothPreviews();
        }

        function selectToDepth(maxDepth) {
            if (!childrenTreeData) return;
            excludedChildren = new Set();
            collectPathsBeyondDepth(childrenTreeData, maxDepth, excludedChildren);
            renderBothPreviews();
        }

        function collectAllPaths(node, paths) {
            if (!node.is_root && node.path) {
                paths.add(node.path);
            }
            for (const child of (node.children || [])) {
                collectAllPaths(child, paths);
            }
        }

        function collectPathsBeyondDepth(node, maxDepth, paths) {
            if (!node.is_root && node.depth > maxDepth) {
                paths.add(node.path);
            }
            for (const child of (node.children || [])) {
                collectPathsBeyondDepth(child, maxDepth, paths);
            }
        }

        function getDescendantPaths(node) {
            const paths = [];
            for (const child of (node.children || [])) {
                if (child.path) paths.push(child.path);
                paths.push(...getDescendantPaths(child));
            }
            return paths;
        }

        function findNodeByPath(node, targetPath) {
            if (node.path === targetPath) return node;
            for (const child of (node.children || [])) {
                const found = findNodeByPath(child, targetPath);
                if (found) return found;
            }
            return null;
        }

        function calculateTreeTotals(node, totals = null, ancestorExcluded = false) {
            if (!totals) totals = { total: 0, included: 0, lines: 0, tokens: 0 };

            const isDirectlyExcluded = excludedChildren.has(node.path);
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
                calculateTreeTotals(child, totals, isExcluded);
            }

            return totals;
        }

        function renderTreeNode(node, guides = [], isRoot = false, isLastSibling = false, ancestorExcluded = false, totalTokens = 0) {
            if (isRoot) {
                let html = '';
                const children = node.children || [];
                children.forEach((child, idx) => {
                    const isLast = idx === children.length - 1;
                    html += renderTreeNode(child, [], false, isLast, false, totalTokens);
                });
                return html;
            }

            const isDirectlyExcluded = excludedChildren.has(node.path);
            const isInheritedExcluded = ancestorExcluded && !isDirectlyExcluded;
            const isExcluded = isDirectlyExcluded || ancestorExcluded;
            const hasChildren = node.children && node.children.length > 0;
            const nodeId = 'node-' + node.path.replace(/[^a-zA-Z0-9]/g, '-');

            let rowClass = 'tree-node-row';
            if (isDirectlyExcluded) {
                rowClass += ' excluded';
            } else if (isInheritedExcluded) {
                rowClass += ' inherited-excluded';
            }

            // Checkbox state
            let checkboxClass = 'tree-node-checkbox';
            let checkboxContent = '';
            if (isDirectlyExcluded) {
                checkboxContent = '';  // unchecked
            } else if (isInheritedExcluded) {
                checkboxClass += ' inherited-unchecked';
                checkboxContent = '';
            } else {
                checkboxClass += ' checked';
                checkboxContent = '✓';
            }

            let guidesHtml = '';
            for (const g of guides) {
                guidesHtml += `<span class="tree-node-guide ${g}"></span>`;
            }

            // Safe path for onclick (escape quotes)
            const safePath = node.path.replace(/'/g, "\\'");

            // Build connection dots HTML
            let connectionDots = '';
            if (node.connections && node.connections.length > 0) {
                connectionDots = '<span class="tree-node-connections">';
                for (const conn of node.connections) {
                    connectionDots += `<span class="connection-dot" style="background:${conn.color};" title="${conn.label}"></span>`;
                }
                connectionDots += '</span>';
            }

            // Calculate percentage relative to max tokens (for visual scaling)
            // totalTokens here is actually maxTokens for relative scaling
            const maxTokens = totalTokens;
            const pctBarWidth = (maxTokens > 0 && !isExcluded) ? ((node.tokens || 0) / maxTokens * 100) : 0;
            const pctDisplay = pctBarWidth >= 0.1 ? pctBarWidth.toFixed(1) + '%' : (isExcluded ? '—' : '<0.1%');

            // Get parent folder path (everything except filename)
            const pathParts = node.path.split('/');
            const folderPath = pathParts.length > 1 ? pathParts.slice(0, -1).join('/') : '';

            let html = `<div class="tree-node" id="${nodeId}">
                <div class="${rowClass}" onclick="toggleChildCascade('${safePath}')">
                    <span class="tree-node-indent">${guidesHtml}<span class="tree-node-connector ${isLastSibling ? 'last' : ''}"></span></span>
                    <span class="tree-node-toggle ${hasChildren ? '' : 'leaf'}" onclick="event.stopPropagation(); toggleTreeNode('${nodeId}')">▼</span>
                    <span class="${checkboxClass}">${checkboxContent}</span>
                    <span class="tree-node-icon">📄</span>
                    <span class="tree-node-name" title="${node.path}">${node.name}</span>
                    <span class="tree-node-folder-path" title="${node.path}">${folderPath}</span>
                    ${connectionDots}
                    <span class="tree-node-metrics">${node.lines} L</span>
                    <span class="tree-node-pct-bar ${isExcluded ? 'excluded' : ''}" title="${isExcluded ? 'Excluded' : pctDisplay + ' relative to largest file'}">
                        <span class="pct-fill" style="width:${pctBarWidth}%"></span>
                    </span>
                </div>`;

            if (hasChildren) {
                html += `<div class="tree-node-children" id="${nodeId}-children">`;
                const children = node.children;
                children.forEach((child, idx) => {
                    const isLast = idx === children.length - 1;
                    const newGuides = [...guides, isLastSibling ? 'empty' : '', isLast ? 'last' : ''];
                    html += renderTreeNode(child, newGuides.filter(g => g), false, isLast, isExcluded, totalTokens);
                });
                html += '</div>';
            }

            html += '</div>';
            return html;
        }

        function toggleTreeNode(nodeId) {
            const children = document.getElementById(nodeId + '-children');
            const toggle = document.querySelector(`#${nodeId} > .tree-node-row .tree-node-toggle`);
            if (children && toggle) {
                children.classList.toggle('collapsed');
                toggle.classList.toggle('collapsed');
            }
        }

        function toggleChild(path) {
            if (excludedChildren.has(path)) {
                excludedChildren.delete(path);
            } else {
                excludedChildren.add(path);
            }
            renderBothPreviews();
        }

        function toggleChildCascade(path) {
            // Find the node to get its descendants
            const node = findNodeByPath(childrenTreeData, path);
            if (!node) {
                toggleChild(path);
                return;
            }

            const isCurrentlyExcluded = excludedChildren.has(path);
            const descendants = getDescendantPaths(node);

            if (isCurrentlyExcluded) {
                // Include this node and all descendants
                excludedChildren.delete(path);
                for (const desc of descendants) {
                    excludedChildren.delete(desc);
                }
            } else {
                // Exclude this node (descendants will be inherited-excluded automatically)
                excludedChildren.add(path);
                // Also remove any explicit exclusions on descendants (they inherit from parent)
                for (const desc of descendants) {
                    excludedChildren.delete(desc);
                }
            }
            renderBothPreviews();
        }

        function renderBothPreviews() {
            renderChildrenPreview();
            if (frontendTreeData && frontendTreeData.children && frontendTreeData.children.length > 0) {
                renderFrontendPreview();
            }
        }

        function getAllExcludedPaths() {
            // Collect all paths that are excluded (directly or inherited)
            if (!childrenTreeData) return Array.from(excludedChildren);

            const allExcluded = new Set();
            function collectExcluded(node, ancestorExcluded) {
                const isDirectlyExcluded = excludedChildren.has(node.path);
                const isExcluded = isDirectlyExcluded || ancestorExcluded;

                if (!node.is_root && isExcluded) {
                    allExcluded.add(node.path);
                }

                for (const child of (node.children || [])) {
                    collectExcluded(child, isExcluded);
                }
            }
            collectExcluded(childrenTreeData, false);
            return Array.from(allExcluded);
        }

        // Frontend preview functions
        function previewFrontend() {
            if (!selectedFile) return;
            const sectionEl = document.getElementById('frontend-section');
            const previewEl = document.getElementById('frontend-preview');
            const checkEl = document.getElementById('include-frontend-check');

            // Reset state
            if (checkEl) checkEl.checked = false;
            includeFrontend = false;

            fetch('/api/preview-frontend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: selectedFile._path })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    sectionEl.style.display = 'none';
                    return;
                }
                frontendTreeData = data.tree;
                if (frontendTreeData && frontendTreeData.children && frontendTreeData.children.length > 0) {
                    sectionEl.style.display = 'block';
                    renderFrontendPreview();
                } else {
                    sectionEl.style.display = 'none';
                }
            })
            .catch(() => {
                sectionEl.style.display = 'none';
            });
        }

        function toggleFrontendInclude() {
            const checkEl = document.getElementById('include-frontend-check');
            includeFrontend = checkEl ? checkEl.checked : false;
        }

        function renderFrontendPreview() {
            const previewEl = document.getElementById('frontend-preview');
            if (!frontendTreeData || !frontendTreeData.children || frontendTreeData.children.length === 0) {
                previewEl.innerHTML = '';
                return;
            }

            const totals = calculateFrontendTotals(frontendTreeData);

            // Calculate unified max tokens across both trees (for relative scaling)
            const backendMaxTokens = childrenTreeData
                ? findMaxTokensInTree(childrenTreeData, excludedChildren)
                : 0;
            const frontendMaxTokens = findMaxTokensInFrontendTree(frontendTreeData, excludedFrontend);
            const unifiedMaxTokens = Math.max(backendMaxTokens, frontendMaxTokens);

            let html = `<div class="frontend-tree-box">
                <div class="frontend-tree-header">
                    <div class="children-tree-header-row">
                        <h4>Front-End Files</h4>
                        <span class="frontend-tree-totals">${totals.included}/${totals.total} files | ${totals.lines.toLocaleString()} L | ${totals.tokens.toLocaleString()} T</span>
                        <span class="code-size-label">Code Size</span>
                    </div>
                    <div class="children-tree-header-row">
                        <div class="children-tree-controls">
                            <button class="tree-control-btn" onclick="selectAllFrontend()">✓ All</button>
                            <button class="tree-control-btn" onclick="selectNoneFrontend()">✗ None</button>
                        </div>
                    </div>
                </div>
                <div class="children-tree-content">
                    ${renderFrontendTreeNodes(frontendTreeData.children, [], false, unifiedMaxTokens)}
                </div>
            </div>`;

            previewEl.innerHTML = html;
        }

        function calculateAllFrontendTokens(node, excludedPaths = new Set(), ancestorExcluded = false) {
            let total = 0;
            const isExcluded = excludedPaths.has(node.path) || ancestorExcluded;
            if (!node.is_root && !isExcluded) {
                total += node.tokens || 0;
            }
            for (const child of (node.children || [])) {
                total += calculateAllFrontendTokens(child, excludedPaths, isExcluded);
            }
            return total;
        }

        function findMaxTokensInFrontendTree(node, excludedPaths = new Set(), ancestorExcluded = false) {
            let maxTokens = 0;
            const isExcluded = excludedPaths.has(node.path) || ancestorExcluded;
            if (!node.is_root && !isExcluded) {
                maxTokens = node.tokens || 0;
            }
            for (const child of (node.children || [])) {
                const childMax = findMaxTokensInFrontendTree(child, excludedPaths, isExcluded);
                if (childMax > maxTokens) maxTokens = childMax;
            }
            return maxTokens;
        }

        function renderFrontendTreeNodes(nodes, guides, ancestorExcluded, totalTokens = 0) {
            if (!nodes || nodes.length === 0) return '';
            return nodes.map((node, index) => {
                const isLast = index === nodes.length - 1;
                return renderFrontendTreeNode(node, guides, isLast, ancestorExcluded, totalTokens);
            }).join('');
        }

        function renderFrontendTreeNode(node, guides, isLastSibling, ancestorExcluded, totalTokens = 0) {
            const isExcluded = excludedFrontend.has(node.path);
            const isInheritedExcluded = ancestorExcluded && !excludedFrontend.has(node.path);
            const effectiveExcluded = isExcluded || ancestorExcluded;

            const fileType = node.file_type || 'unknown';
            const icon = fileType === 'html' ? '📄' : fileType === 'js' || fileType === 'ts' ? '📜' : fileType === 'css' ? '🎨' : '📁';

            let guideHtml = '';
            for (let i = 0; i < guides.length; i++) {
                guideHtml += `<span class="tree-guide" style="left:${i * 20 + 12}px;${guides[i] ? '' : 'display:none;'}"></span>`;
            }

            const depth = guides.length;
            const connectorLeft = depth * 20;
            const connector = depth > 0 ? `<span class="tree-connector" style="left:${connectorLeft - 8}px;width:12px;"></span>` : '';

            const hasChildren = node.children && node.children.length > 0;
            const toggleIcon = hasChildren ? '▼' : '';
            const toggleCls = hasChildren ? '' : 'hidden';

            const checkCls = isExcluded ? '' : (isInheritedExcluded ? 'inherited-unchecked' : 'checked');
            const rowCls = effectiveExcluded ? 'excluded' : '';
            const nameCls = isInheritedExcluded ? 'inherited-excluded' : (isExcluded ? 'excluded' : '');

            const typeBadge = `<span class="frontend-file-type ${fileType}">${fileType.toUpperCase()}</span>`;

            // Build connection dots HTML for frontend files
            let connectionDots = '';
            if (node.connections && node.connections.length > 0) {
                connectionDots = '<span class="tree-node-connections">';
                for (const conn of node.connections) {
                    connectionDots += `<span class="connection-dot" style="background:${conn.color};" title="${conn.label}"></span>`;
                }
                connectionDots += '</span>';
            }

            // Calculate percentage relative to max tokens (for visual scaling)
            // totalTokens here is actually maxTokens for relative scaling
            const maxTokens = totalTokens;
            const pctBarWidth = (maxTokens > 0 && !effectiveExcluded) ? ((node.tokens || 0) / maxTokens * 100) : 0;
            const pctDisplay = pctBarWidth >= 0.1 ? pctBarWidth.toFixed(1) + '%' : (effectiveExcluded ? '—' : '<0.1%');

            // Get parent folder path
            const pathParts = node.path.split('/');
            const folderPath = pathParts.length > 1 ? pathParts.slice(0, -1).join('/') : '';

            let html = `
                <div class="tree-node">
                    <div class="tree-node-row ${rowCls}" style="padding-left:${depth * 20 + 8}px;" onclick="toggleFrontendCascade('${node.path}')">
                        ${guideHtml}
                        ${connector}
                        <span class="tree-node-toggle ${toggleCls}" onclick="event.stopPropagation();toggleFrontendNodeCollapse(this)">${toggleIcon}</span>
                        <span class="tree-node-checkbox ${checkCls}">✓</span>
                        <span class="tree-node-icon">${icon}</span>
                        <span class="tree-node-name ${nameCls}">${node.name}</span>
                        <span class="tree-node-folder-path" title="${node.path}">${folderPath}</span>
                        ${connectionDots}
                        ${typeBadge}
                        <span class="tree-node-metrics">${node.lines || 0} L</span>
                        <span class="tree-node-pct-bar ${effectiveExcluded ? 'excluded' : ''}" title="${effectiveExcluded ? 'Excluded' : pctDisplay + ' relative to largest file'}">
                            <span class="pct-fill" style="width:${pctBarWidth}%"></span>
                        </span>
                    </div>`;

            if (hasChildren) {
                const newGuides = [...guides, !isLastSibling];
                html += `<div class="tree-node-children expanded">
                    ${renderFrontendTreeNodes(node.children, newGuides, effectiveExcluded, totalTokens)}
                </div>`;
            }

            html += '</div>';
            return html;
        }

        function toggleFrontendNodeCollapse(toggleEl) {
            const nodeEl = toggleEl.closest('.tree-node');
            const childrenEl = nodeEl.querySelector(':scope > .tree-node-children');
            if (childrenEl) {
                const isCollapsed = !childrenEl.classList.contains('expanded');
                childrenEl.classList.toggle('expanded', isCollapsed);
                toggleEl.style.transform = isCollapsed ? '' : 'rotate(-90deg)';
            }
        }

        function toggleFrontendCascade(path) {
            const wasExcluded = excludedFrontend.has(path);

            function findNode(node, targetPath) {
                if (node.path === targetPath) return node;
                for (const child of (node.children || [])) {
                    const found = findNode(child, targetPath);
                    if (found) return found;
                }
                return null;
            }

            function getAllDescendantPaths(node) {
                const paths = [node.path];
                for (const child of (node.children || [])) {
                    paths.push(...getAllDescendantPaths(child));
                }
                return paths;
            }

            const targetNode = findNode(frontendTreeData, path);
            if (!targetNode) return;

            const allPaths = getAllDescendantPaths(targetNode);

            if (wasExcluded) {
                // Re-include this and remove explicit exclusions from descendants
                allPaths.forEach(p => excludedFrontend.delete(p));
            } else {
                // Exclude this node
                excludedFrontend.add(path);
                // Remove explicit exclusions from descendants (they inherit)
                allPaths.slice(1).forEach(p => excludedFrontend.delete(p));
            }

            renderBothPreviews();
        }

        function selectAllFrontend() {
            excludedFrontend = new Set();
            renderBothPreviews();
        }

        function selectNoneFrontend() {
            function collectPaths(node) {
                const paths = [];
                if (!node.is_root) paths.push(node.path);
                for (const child of (node.children || [])) {
                    paths.push(...collectPaths(child));
                }
                return paths;
            }
            excludedFrontend = new Set(collectPaths(frontendTreeData));
            renderBothPreviews();
        }

        function calculateFrontendTotals(tree) {
            let total = 0, included = 0, lines = 0, tokens = 0;

            function traverse(node, ancestorExcluded) {
                if (node.is_root) {
                    for (const child of (node.children || [])) {
                        traverse(child, false);
                    }
                    return;
                }

                total++;
                const isExcluded = excludedFrontend.has(node.path) || ancestorExcluded;
                if (!isExcluded) {
                    included++;
                    lines += node.lines || 0;
                    tokens += node.tokens || 0;
                }
                for (const child of (node.children || [])) {
                    traverse(child, isExcluded);
                }
            }

            traverse(tree, false);
            return { total, included, lines, tokens };
        }

        function getAllExcludedFrontendPaths() {
            const allExcluded = new Set();
            function collectExcluded(node, ancestorExcluded) {
                if (node.is_root) {
                    for (const child of (node.children || [])) {
                        collectExcluded(child, false);
                    }
                    return;
                }

                const isDirectlyExcluded = excludedFrontend.has(node.path);
                const isExcluded = isDirectlyExcluded || ancestorExcluded;

                if (isExcluded) {
                    allExcluded.add(node.path);
                }

                for (const child of (node.children || [])) {
                    collectExcluded(child, isExcluded);
                }
            }
            if (frontendTreeData) {
                collectExcluded(frontendTreeData, false);
            }
            return Array.from(allExcluded);
        }

        function copySnapshot() {
            if (!selectedFile) return;

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
                    path: selectedFile._path,
                    parent_depth: parentDepth,
                    include_chain: includeChain,
                    chain_length: chainLength > 0 ? chainLength : null,
                    child_depth: childDepth,
                    child_max_tokens: childMaxTokens,
                    excluded_children: allExcluded,
                    include_frontend: includeFrontend,
                    excluded_frontend: allExcludedFrontend
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

        function formatPath(pathArray) {
            return pathArray.map((p, i) => {
                const isLast = i === pathArray.length - 1;
                const cls = isLast ? 'current' : 'file';
                const arrow = i < pathArray.length - 1 ? '<span class="arrow">→</span>' : '';
                return `<span class="${cls}">${p.split('/').pop()}</span>${arrow}`;
            }).join('');
        }

        // Context Menu
        function showContextMenu(e, data) {
            e.preventDefault();
            contextMenuFile = data;
            const menu = document.getElementById('context-menu');
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
            menu.classList.add('visible');
        }

        document.addEventListener('click', () => {
            document.getElementById('context-menu').classList.remove('visible');
        });

        function addAsEntryPoint() {
            if (contextMenuFile) {
                promptAddEntryPoint(contextMenuFile._path);
            }
        }

        function copyPath() {
            if (contextMenuFile) {
                navigator.clipboard.writeText(contextMenuFile._path);
            }
        }

        function promptAddEntryPoint(path) {
            document.getElementById('entry-path').value = path;
            document.getElementById('entry-label').value = path.split('/').pop().replace('.py', '').toUpperCase();

            const picker = document.getElementById('color-picker');
            picker.innerHTML = '';
            selectedColor = availableColors[0];

            for (const color of availableColors) {
                const opt = document.createElement('div');
                opt.className = 'color-option' + (color === selectedColor ? ' selected' : '');
                opt.style.background = color.hex;
                opt.textContent = color.emoji;
                opt.onclick = () => {
                    picker.querySelectorAll('.color-option').forEach(o => o.classList.remove('selected'));
                    opt.classList.add('selected');
                    selectedColor = color;
                };
                picker.appendChild(opt);
            }

            document.getElementById('add-entry-modal').classList.add('visible');
        }

        function closeAddEntry() {
            document.getElementById('add-entry-modal').classList.remove('visible');
        }

        function saveEntryPoint() {
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
                    color: selectedColor.hex,
                    emoji: selectedColor.emoji
                })
            }).then(() => {
                closeAddEntry();
                refresh();
            });
        }

        function openSettings() {
            fetch('/api/config')
                .then(r => r.json())
                .then(config => {
                    document.getElementById('current-root').textContent = 'Current: ' + (config.project_root || 'Not set');
                });

            const list = document.getElementById('entry-point-list');
            list.innerHTML = '';

            const eps = treeData.config.entry_points || [];
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

        function toggleEntryPoint(path) {
            fetch('/api/entry-points/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            })
            .then(r => r.json())
            .then(() => {
                closeSettings();
                refresh();
            });
        }

        function changeProjectRoot(newRoot) {
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
                loadData();
            })
            .catch(err => alert('Error: ' + err));
        }

        function loadSuggestions() {
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

        function closeSettings() {
            document.getElementById('settings-modal').classList.remove('visible');
        }

        function loadSubmodules() {
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

        function toggleSubmodule(path) {
            fetch('/api/submodules/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            })
            .then(r => r.json())
            .then(() => {
                loadSubmodules();
                refresh();
            });
        }

        function removeEntryPoint(path) {
            if (confirm('Remove this entry point?')) {
                fetch('/api/entry-points', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: path })
                }).then(() => {
                    closeSettings();
                    refresh();
                });
            }
        }

        // Search
        document.getElementById('search').addEventListener('input', (e) => {
            searchQuery = e.target.value;
            renderTree(treeData.tree);
        });

        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                document.getElementById('search').focus();
            }
        });

        // Resizable panel
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

        // ===== FULLSCREEN DEPENDENCY VIEWER =====

        function openFullscreenViewer() {
            if (!selectedFile) return;

            // Reset exclusions
            excludedParents = new Set();
            excludedChain = new Set();
            excludedChildren = new Set();

            // Create fullscreen container
            const viewer = document.createElement('div');
            viewer.className = 'dep-viewer-fullscreen';
            viewer.id = 'fullscreen-viewer';
            viewer.innerHTML = `
                <div class="dep-viewer-header">
                    <div style="display:flex;align-items:center;">
                        <span class="dep-viewer-title">📊 Dependency Viewer</span>
                        <span class="dep-viewer-subtitle" id="fs-file-path">${selectedFile._path}</span>
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
                body: JSON.stringify({ path: selectedFile._path })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('fs-body').innerHTML = `<div style="color:#f85149;padding:20px;">${data.error}</div>`;
                    return;
                }
                fullDepData = data;
                renderFullscreenViewer();
            });
        }

        function closeFullscreenViewer() {
            const viewer = document.getElementById('fullscreen-viewer');
            if (viewer) viewer.remove();
            fullDepData = null;
        }

        function renderFullscreenViewer() {
            if (!fullDepData) return;
            const body = document.getElementById('fs-body');

            // Calculate totals
            const totals = calculateFullTotals();
            document.getElementById('fs-totals').textContent =
                `${totals.included}/${totals.total} files | ${totals.lines.toLocaleString()} lines | ${totals.tokens.toLocaleString()} tokens`;

            let html = '';

            // Target file
            const t = fullDepData.target;
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
            if (fullDepData.chains && fullDepData.chains.length > 0) {
                for (const chain of fullDepData.chains) {
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
            if (fullDepData.parents && fullDepData.parents.length > 0) {
                html += `
                    <div class="dep-viewer-section">
                        <div class="dep-viewer-section-header">
                            <h4>⬆️ Parents (files that import this)</h4>
                            <span class="section-badge parent">${fullDepData.parents.length} files</span>
                            <button class="tree-control-btn" style="margin-left:auto;" onclick="fsToggleAllParents()">Toggle All</button>
                        </div>
                        <div class="dep-viewer-section-content">
                            ${renderParentsList(fullDepData.parents)}
                        </div>
                    </div>
                `;
            }

            // Children section
            if (fullDepData.children_tree && fullDepData.children_tree.children && fullDepData.children_tree.children.length > 0) {
                const childCount = countTreeNodes(fullDepData.children_tree);
                const maxDepth = getMaxDepth(fullDepData.children_tree);
                const fsMaxTokens = findMaxTokensInTree(fullDepData.children_tree, excludedChildren);

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
                            ${renderTreeNode(fullDepData.children_tree, [], true, false, false, fsMaxTokens)}
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
                const isExcluded = excludedParents.has(p.path);
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
                const isExcluded = excludedChain.has(chainKey);
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
            if (!fullDepData) return totals;

            // Target always included
            totals.total++;
            totals.included++;
            totals.lines += fullDepData.target.lines || 0;
            totals.tokens += fullDepData.target.tokens || 0;

            // Parents
            for (const p of (fullDepData.parents || [])) {
                totals.total++;
                if (!excludedParents.has(p.path)) {
                    totals.included++;
                    totals.lines += p.lines || 0;
                    totals.tokens += p.tokens || 0;
                }
            }

            // Chain files
            for (const chain of (fullDepData.chains || [])) {
                for (const f of (chain.files || [])) {
                    totals.total++;
                    const chainKey = `${chain.label}:${f.path}`;
                    if (!excludedChain.has(chainKey)) {
                        totals.included++;
                        totals.lines += f.lines || 0;
                        totals.tokens += f.tokens || 0;
                    }
                }
            }

            // Children (recursive with inheritance)
            if (fullDepData.children_tree) {
                addChildTotals(fullDepData.children_tree, totals, false);
            }

            return totals;
        }

        function addChildTotals(node, totals, ancestorExcluded) {
            const isDirectlyExcluded = excludedChildren.has(node.path);
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
        function fsToggleParent(path) {
            if (excludedParents.has(path)) {
                excludedParents.delete(path);
            } else {
                excludedParents.add(path);
            }
            renderFullscreenViewer();
        }

        function fsToggleChainFile(label, path) {
            const key = `${label}:${path}`;
            if (excludedChain.has(key)) {
                excludedChain.delete(key);
            } else {
                excludedChain.add(key);
            }
            renderFullscreenViewer();
        }

        function fsToggleChain(label) {
            if (!fullDepData) return;
            const chain = fullDepData.chains.find(c => c.label === label);
            if (!chain) return;

            // Check if all are excluded
            const allExcluded = chain.files.every(f => excludedChain.has(`${label}:${f.path}`));

            for (const f of chain.files) {
                const key = `${label}:${f.path}`;
                if (allExcluded) {
                    excludedChain.delete(key);
                } else {
                    excludedChain.add(key);
                }
            }
            renderFullscreenViewer();
        }

        function fsToggleAllParents() {
            if (!fullDepData) return;
            const allExcluded = fullDepData.parents.every(p => excludedParents.has(p.path));

            for (const p of fullDepData.parents) {
                if (allExcluded) {
                    excludedParents.delete(p.path);
                } else {
                    excludedParents.add(p.path);
                }
            }
            renderFullscreenViewer();
        }

        function fsToggleAllChildren() {
            if (!fullDepData || !fullDepData.children_tree) return;

            const allPaths = new Set();
            collectAllPaths(fullDepData.children_tree, allPaths);

            const pathsArray = Array.from(allPaths);
            const allExcluded = pathsArray.length > 0 && pathsArray.every(p => excludedChildren.has(p));

            if (allExcluded) {
                excludedChildren = new Set();
            } else {
                excludedChildren = new Set(pathsArray);
            }
            renderFullscreenViewer();
        }

        function fsSelectChildrenToDepth(maxDepth) {
            if (!fullDepData || !fullDepData.children_tree) return;
            excludedChildren = new Set();
            collectPathsBeyondDepth(fullDepData.children_tree, maxDepth, excludedChildren);
            renderFullscreenViewer();
        }

        function fsSelectAll() {
            excludedParents = new Set();
            excludedChain = new Set();
            excludedChildren = new Set();
            renderFullscreenViewer();
        }

        function fsSelectNone() {
            if (!fullDepData) return;

            // Exclude all parents
            for (const p of (fullDepData.parents || [])) {
                excludedParents.add(p.path);
            }

            // Exclude all chain files
            for (const chain of (fullDepData.chains || [])) {
                for (const f of (chain.files || [])) {
                    excludedChain.add(`${chain.label}:${f.path}`);
                }
            }

            // Exclude all children
            if (fullDepData.children_tree) {
                const allChildPaths = new Set();
                collectAllPaths(fullDepData.children_tree, allChildPaths);
                excludedChildren = allChildPaths;
            }

            renderFullscreenViewer();
        }

        function fsSelectParentsOnly() {
            fsSelectNone();
            excludedParents = new Set();
            renderFullscreenViewer();
        }

        function fsSelectChildrenOnly() {
            fsSelectNone();
            excludedChildren = new Set();
            renderFullscreenViewer();
        }

        function copyFromFullscreen() {
            if (!selectedFile || !fullDepData) return;

            // Collect all excluded paths for the API
            const allExcludedChildren = getAllExcludedPaths();

            // Build excluded parents list
            const excludedParentsList = Array.from(excludedParents);

            // For now, use the existing copy-snapshot API with manual exclusions
            // We include parents/chain based on what's selected
            const statusEl = document.createElement('div');
            statusEl.style.cssText = 'position:fixed;bottom:20px;right:20px;background:#238636;color:#fff;padding:12px 20px;border-radius:8px;z-index:4000;';
            statusEl.textContent = 'Generating snapshot...';
            document.body.appendChild(statusEl);

            fetch('/api/copy-snapshot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: selectedFile._path,
                    parent_depth: excludedParents.size === 0 ? 10 : 0,
                    include_chain: excludedChain.size === 0,
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

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const viewer = document.getElementById('fullscreen-viewer');
                if (viewer) closeFullscreenViewer();
                const folderBrowser = document.getElementById('folder-browser-modal');
                if (folderBrowser.classList.contains('visible')) closeFolderBrowser();
                const deleteModal = document.getElementById('delete-orphans-modal');
                if (deleteModal.classList.contains('visible')) closeDeleteOrphansModal();
                const chatModal = document.getElementById('chat-modal');
                if (chatModal.classList.contains('visible')) closeChatModal();
            }
        });

        let currentBrowsePath = '';
        let autocompleteTimeout = null;

        function openFolderBrowser() {
            fetch('/api/config')
                .then(r => r.json())
                .then(config => {
                    currentBrowsePath = config.project_root || '';
                    document.getElementById('folder-path-input').value = currentBrowsePath;
                    navigateToFolder(currentBrowsePath);
                    loadRecentProjects();
                    document.getElementById('folder-browser-modal').classList.add('visible');
                });
        }

        function closeFolderBrowser() {
            document.getElementById('folder-browser-modal').classList.remove('visible');
            document.getElementById('autocomplete-dropdown').classList.remove('visible');
        }

        function navigateToFolder(path) {
            currentBrowsePath = path;
            document.getElementById('folder-path-input').value = path;
            
            fetch('/api/browse-directory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            })
            .then(r => r.json())
            .then(data => {
                currentBrowsePath = data.current;
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

        function selectRecentProject(path) {
            closeFolderBrowser();
            changeProjectRoot(path);
        }

        function selectCurrentFolder() {
            if (!currentBrowsePath) return;
            closeFolderBrowser();
            changeProjectRoot(currentBrowsePath);
        }

        function handlePathInput() {
            clearTimeout(autocompleteTimeout);
            autocompleteTimeout = setTimeout(() => {
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

        function handlePathKeydown(e) {
            if (e.key === 'Enter') {
                document.getElementById('autocomplete-dropdown').classList.remove('visible');
                navigateToFolder(document.getElementById('folder-path-input').value);
            }
        }

        function selectAutocompletePath(path) {
            document.getElementById('autocomplete-dropdown').classList.remove('visible');
            navigateToFolder(path);
        }

        let orphanDeleteData = null;

        function openDeleteOrphansModal() {
            document.getElementById('delete-orphans-modal').classList.add('visible');
            document.getElementById('delete-orphans-footer').style.display = 'none';
            document.getElementById('delete-orphans-body').innerHTML = '<div class="loading"><div class="spinner"></div> Loading orphan files...</div>';
            
            fetch('/api/orphans/preview-delete', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    orphanDeleteData = data;
                    renderDeleteOrphansPreview(data);
                })
                .catch(err => {
                    document.getElementById('delete-orphans-body').innerHTML = `<div style="color: #f85149; padding: 20px;">Error: ${err}</div>`;
                });
        }

        function closeDeleteOrphansModal() {
            document.getElementById('delete-orphans-modal').classList.remove('visible');
            orphanDeleteData = null;
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

        function validateDeleteConfirmation() {
            const input = document.getElementById('delete-confirm-input');
            const btn = document.getElementById('confirm-delete-btn');
            const isValid = input.value === 'DELETE';
            
            btn.disabled = !isValid;
            input.classList.toggle('valid', isValid);
        }

        function executeOrphanDeletion() {
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
                        closeSettings();
                        refresh();
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

        // ============================================================================
        // Chat with Claude
        // ============================================================================

        let chatHistory = [];
        let currentSnapshotContent = null;
        let isChatStreaming = false;

        function openChatModal() {
            if (!selectedFile) {
                alert('Please select a file first');
                return;
            }

            // Generate the snapshot content (same as copy)
            generateSnapshotForChat().then(content => {
                currentSnapshotContent = content;
                const badge = document.getElementById('chat-context-badge');
                if (content) {
                    const lines = content.split('\n').length;
                    const chars = content.length;
                    badge.textContent = `${lines} lines | ${Math.round(chars/4)} tokens (approx)`;
                    badge.classList.add('loaded');
                } else {
                    badge.textContent = 'No context loaded';
                    badge.classList.remove('loaded');
                }
            });

            document.getElementById('chat-modal').classList.add('visible');
            document.getElementById('chat-input').focus();
        }

        function closeChatModal() {
            document.getElementById('chat-modal').classList.remove('visible');
        }

        async function generateSnapshotForChat() {
            if (!selectedFile) return null;

            const allExcluded = getAllExcludedPaths();
            const allExcludedFrontend = getAllExcludedFrontendPaths();

            try {
                const response = await fetch('/api/copy-snapshot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        path: selectedFile._path,
                        parent_depth: parentDepth,
                        include_chain: includeChain,
                        chain_length: chainLength > 0 ? chainLength : null,
                        child_depth: childDepth,
                        child_max_tokens: childMaxTokens,
                        excluded_children: allExcluded,
                        include_frontend: includeFrontend,
                        excluded_frontend: allExcludedFrontend
                    })
                });
                const data = await response.json();
                return data.content || null;
            } catch (e) {
                console.error('Failed to generate snapshot:', e);
                return null;
            }
        }

        function handleChatKeydown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendChatMessage();
            }
        }

        async function sendChatMessage() {
            if (isChatStreaming) return;

            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            if (!message) return;

            input.value = '';
            isChatStreaming = true;
            updateSendButton();

            // Add user message to UI
            addChatMessage('user', message);
            chatHistory.push({ role: 'user', content: message });

            // Create assistant message placeholder
            const assistantDiv = addChatMessage('assistant', '');
            const contentDiv = assistantDiv.querySelector('.chat-message-content');
            contentDiv.innerHTML = '<span style="color:#8b949e">Thinking...</span>';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        snapshot: currentSnapshotContent || '',
                        history: chatHistory.slice(0, -1)
                    })
                });

                if (!response.ok) {
                    const errText = await response.text();
                    contentDiv.innerHTML = `<span class="chat-error">Error ${response.status}: ${errText}</span>`;
                    isChatStreaming = false;
                    updateSendButton();
                    return;
                }

                // Handle both streaming and non-streaming responses
                const contentType = response.headers.get('content-type') || '';

                if (contentType.includes('text/event-stream')) {
                    // SSE streaming
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let fullResponse = '';
                    let buffer = '';

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n');
                        buffer = lines.pop() || '';

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data === '[DONE]') continue;
                                if (data.startsWith('[ERROR]')) {
                                    contentDiv.innerHTML = `<span class="chat-error">${data}</span>`;
                                    continue;
                                }
                                fullResponse += data;
                                renderMarkdown(contentDiv, fullResponse);
                                scrollChatToBottom();
                            }
                        }
                    }

                    if (fullResponse) {
                        chatHistory.push({ role: 'assistant', content: fullResponse });
                    } else {
                        contentDiv.innerHTML = '<span class="chat-error">No response received</span>';
                    }
                } else {
                    // JSON response fallback
                    const data = await response.json();
                    if (data.error) {
                        contentDiv.innerHTML = `<span class="chat-error">${data.error}</span>`;
                    } else if (data.content) {
                        renderMarkdown(contentDiv, data.content);
                        chatHistory.push({ role: 'assistant', content: data.content });
                    }
                }

            } catch (e) {
                contentDiv.innerHTML = `<span class="chat-error">Error: ${e.message}</span>`;
            }

            isChatStreaming = false;
            updateSendButton();
        }

        function addChatMessage(role, content) {
            const messagesDiv = document.getElementById('chat-messages');

            // Remove welcome message if present
            const welcome = messagesDiv.querySelector('.chat-welcome');
            if (welcome) welcome.remove();

            const msgDiv = document.createElement('div');
            msgDiv.className = `chat-message chat-message-${role}`;

            const labelDiv = document.createElement('div');
            labelDiv.className = 'chat-message-label';
            labelDiv.textContent = role === 'user' ? 'You' : 'Claude';

            const contentDiv = document.createElement('div');
            contentDiv.className = 'chat-message-content';

            if (role === 'user') {
                contentDiv.textContent = content;
            } else if (content) {
                renderMarkdown(contentDiv, content);
            }

            msgDiv.appendChild(labelDiv);
            msgDiv.appendChild(contentDiv);
            messagesDiv.appendChild(msgDiv);

            scrollChatToBottom();
            return msgDiv;
        }

        function renderMarkdown(element, content) {
            if (typeof marked === 'undefined') {
                element.textContent = content;
                return;
            }

            // Configure marked with highlight.js
            marked.setOptions({
                breaks: true,
                gfm: true,
                highlight: function(code, lang) {
                    if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(code, { language: lang }).value;
                        } catch (e) {}
                    }
                    // For unknown languages or plain text, just escape HTML
                    return code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                }
            });

            // Parse and sanitize
            let html = marked.parse(content);
            if (typeof DOMPurify !== 'undefined') {
                html = DOMPurify.sanitize(html);
            }

            element.innerHTML = html;

            // Apply highlight.js to any code blocks that weren't highlighted
            if (typeof hljs !== 'undefined') {
                element.querySelectorAll('pre code:not(.hljs)').forEach(block => {
                    hljs.highlightElement(block);
                });
            }
        }

        function scrollChatToBottom() {
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function updateSendButton() {
            const btn = document.getElementById('chat-send-btn');
            btn.disabled = isChatStreaming;
            btn.textContent = isChatStreaming ? '...' : 'Send';
        }

        function clearChatHistory() {
            chatHistory = [];
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML = `
                <div class="chat-welcome">
                    <div class="chat-welcome-icon">🔍</div>
                    <p>Load a file's dependencies and ask questions about the code.</p>
                    <p class="chat-welcome-hint">The current snapshot will be used as context.</p>
                </div>
            `;
        }
