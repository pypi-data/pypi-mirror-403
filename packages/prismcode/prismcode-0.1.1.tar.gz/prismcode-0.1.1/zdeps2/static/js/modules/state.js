// ============================================================================
// Global State - Shared application state
// ============================================================================

export const state = {
    treeData: null,
    currentFilter: 'all',
    searchQuery: '',
    selectedFile: null,
    contextMenuFile: null,
    selectedColor: null,
    availableColors: [],

    // Snapshot controls
    parentDepth: 1,
    includeChain: false,
    chainLength: 0,
    childDepth: 0,
    childMaxTokens: 0,

    // Exclusion sets
    excludedChildren: new Set(),
    excludedParents: new Set(),
    excludedChain: new Set(),
    excludedFrontend: new Set(),

    // Extra files for snapshot (manually selected from sidebar)
    extraFiles: new Set(),

    // Dependency data
    childrenData: null,
    childrenTreeData: null,
    fullDepData: null,
    frontendTreeData: null,
    includeFrontend: false,

    // Folder browser
    currentBrowsePath: '',
    autocompleteTimeout: null,

    // Delete orphans
    orphanDeleteData: null,

    // Chat
    chatHistory: [],
    currentSnapshotContent: null,
    isChatStreaming: false
};

// Reset functions
export function resetFileSelection() {
    state.excludedChildren = new Set();
    state.childrenData = null;
    state.frontendTreeData = null;
    state.excludedFrontend = new Set();
    state.includeFrontend = false;
}

export function resetFullscreenExclusions() {
    state.excludedParents = new Set();
    state.excludedChain = new Set();
    state.excludedChildren = new Set();
}
