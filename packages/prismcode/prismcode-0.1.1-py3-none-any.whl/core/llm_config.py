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
import stat
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

try:
    from cryptography.fernet import Fernet, InvalidToken
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    Fernet = None
    InvalidToken = Exception

import litellm


class LLMConfigManager:
    """Manages LLM provider configuration with secure key storage."""
    
    PROVIDERS = {
        'anthropic': {
            'name': 'Anthropic',
            'key_env': 'ANTHROPIC_API_KEY',
            'litellm_prefix': 'anthropic/',
            'default_model': 'claude-sonnet-4-20250514',
            'models': [
                {'id': 'claude-sonnet-4-20250514', 'name': 'Claude Sonnet 4'},
                {'id': 'claude-opus-4-20250514', 'name': 'Claude Opus 4'},
                {'id': 'claude-3-5-haiku-20241022', 'name': 'Claude 3.5 Haiku'},
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
                {'id': 'o1', 'name': 'o1'},
                {'id': 'o1-mini', 'name': 'o1 Mini'},
            ]
        },
        'google': {
            'name': 'Google (Gemini)',
            'key_env': 'GEMINI_API_KEY',
            'litellm_prefix': 'gemini/',
            'default_model': 'gemini-2.0-flash',
            'models': [
                {'id': 'gemini-2.0-flash', 'name': 'Gemini 2.0 Flash'},
                {'id': 'gemini-2.0-flash-thinking-exp', 'name': 'Gemini 2.0 Flash Thinking'},
                {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro'},
                {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash'},
            ]
        },
        'groq': {
            'name': 'Groq',
            'key_env': 'GROQ_API_KEY',
            'litellm_prefix': 'groq/',
            'default_model': 'llama-3.3-70b-versatile',
            'models': [
                {'id': 'llama-3.3-70b-versatile', 'name': 'Llama 3.3 70B'},
                {'id': 'llama-3.1-8b-instant', 'name': 'Llama 3.1 8B Instant'},
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
        self._config: Dict[str, Any] = {}
        self._fernet: Optional[Fernet] = None
        
        self._ensure_dirs()
        self._init_encryption()
        self._load_config()
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def _ensure_dirs(self) -> None:
        """Create ~/.prism directory if it doesn't exist."""
        self._prism_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_encryption(self) -> None:
        """Initialize Fernet encryption. Creates key file if missing."""
        if not HAS_CRYPTO:
            # cryptography not installed - keys will be stored in plaintext
            # with a warning
            return
        
        if self._key_path.exists():
            # Load existing key
            try:
                key = self._key_path.read_bytes()
                self._fernet = Fernet(key)
            except Exception as e:
                print(f"Warning: Failed to load encryption key: {e}")
                self._fernet = None
        else:
            # Generate new key
            try:
                key = Fernet.generate_key()
                self._key_path.write_bytes(key)
                # Restrict permissions to owner only (600)
                self._key_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
                self._fernet = Fernet(key)
            except Exception as e:
                print(f"Warning: Failed to create encryption key: {e}")
                self._fernet = None
    
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        if self._config_path.exists():
            try:
                self._config = json.loads(self._config_path.read_text())
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load LLM config: {e}")
                self._config = {}
        else:
            self._config = {}
    
    def _save_config(self) -> None:
        """Save configuration to JSON file."""
        try:
            self._config_path.write_text(json.dumps(self._config, indent=2))
        except IOError as e:
            print(f"Warning: Failed to save LLM config: {e}")
    
    # -------------------------------------------------------------------------
    # Encryption helpers
    # -------------------------------------------------------------------------
    
    def _encrypt_key(self, api_key: str) -> str:
        """Encrypt an API key. Returns plaintext if encryption unavailable."""
        if self._fernet:
            try:
                return self._fernet.encrypt(api_key.encode()).decode()
            except Exception:
                pass
        # Fallback: base64 encode (NOT secure, just obfuscation)
        import base64
        return "b64:" + base64.b64encode(api_key.encode()).decode()
    
    def _decrypt_key(self, encrypted: str) -> Optional[str]:
        """Decrypt an API key. Returns None if decryption fails."""
        if not encrypted:
            return None
        
        # Handle base64 fallback
        if encrypted.startswith("b64:"):
            import base64
            try:
                return base64.b64decode(encrypted[4:]).decode()
            except Exception:
                return None
        
        # Fernet decryption
        if self._fernet:
            try:
                return self._fernet.decrypt(encrypted.encode()).decode()
            except InvalidToken:
                return None
            except Exception:
                return None
        
        return None
    
    # -------------------------------------------------------------------------
    # API Key Management
    # -------------------------------------------------------------------------
    
    def has_api_key(self, provider_id: str) -> bool:
        """Check if an API key exists for a provider (config or env var)."""
        # Check config first
        if self._config.get('keys', {}).get(provider_id):
            return True
        
        # Check environment variable
        provider = self.PROVIDERS.get(provider_id)
        if provider and provider.get('key_env'):
            return bool(os.getenv(provider['key_env']))
        
        # Ollama doesn't need a key
        if provider_id == 'ollama':
            return True
        
        return False
    
    def get_api_key(self, provider_id: str) -> Optional[str]:
        """Get decrypted API key for a provider. Checks config then env var."""
        # Check config first
        encrypted = self._config.get('keys', {}).get(provider_id)
        if encrypted:
            decrypted = self._decrypt_key(encrypted)
            if decrypted:
                return decrypted
        
        # Fallback to environment variable
        provider = self.PROVIDERS.get(provider_id)
        if provider and provider.get('key_env'):
            return os.getenv(provider['key_env'])
        
        return None
    
    def set_api_key(self, provider_id: str, api_key: str) -> bool:
        """Encrypt and store an API key for a provider."""
        if provider_id not in self.PROVIDERS:
            return False
        
        if 'keys' not in self._config:
            self._config['keys'] = {}
        
        self._config['keys'][provider_id] = self._encrypt_key(api_key)
        self._save_config()
        return True
    
    def delete_api_key(self, provider_id: str) -> bool:
        """Remove an API key for a provider."""
        if 'keys' in self._config and provider_id in self._config['keys']:
            del self._config['keys'][provider_id]
            self._save_config()
            return True
        return False
    
    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------
    
    def validate_api_key(self, provider_id: str, api_key: str) -> Tuple[bool, str]:
        """
        Validate an API key by making a test API call.
        Returns (success, message).
        """
        provider = self.PROVIDERS.get(provider_id)
        if not provider:
            return False, f"Unknown provider: {provider_id}"
        
        if provider_id == 'ollama':
            # Ollama doesn't use API keys
            return True, "Ollama does not require an API key"
        
        # Set the API key temporarily in environment for LiteLLM
        env_var = provider.get('key_env')
        if not env_var:
            return False, "Provider does not support API keys"
        
        old_value = os.environ.get(env_var)
        try:
            os.environ[env_var] = api_key
            
            # Make a minimal API call to validate
            model = provider['litellm_prefix'] + provider['default_model']
            
            # Use a minimal completion request
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
                timeout=10
            )
            
            return True, "API key validated successfully"
            
        except litellm.AuthenticationError:
            return False, "Invalid API key"
        except litellm.RateLimitError:
            # Rate limited means the key is valid!
            return True, "API key valid (rate limited)"
        except litellm.APIConnectionError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            error_msg = str(e).lower()
            if 'invalid' in error_msg or 'auth' in error_msg or 'key' in error_msg:
                return False, "Invalid API key"
            return False, f"Validation error: {str(e)}"
        finally:
            # Restore original env var
            if old_value is not None:
                os.environ[env_var] = old_value
            elif env_var in os.environ:
                del os.environ[env_var]
    
    # -------------------------------------------------------------------------
    # Model Fetching
    # -------------------------------------------------------------------------
    
    def fetch_models(self, provider_id: str) -> List[Dict[str, Any]]:
        """
        Fetch available models for a provider.
        Returns list of {id, name} dicts.
        Falls back to static list if API fails.
        """
        provider = self.PROVIDERS.get(provider_id)
        if not provider:
            return []
        
        # For Ollama, fetch from local server
        if provider_id == 'ollama':
            return self._fetch_ollama_models()
        
        # For other providers, try to fetch dynamically
        try:
            if provider_id == 'anthropic':
                return self._fetch_anthropic_models()
            elif provider_id == 'openai':
                return self._fetch_openai_models()
            elif provider_id == 'google':
                return self._fetch_google_models()
            elif provider_id == 'groq':
                return self._fetch_groq_models()
        except Exception as e:
            print(f"Failed to fetch models for {provider_id}: {e}")
        
        # Fallback to static list if dynamic fetch fails
        return provider.get('models', [])
    
    def _fetch_ollama_models(self) -> List[Dict[str, Any]]:
        """Fetch models from local Ollama server."""
        import urllib.request
        import urllib.error
        
        url = self.get_ollama_url()
        try:
            req = urllib.request.Request(f"{url}/api/tags", method='GET')
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = data.get('models', [])
                return [
                    {'id': m['name'], 'name': m['name']}
                    for m in models
                ]
        except Exception:
            return []

    def _fetch_anthropic_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from Anthropic API."""
        api_key = self.get_api_key('anthropic')
        if not api_key:
            return []
        
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(
                'https://api.anthropic.com/v1/models',
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                models = []
                for model in data.get('data', []):
                    # Filter to only include Claude models that are available
                    if model.get('id', '').startswith('claude-'):
                        models.append({
                            'id': model['id'],
                            'name': model.get('display_name', model['id']),
                            'context_window': model.get('max_tokens', None)
                        })
                
                # Sort by name, put newer models first
                models.sort(key=lambda x: x['id'], reverse=True)
                return models
                
        except Exception as e:
            print(f"Failed to fetch Anthropic models: {e}")
            return []

    def _fetch_openai_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from OpenAI API."""
        api_key = self.get_api_key('openai')
        if not api_key:
            return []
        
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(
                'https://api.openai.com/v1/models',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                models = []
                
                # Filter to only include chat completion models
                chat_models = []
                for model in data.get('data', []):
                    model_id = model.get('id', '')
                    # Include GPT models and o1 models
                    if (model_id.startswith('gpt-') or 
                        model_id.startswith('o1') or 
                        model_id.startswith('chatgpt')):
                        
                        # Clean up the name
                        name = model_id
                        if model_id.startswith('gpt-4o'):
                            name = model_id.replace('gpt-4o', 'GPT-4o').replace('-', ' ').title()
                        elif model_id.startswith('gpt-4'):
                            name = model_id.replace('gpt-4', 'GPT-4').replace('-', ' ').title()
                        elif model_id.startswith('gpt-3.5'):
                            name = model_id.replace('gpt-3.5', 'GPT-3.5').replace('-', ' ').title()
                        elif model_id.startswith('o1'):
                            name = model_id.replace('o1', 'o1').replace('-', ' ').title()
                        
                        models.append({
                            'id': model_id,
                            'name': name,
                            'created': model.get('created', 0)
                        })
                
                # Sort by creation date (newer first)
                models.sort(key=lambda x: x.get('created', 0), reverse=True)
                
                return models[:20]  # Limit to top 20 models
                
        except Exception as e:
            print(f"Failed to fetch OpenAI models: {e}")
            return []

    def _fetch_google_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from Google Gemini API."""
        api_key = self.get_api_key('google')
        if not api_key:
            return []
        
        try:
            import urllib.request
            import urllib.error
            
            # Use the list models API
            req = urllib.request.Request(
                f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}',
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                models = []
                
                for model in data.get('models', []):
                    model_name = model.get('name', '')
                    if 'models/' in model_name:
                        model_id = model_name.split('models/')[-1]
                        
                        # Only include Gemini models that support generateContent
                        supported_methods = model.get('supportedGenerationMethods', [])
                        if 'generateContent' in supported_methods:
                            # Clean up display name
                            display_name = model.get('displayName', model_id)
                            if display_name.startswith('Gemini '):
                                display_name = display_name.replace('Gemini ', 'Gemini ')
                            
                            models.append({
                                'id': model_id,
                                'name': display_name,
                                'description': model.get('description', '')
                            })
                
                # Sort to put newer models first
                models.sort(key=lambda x: x['id'], reverse=True)
                return models
                
        except Exception as e:
            print(f"Failed to fetch Google models: {e}")
            return []

    def _fetch_groq_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from Groq API."""
        api_key = self.get_api_key('groq')
        if not api_key:
            return []
        
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(
                'https://api.groq.com/openai/v1/models',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                models = []
                
                for model in data.get('data', []):
                    model_id = model.get('id', '')
                    
                    # Clean up the display name
                    name = model_id
                    if 'llama' in model_id.lower():
                        name = model_id.replace('llama-', 'Llama ').replace('llama3', 'Llama 3').title()
                    elif 'mixtral' in model_id.lower():
                        name = model_id.replace('mixtral-', 'Mixtral ').title()
                    elif 'gemma' in model_id.lower():
                        name = model_id.replace('gemma-', 'Gemma ').title()
                    
                    models.append({
                        'id': model_id,
                        'name': name,
                        'created': model.get('created', 0)
                    })
                
                # Sort by creation date (newer first)
                models.sort(key=lambda x: x.get('created', 0), reverse=True)
                return models
                
        except Exception as e:
            print(f"Failed to fetch Groq models: {e}")
            return []
    
    # -------------------------------------------------------------------------
    # Active Model Selection
    # -------------------------------------------------------------------------
    
    def get_active_provider(self) -> Optional[str]:
        """Get the currently active provider ID."""
        return self._config.get('active_provider')
    
    def get_active_model(self) -> Optional[str]:
        """Get the currently active model ID."""
        return self._config.get('active_model')
    
    def set_active_model(self, provider_id: str, model_id: str) -> bool:
        """Set the active provider and model."""
        if provider_id not in self.PROVIDERS:
            return False
        
        self._config['active_provider'] = provider_id
        self._config['active_model'] = model_id
        self._save_config()
        return True
    
    def get_active_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the full configuration for the active model.
        Returns {model, litellm_params} or None if not configured.
        """
        provider_id = self.get_active_provider()
        model_id = self.get_active_model()
        
        if not provider_id or not model_id:
            return None
        
        provider = self.PROVIDERS.get(provider_id)
        if not provider:
            return None
        
        # Check we have an API key (or it's Ollama)
        if provider_id != 'ollama' and not self.has_api_key(provider_id):
            return None
        
        # Build the full model string for LiteLLM
        full_model = provider['litellm_prefix'] + model_id
        
        # Build litellm_params
        litellm_params = {
            'timeout': 120,
        }
        
        # For Ollama, add base URL
        if provider_id == 'ollama':
            litellm_params['api_base'] = self.get_ollama_url()
        
        # Set the API key in environment if we have one from config
        api_key = self.get_api_key(provider_id)
        if api_key and provider.get('key_env'):
            os.environ[provider['key_env']] = api_key
        
        return {
            'model': full_model,
            'litellm_params': litellm_params
        }
    
    # -------------------------------------------------------------------------
    # Ollama Configuration
    # -------------------------------------------------------------------------
    
    def get_ollama_url(self) -> str:
        """Get the Ollama server URL."""
        return self._config.get('ollama_url', 'http://localhost:11434')
    
    def set_ollama_url(self, url: str) -> None:
        """Set the Ollama server URL."""
        self._config['ollama_url'] = url.rstrip('/')
        self._save_config()
    
    def test_ollama_connection(self, url: Optional[str] = None) -> Tuple[bool, str, List[str]]:
        """
        Test connection to Ollama server.
        Returns (success, message, list of model names).
        """
        import urllib.request
        import urllib.error
        
        test_url = url or self.get_ollama_url()
        try:
            req = urllib.request.Request(f"{test_url}/api/tags", method='GET')
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = [m['name'] for m in data.get('models', [])]
                return True, f"Connected - {len(models)} models available", models
        except urllib.error.URLError as e:
            return False, f"Connection failed: {e.reason}", []
        except Exception as e:
            return False, f"Error: {str(e)}", []
    
    # -------------------------------------------------------------------------
    # Provider Status (for UI)
    # -------------------------------------------------------------------------
    
    def get_providers_status(self, fetch_models: bool = False) -> List[Dict[str, Any]]:
        """
        Get status of all providers for the settings UI.
        Returns list of provider info with hasKey, isActive, models.
        
        Args:
            fetch_models: If True, fetch models from API (slow). If False, use static fallback (fast).
        """
        active_provider = self.get_active_provider()
        active_model = self.get_active_model()
        
        result = []
        for provider_id, provider in self.PROVIDERS.items():
            has_key = self.has_api_key(provider_id)
            
            # Only fetch models if explicitly requested AND we have a key
            # Otherwise use static fallback for fast initial load
            if fetch_models and has_key:
                try:
                    models = self.fetch_models(provider_id)
                    # If fetch returned nothing, fallback to static list
                    if not models:
                        models = provider.get('models', [])
                except Exception:
                    models = provider.get('models', [])
            else:
                # Use static fallback for fast load
                models = provider.get('models', [])
            
            result.append({
                'id': provider_id,
                'name': provider['name'],
                'hasKey': has_key,
                'isActive': provider_id == active_provider,
                'models': models,
                'activeModel': active_model if provider_id == active_provider else None,
                'keyEnv': provider.get('key_env'),
                'isLocal': provider_id == 'ollama'
            })
        
        return result
    
    def get_full_status(self, fetch_models: bool = False) -> Dict[str, Any]:
        """
        Get full status including providers and active selection.
        
        Args:
            fetch_models: If True, fetch models from API (slow). Default False for fast load.
        """
        return {
            'providers': self.get_providers_status(fetch_models=fetch_models),
            'active': {
                'provider': self.get_active_provider(),
                'model': self.get_active_model()
            },
            'ollama_url': self.get_ollama_url()
        }


# Singleton instance for easy access
_instance: Optional[LLMConfigManager] = None

def get_llm_config() -> LLMConfigManager:
    """Get the global LLMConfigManager instance."""
    global _instance
    if _instance is None:
        _instance = LLMConfigManager()
    return _instance
