"""
Configuration constants for Prism.
"""
import os
from pathlib import Path
from tools import read_file, create_file, edit_file, rename_file, delete_file, ls, focus, unfocus, list_focused, bash
from tools import (
    find_entry_points,
    get_dependency_info,
    macro_focus,
    add_entry_point,
    remove_entry_point,
    list_entry_points,
    trace_entry_point,
    rescan_project,
)

# Load CLAUDE.md for system prompt context
def _load_claude_md() -> str:
    """Load CLAUDE.md if it exists in the current directory."""
    claude_path = Path.cwd() / "CLAUDE.md"
    if claude_path.exists():
        try:
            return claude_path.read_text()
        except Exception:
            pass
    return ""

# Language mapping for syntax highlighting
LANG_MAP = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "md": "markdown",
    "json": "json",
    "yml": "yaml",
    "yaml": "yaml",
    "sh": "bash",
    "rs": "rust",
    "go": "go",
    "rb": "ruby",
}

# Base system prompt
_BASE_PROMPT = "You are a helpful coding assistant. Use tools to read, create, edit, and navigate files. Be concise."

# Build full system prompt with CLAUDE.md context
def _build_system_prompt() -> str:
    """Build system prompt, including CLAUDE.md if present."""
    claude_md = _load_claude_md()
    if claude_md:
        return f"{_BASE_PROMPT}\n\n# Project Documentation\n\n{claude_md}"
    return _BASE_PROMPT

def _get_reliable_model_config():
    """
    Determine the best model configuration based on available credentials.
    
    Priority:
    1. User-configured model from LLMConfigManager (Settings UI)
    2. Environment variable fallback (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
    3. Default to Anthropic Claude if nothing else configured
    
    NOTE: This is called dynamically each time an Agent is created, so changes
    to the active model in settings will apply immediately.
    """
    # Try user-configured model first (from Settings UI)
    try:
        from core.llm_config import get_llm_config
        llm_config = get_llm_config()
        config = llm_config.get_active_config()
        if config:
            # Merge with our standard timeout settings
            litellm_params = config.get('litellm_params', {})
            litellm_params.setdefault('timeout', 900)
            litellm_params.setdefault('stream_timeout', 60)
            return {
                "model": config['model'],
                "litellm_params": litellm_params
            }
    except Exception as e:
        # If LLMConfigManager fails, fall through to env var detection
        print(f"Note: LLMConfigManager not available ({e}), using env var fallback")
    
    # Fallback: detect from environment variables
    if os.getenv('ANTHROPIC_API_KEY'):
        return {
            "model": "anthropic/claude-sonnet-4-20250514",
            "litellm_params": {"timeout": 900, "stream_timeout": 60}
        }
    if os.getenv('OPENAI_API_KEY'):
        return {
            "model": "openai/gpt-4o",
            "litellm_params": {"timeout": 900, "stream_timeout": 60}
        }
    if os.getenv('GEMINI_API_KEY'):
        return {
            "model": "gemini/gemini-2.0-flash",
            "litellm_params": {"timeout": 900, "stream_timeout": 60}
        }
    if os.getenv('GROQ_API_KEY'):
        return {
            "model": "groq/llama-3.3-70b-versatile",
            "litellm_params": {"timeout": 900, "stream_timeout": 60}
        }
    
    # Ultimate fallback - assume Anthropic (will fail if no key, but that's expected)
    return {
        "model": "anthropic/claude-sonnet-4-20250514",
        "litellm_params": {"timeout": 900, "stream_timeout": 60}
    }

# Don't cache the config - call the function each time to get fresh config
def get_agent_config():
    """
    Get agent configuration with current model settings.
    Called dynamically each time an Agent is created to pick up config changes.
    """
    model_config = _get_reliable_model_config()
    
    return {
        "system_prompt": _build_system_prompt(),
        "tools": [
            # File operations
            read_file, create_file, edit_file, rename_file, delete_file, ls,
            # Focus management
            focus, unfocus, list_focused,
            # Shell
            bash,
            # Prism dependency tools
            find_entry_points,
            get_dependency_info,
            macro_focus,
            add_entry_point,
            remove_entry_point,
            list_entry_points,
            trace_entry_point,
            rescan_project,
        ],
        # Configuration derived from current settings (dynamic)
        "model": model_config["model"],
        "litellm_params": model_config["litellm_params"]
    }

# For backwards compatibility - but this will be stale if config changes!
# Use get_agent_config() instead for fresh config
# Note: Lazy evaluation to avoid import-time errors with misconfigured env vars
AGENT_CONFIG = None

def _get_agent_config_cached():
    """Lazy initialization of AGENT_CONFIG."""
    global AGENT_CONFIG
    if AGENT_CONFIG is None:
        try:
            AGENT_CONFIG = get_agent_config()
        except Exception as e:
            # Return minimal config if LLM setup fails (user can configure from UI)
            print(f"Warning: LLM config failed ({e}), using placeholder until configured")
            AGENT_CONFIG = {
                "system_prompt": _BASE_PROMPT,
                "tools": [],
                "model": "anthropic/claude-sonnet-4-20250514",
                "litellm_params": {"timeout": 900}
            }
    return AGENT_CONFIG

# Slash command definitions
SLASH_COMMANDS = [
    ("/session", "Show current session info"),
    ("/sessions", "List recent sessions"),
    ("/session new", "Start a new session"),
    ("/session <id>", "Load a previous session"),
    ("/theme <name>", "Change theme"),
    ("/themes", "List all available themes"),
    ("/toggle-diff", "Toggle detailed diff display"),
    ("/help", "Show help"),
]
