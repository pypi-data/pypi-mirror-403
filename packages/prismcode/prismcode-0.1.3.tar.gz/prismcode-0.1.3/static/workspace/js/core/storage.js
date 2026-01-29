/* Prism Workspace - Storage */
const STORAGE_KEY = 'prism-workspace';

export function loadLayout() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch (e) {
    return null;
  }
}

export function saveLayout(layout) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(layout));
  } catch (e) {
    console.warn('Failed to save layout:', e);
  }
}

export function loadSetting(key, defaultValue) {
  try {
    const settings = JSON.parse(localStorage.getItem('prism-settings') || '{}');
    return settings[key] ?? defaultValue;
  } catch (e) {
    return defaultValue;
  }
}

export function saveSetting(key, value) {
  try {
    const settings = JSON.parse(localStorage.getItem('prism-settings') || '{}');
    settings[key] = value;
    localStorage.setItem('prism-settings', JSON.stringify(settings));
  } catch (e) {
    console.warn('Failed to save setting:', e);
  }
}
