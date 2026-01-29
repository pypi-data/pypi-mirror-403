// ============================================================================
// ZDEPS2 - Main Application Entry Point
// ============================================================================
// This is the modular version of app.js that imports all functionality
// from separate modules for better organization and maintainability.
// ============================================================================

// Import state (must be first - other modules depend on it)
import { state } from './modules/state.js';

// Import all modules - order matters to avoid circular dependency issues
import { loadData, refresh } from './modules/data.js';
import { renderTree, getBadges } from './modules/tree.js';
import { showContextMenu, initContextMenuListener, addAsEntryPoint, copyPath } from './modules/context-menu.js';
import {
    previewChildren, renderChildrenPreview, selectAllChildren, selectNoneChildren,
    selectToDepth, toggleTreeNode, toggleChildCascade, getAllExcludedPaths
} from './modules/children-preview.js';
import {
    previewFrontend, renderFrontendPreview, toggleFrontendInclude,
    selectAllFrontend, selectNoneFrontend, getAllExcludedFrontendPaths
} from './modules/frontend-preview.js';
import { copySnapshot, toggleChain, generateSnapshotForChat, formatPath } from './modules/snapshot.js';
import { selectFile } from './modules/file-details.js';
import {
    openSettings, closeSettings, saveEntryPoint, closeAddEntry,
    promptAddEntryPoint, toggleEntryPoint, removeEntryPoint,
    changeProjectRoot, loadSuggestions, toggleSubmodule
} from './modules/settings.js';
import {
    openFullscreenViewer, closeFullscreenViewer, copyFromFullscreen,
    fsSelectAll, fsSelectNone, fsSelectParentsOnly, fsSelectChildrenOnly,
    fsToggleParent, fsToggleChainFile, fsToggleChain, fsToggleAllParents,
    fsToggleAllChildren, fsSelectChildrenToDepth, initEscapeListener
} from './modules/fullscreen-viewer.js';
import {
    openFolderBrowser, closeFolderBrowser, navigateToFolder,
    selectRecentProject, selectCurrentFolder, handlePathInput,
    handlePathKeydown, selectAutocompletePath
} from './modules/folder-browser.js';
import {
    openDeleteOrphansModal, closeDeleteOrphansModal,
    validateDeleteConfirmation, executeOrphanDeletion
} from './modules/delete-orphans.js';
import {
    openChatModal, closeChatModal, handleChatKeydown,
    sendChatMessage, clearChatHistory
} from './modules/chat.js';
import { initSearch, initResizer } from './modules/ui.js';

// Expose state globally for inline event handlers that need to modify it
window.state = state;

// Initialize the application
function init() {
    // Load initial data
    loadData();

    // Initialize UI components
    initContextMenuListener();
    initSearch();
    initResizer();
    initEscapeListener();
}

// Start the application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
