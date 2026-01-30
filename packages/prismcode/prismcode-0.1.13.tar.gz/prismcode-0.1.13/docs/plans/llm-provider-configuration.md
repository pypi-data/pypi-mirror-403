# Plan: LLM Provider Configuration Feature

## Overview
Allow users to configure LLM providers (Anthropic, OpenAI, Google, Groq, Ollama) through the Settings modal. Users can add API keys which are stored securely, fetch available models once a key is validated, and select which model to use project-wide.

## Goals
- Users can add/remove API keys for any supported LLM provider
- API keys are encrypted at rest (never stored in plaintext)
- Users can validate keys before saving (test API call)
- Users can fetch and browse available models per provider
- Users can select active provider + model (used for all new conversations)
- Ollama/local models supported with custom URL
- Environment variables still work as fallback

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Settings Modal)                │
│                    static/workspace/js/                     │
│                    components/preferences/llm-pane.js       │
└─────────────────────────────┬───────────────────────────────┘
                              │ REST API (/api/llm/*)
┌─────────────────────────────▼───────────────────────────────┐
│                    Backend (Flask)                          │
│                    run_web.py                               │
│                    - /api/llm/providers                     │
│                    - /api/llm/key (POST/DELETE)             │
│                    - /api/llm/validate                      │
│                    - /api/llm/models/<provider>             │
│                    - /api/llm/active                        │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    LLM Config Manager                       │
│                    core/llm_config.py (NEW FILE)            │
│                                                             │
│    ┌─────────────────────────────────────────────────┐     │
│    │  LLMConfigManager                               │     │
│    │  - _config: dict (loaded from JSON)             │     │
│    │  - _fernet: Fernet (for encryption)             │     │
│    │                                                 │     │
│    │  Methods:                                       │     │
│    │  + get_providers_status() -> list[dict]         │     │
│    │  + set_api_key(provider, key) -> bool           │     │
│    │  + get_api_key(provider) -> str | None          │     │
│    │  + delete_api_key(provider) -> bool             │     │
│    │  + validate_api_key(provider, key) -> (ok, msg) │     │
│    │  + fetch_models(provider) -> list[dict]         │     │
│    │  + get_active_config() -> dict                  │     │
│    │  + set_active_model(provider, model) -> bool    │     │
│    └─────────────────────────────────────────────────┘     │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                    Storage (~/.prism/)                      │
│                                                             │
│    ~/.prism/llm_config.json                                │
│    {                                                        │
│      "active_provider": "anthropic",                        │
│      "active_model": "claude-sonnet-4-20250514",           │
│      "keys": {                                              │
│        "anthropic": "<encrypted>",                          │
│        "openai": "<encrypted>"                              │
│      },                                                     │
│      "ollama_url": "http://localhost:11434"                │
│    }                                                        │
│                                                             │
│    ~/.prism/.llm_key  (Fernet encryption key, 600 perms)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Supported Providers

| Provider | ID | Key Env Var | LiteLLM Prefix | Notes |
|----------|-----|-------------|----------------|-------|
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | `anthropic/` | Claude models |
| OpenAI | `openai` | `OPENAI_API_KEY` | `openai/` | GPT models |
| Google | `google` | `GEMINI_API_KEY` | `gemini/` | Gemini models |
| Groq | `groq` | `GROQ_API_KEY` | `groq/` | Fast inference |
| Ollama | `ollama` | N/A | `ollama/` | Local models, custom URL |

---

## Phase 1: Backend Core - LLM Config Manager

### Focus Files
```
core/llm_config.py         # CREATE - Main config manager class
core/__init__.py           # MODIFY - Add export
```

### Implementation Details

**File: `core/llm_config.py`**

```python
"""
LLM Configuration Manager

Handles:
- Secure storage of API keys (encrypted with Fernet)
- Provider configuration and status
- Model fetching from providers
- Active model selection

Storage: ~/.prism/llm_config.json (config) + ~/.prism/.llm_key (encryption key)
"""
import os
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from cryptography.fernet import Fernet
import litellm

class LLMConfigManager:
    """Manages LLM provider configuration with secure key storage."""
    
    PROVIDERS = {
        'anthropic': {
            'name': 'Anthropic',
            'key_env': 'ANTHROPIC_API_KEY',
            'litellm_prefix': 'anthropic/',
            'default_model': 'claude-sonnet-4-20250514',
            'models': [  # Fallback if fetch fails
                {'id': 'claude-sonnet-4-20250514', 'name': 'Claude Sonnet 4'},
                {'id': 'claude-opus-4-20250514', 'name': 'Claude Opus 4'},
            ]
        },
        'openai': {
            'name': 'OpenAI',
            'key_env': 'OPENAI_API_KEY', 
            'litellm_prefix': 'openai/',
            'default_model': 'gpt-4o',
            'models': [
                {'id': 'gpt-4o', 'name': 'GPT-4o'},
                {'id': 'gpt-4o-mini', 'name': 'GPT-4o Mini'},
                {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo'},
            ]
        },
        'google': {
            'name': 'Google (Gemini)',
            'key_env': 'GEMINI_API_KEY',
            'litellm_prefix': 'gemini/',
            'default_model': 'gemini-2.0-flash',
            'models': [
                {'id': 'gemini-2.0-flash', 'name': 'Gemini 2.0 Flash'},
                {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro'},
            ]
        },
        'groq': {
            'name': 'Groq',
            'key_env': 'GROQ_API_KEY',
            'litellm_prefix': 'groq/',
            'default_model': 'llama-3.3-70b-versatile',
            'models': [
                {'id': 'llama-3.3-70b-versatile', 'name': 'Llama 3.3 70B'},
                {'id': 'mixtral-8x7b-32768', 'name': 'Mixtral 8x7B'},
            ]
        },
        'ollama': {
            'name': 'Ollama (Local)',
            'key_env': None,  # No API key needed
            'litellm_prefix': 'ollama/',
            'default_model': 'llama3',
            'models': []  # Fetched dynamically
        }
    }
    
    def __init__(self):
        self._prism_dir = Path.home() / '.prism'
        self._config_path = self._prism_dir / 'llm_config.json'
        self._key_path = self._prism_dir / '.llm_key'
        self._config = {}
        self._fernet = None
        
        self._ensure_dirs()
        self._init_encryption()
        self._load_config()
    
    # ... full implementation
```

### Checklist

- [x] Create `core/llm_config.py` file
- [x] Implement `__init__` with directory/encryption setup
- [x] Implement `_ensure_dirs()` - create ~/.prism if needed
- [x] Implement `_init_encryption()` - create/load Fernet key
- [x] Implement `_load_config()` - load JSON config
- [x] Implement `_save_config()` - persist JSON config
- [x] Implement `_encrypt_key(api_key)` - encrypt with Fernet
- [x] Implement `_decrypt_key(encrypted)` - decrypt with Fernet
- [x] Implement `get_providers_status()` - list all providers with hasKey status
- [x] Implement `has_api_key(provider_id)` - check if key exists (config or env)
- [x] Implement `get_api_key(provider_id)` - get decrypted key (config or env fallback)
- [x] Implement `set_api_key(provider_id, api_key)` - encrypt and store
- [x] Implement `delete_api_key(provider_id)` - remove from config
- [x] Implement `validate_api_key(provider_id, api_key)` - test with real API call
- [x] Implement `fetch_models(provider_id)` - get models from provider API
- [x] Implement `get_active_config()` - return {model, litellm_params} for Agent
- [x] Implement `set_active_model(provider_id, model_id)` - set active selection
- [x] Implement `get_ollama_url()` and `set_ollama_url(url)`
- [x] Implement `test_ollama_connection(url)` - verify Ollama is running
- [x] Add `LLMConfigManager` to `core/__init__.py` exports
- [ ] Write basic unit tests

---

## Phase 2: Backend API Routes

### Focus Files
```
run_web.py                 # MODIFY - Add /api/llm/* routes
core/llm_config.py         # Reference for handlers
```

### API Endpoints

#### GET `/api/llm/providers`
Returns all providers with their status and current selection.

**Response:**
```json
{
  "providers": [
    {
      "id": "anthropic",
      "name": "Anthropic", 
      "hasKey": true,
      "isActive": true,
      "models": [
        {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
        {"id": "claude-opus-4-20250514", "name": "Claude Opus 4"}
      ]
    },
    {
      "id": "openai",
      "name": "OpenAI",
      "hasKey": false,
      "isActive": false,
      "models": []
    }
  ],
  "active": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-20250514"
  },
  "ollama_url": "http://localhost:11434"
}
```

#### POST `/api/llm/key`
Save an API key for a provider.

**Request:**
```json
{
  "provider_id": "openai",
  "api_key": "sk-proj-..."
}
```

**Response:**
```json
{
  "success": true,
  "models": [...]  // Fetched models if validation succeeded
}
```

#### DELETE `/api/llm/key/<provider_id>`
Remove an API key.

**Response:**
```json
{"success": true}
```

#### POST `/api/llm/validate`
Test an API key without saving.

**Request:**
```json
{
  "provider_id": "openai", 
  "api_key": "sk-proj-..."
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Key validated successfully",
  "models": [...]  // Available models
}
```
or
```json
{
  "valid": false,
  "error": "Invalid API key"
}
```

#### GET `/api/llm/models/<provider_id>`
Fetch available models for a provider.

**Response:**
```json
{
  "models": [
    {"id": "gpt-4o", "name": "GPT-4o", "context_window": 128000},
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context_window": 128000}
  ]
}
```

#### POST `/api/llm/active`
Set the active provider and model.

**Request:**
```json
{
  "provider_id": "anthropic",
  "model_id": "claude-sonnet-4-20250514"
}
```

**Response:**
```json
{"success": true}
```

#### POST `/api/llm/ollama/test`
Test Ollama connection.

**Request:**
```json
{"url": "http://localhost:11434"}
```

**Response:**
```json
{
  "success": true,
  "models": ["llama3", "codellama", "mistral"]
}
```

### Checklist

- [x] Import `LLMConfigManager` in `run_web.py`
- [x] Create global `_llm_config = LLMConfigManager()` instance
- [x] Add `GET /api/llm/providers` route
- [x] Add `POST /api/llm/key` route
- [x] Add `DELETE /api/llm/key/<provider_id>` route
- [x] Add `POST /api/llm/validate` route
- [x] Add `GET /api/llm/models/<provider_id>` route
- [x] Add `POST /api/llm/active` route
- [x] Add `POST /api/llm/ollama/test` route
- [x] Add `POST /api/llm/ollama/url` route (save Ollama URL)
- [x] Add error handling for all routes (try/except with proper JSON errors)
- [ ] Test each route with curl/Postman

---

## Phase 3: Connect Config to Agent

### Focus Files
```
config.py                  # MODIFY - Use LLMConfigManager
core/agent.py              # REVIEW - Ensure it uses config correctly
```

### Changes to `config.py`

```python
# Before:
def _get_reliable_model_config():
    return {
        "model": "anthropic/claude-opus-4-5-20251101",
        "litellm_params": {...}
    }

# After:
from core.llm_config import LLMConfigManager

_llm_config = LLMConfigManager()

def _get_reliable_model_config():
    """Get model config from LLMConfigManager with env var fallback."""
    # Try user-configured model first
    config = _llm_config.get_active_config()
    if config:
        return config
    
    # Fallback to environment variables
    if os.getenv('ANTHROPIC_API_KEY'):
        return {
            "model": "anthropic/claude-sonnet-4-20250514",
            "litellm_params": {"timeout": 120}
        }
    if os.getenv('OPENAI_API_KEY'):
        return {
            "model": "openai/gpt-4o",
            "litellm_params": {"timeout": 120}
        }
    # ... other fallbacks
    
    # Ultimate fallback
    return {
        "model": "anthropic/claude-sonnet-4-20250514",
        "litellm_params": {"timeout": 120}
    }

def get_llm_config_manager():
    """Get the LLM config manager instance (for API routes)."""
    return _llm_config
```

### Checklist

- [x] Modify `config.py` to import and use `LLMConfigManager`
- [x] Update `_get_reliable_model_config()` to check user config first
- [x] Add `get_llm_config_manager()` helper for routes to access
- [x] Ensure environment variable fallback still works
- [ ] Test that changing model in config affects new Agent instances
- [ ] Verify existing sessions keep their original model (don't change mid-conversation)

---

## Phase 4: Frontend - LLM Settings Pane

### Focus Files
```
static/workspace/js/components/preferences/llm-pane.js   # REWRITE
static/workspace/css/components/preferences.css          # ADD styles
```

### UI Design

```
┌─────────────────────────────────────────────────────────────┐
│ ACTIVE MODEL                                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ◉ Anthropic                                             │ │
│ │   claude-sonnet-4-20250514                    [Change]  │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ API KEYS                                                    │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ✓ Anthropic                              [Configured ▾] │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ○ OpenAI                                    [Add Key]   │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ○ Google                                    [Add Key]   │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ ○ Groq                                      [Add Key]   │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ LOCAL MODELS (Ollama)                                       │
│                                                             │
│ Server URL: [http://localhost:11434        ] [Test]         │
│                                                             │
│ Status: ✓ Connected - 3 models available                    │
│ Models: llama3, codellama, mistral                          │
└─────────────────────────────────────────────────────────────┘
```

**Key Configuration Expanded State:**

```
┌─────────────────────────────────────────────────────────────┐
│ ○ OpenAI                                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ API Key:                                                │ │
│ │ [sk-proj-abc123...                              ] 👁    │ │
│ │                                                         │ │
│ │ Status: ● Validating...                                 │ │
│ │         ✓ Valid - 15 models available                   │ │
│ │         ✗ Invalid API key                               │ │
│ │                                                         │ │
│ │ [Cancel]                      [Save Key & Set Active]   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component State

```javascript
{
  // From API
  providers: [
    { id: 'anthropic', name: 'Anthropic', hasKey: true, models: [...] },
    { id: 'openai', name: 'OpenAI', hasKey: false, models: [] },
    ...
  ],
  activeProvider: 'anthropic',
  activeModel: 'claude-sonnet-4-20250514',
  ollamaUrl: 'http://localhost:11434',
  ollamaModels: [],
  ollamaConnected: false,
  
  // UI state
  expandedProvider: null,      // Which provider's config is expanded
  keyInput: '',                // Current key being entered
  keyVisible: false,           // Show/hide key toggle
  validationState: 'idle',     // 'idle' | 'validating' | 'valid' | 'invalid'
  validationError: null,
  validatedModels: [],         // Models returned from validation
  saving: false
}
```

### Checklist

- [x] Rewrite `llm-pane.js` with new state structure
- [x] Implement `load()` - fetch from `/api/llm/providers`
- [x] Implement `render()` - full UI with all sections
- [x] Implement active model display section
- [x] Implement provider list with hasKey status indicators
- [x] Implement expand/collapse for provider key config
- [x] Implement key input with show/hide toggle
- [x] Implement "Validate" button with loading spinner
- [x] Implement validation status display (validating/valid/invalid)
- [x] Implement "Save Key" flow
- [x] Implement "Set as Active" functionality  
- [x] Implement model selection dropdown (when key is valid)
- [x] Implement Ollama URL configuration
- [x] Implement Ollama "Test Connection" button
- [x] Implement Ollama models display
- [x] Add CSS for validation states (.validating, .valid, .invalid)
- [x] Add CSS for expanded provider card
- [x] Add loading spinners
- [x] Add error message styling
- [ ] Test all user flows

---

## Phase 5: Security Review

### Focus Files
```
core/llm_config.py         # Review encryption implementation
```

### Security Checklist

- [ ] API keys encrypted with Fernet (AES-128-CBC)
- [ ] Encryption key stored in separate file (`~/.prism/.llm_key`)
- [ ] Encryption key file has restricted permissions (600)
- [ ] API keys never logged (check all print/logging statements)
- [ ] API keys never included in error messages
- [ ] Keys not stored in browser localStorage/sessionStorage
- [ ] Keys only sent over the wire to the LLM provider (not to any other service)
- [ ] Validate that decryption failure is handled gracefully
- [ ] Test that corrupted config file doesn't crash the app

---

## Phase 6: Testing & Polish

### Test Cases

**Key Management:**
- [ ] Add new API key for provider without existing key
- [ ] Replace existing API key
- [ ] Delete API key
- [ ] Key persists across server restart
- [ ] Invalid key rejected with helpful error message
- [ ] Key with wrong format rejected (e.g., OpenAI key for Anthropic)

**Model Selection:**
- [ ] Change active model for current provider
- [ ] Switch to different provider
- [ ] New conversations use new model
- [ ] Existing conversations keep their model (verify in history)

**Ollama:**
- [ ] Test connection to running Ollama
- [ ] Test connection to non-running Ollama (graceful error)
- [ ] Fetch models from Ollama
- [ ] Use Ollama model for conversation

**Fallbacks:**
- [ ] Environment variable works when no config set
- [ ] Config takes precedence over environment variable
- [ ] Missing encryption key is regenerated
- [ ] Corrupted config file is reset gracefully

**UI Polish:**
- [ ] Loading states shown during API calls
- [ ] Error messages are user-friendly
- [ ] Success feedback is clear
- [ ] Keyboard navigation works (Enter to submit, Escape to cancel)

---

## Dependencies

Add to `requirements.txt`:
```
cryptography>=41.0.0
```

The `cryptography` package provides Fernet encryption for secure API key storage.

---

## File Change Summary

| File | Action | Lines (est.) | Description |
|------|--------|--------------|-------------|
| `core/llm_config.py` | CREATE | ~350 | LLM config manager with encryption |
| `core/__init__.py` | MODIFY | +2 | Add export |
| `config.py` | MODIFY | +30, -10 | Use LLMConfigManager |
| `run_web.py` | MODIFY | +120 | Add 7 API routes |
| `static/workspace/js/components/preferences/llm-pane.js` | REWRITE | ~400 | Full settings UI |
| `static/workspace/css/components/preferences.css` | MODIFY | +80 | Validation styles |
| `requirements.txt` | MODIFY | +1 | Add cryptography |

**Total: ~6 files, ~600 lines of new code**

---

## Execution Order

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6
   │           │           │           │           │           │
   ▼           ▼           ▼           ▼           ▼           ▼
Backend     API        Connect      Frontend   Security   Testing
Core        Routes     to Agent     UI         Review     & Polish
```

Each phase should be completed and tested before moving to the next.

---

## Note: Rename Mobius → Prism

**Status: Already Complete** ✓

The codebase already uses "Prism" naming:
- `PrismChat`, `PrismComponent`, `PrismPreferences` (JS classes)
- `prism-chat`, `prism-preferences` (custom elements)
- Assistant label shows "Prism" not "Mobius"
- Comments say "Prism Workspace"

No rename work needed.
