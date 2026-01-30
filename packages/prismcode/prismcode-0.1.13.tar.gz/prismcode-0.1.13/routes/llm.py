"""
LLM configuration routes.
"""
import os
from flask import Blueprint, request, jsonify

from core.llm_config import get_llm_config
from .shared import active_agents, refresh_active_agents

llm_bp = Blueprint('llm', __name__)

# Reference to socketio - will be set by run_web.py
_socketio = None

def set_socketio(socketio):
    """Set the SocketIO instance for broadcasting."""
    global _socketio
    _socketio = socketio


@llm_bp.route('/api/llm/providers')
def api_llm_providers():
    """Get all LLM providers with their status and current selection."""
    try:
        fetch_models = request.args.get('fetch_models') == '1'
        llm_config = get_llm_config()
        return jsonify(llm_config.get_full_status(fetch_models=fetch_models))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/key', methods=['POST'])
def api_llm_set_key():
    """Save an API key for a provider."""
    try:
        data = request.json
        provider_id = data.get('provider_id')
        api_key = data.get('api_key', '').strip()

        if not provider_id:
            return jsonify({"error": "provider_id is required"}), 400
        if not api_key:
            return jsonify({"error": "api_key is required"}), 400

        llm_config = get_llm_config()

        valid, message = llm_config.validate_api_key(provider_id, api_key)
        if not valid:
            return jsonify({"success": False, "error": message}), 400

        if llm_config.set_api_key(provider_id, api_key):
            models = llm_config.fetch_models(provider_id)
            if _socketio:
                _socketio.emit('provider_models_updated', {
                    'provider_id': provider_id,
                    'models': models
                })
            return jsonify({
                "success": True,
                "message": message,
                "models": models
            })
        else:
            return jsonify({"success": False, "error": "Failed to save key"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/key/<provider_id>', methods=['DELETE'])
def api_llm_delete_key(provider_id):
    """Remove an API key for a provider."""
    try:
        llm_config = get_llm_config()

        if llm_config.delete_api_key(provider_id):
            if _socketio:
                _socketio.emit('provider_models_updated', {
                    'provider_id': provider_id,
                    'models': []
                })
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Key not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/validate', methods=['POST'])
def api_llm_validate():
    """Validate an API key without saving."""
    try:
        data = request.json
        provider_id = data.get('provider_id')
        api_key = data.get('api_key', '').strip()

        if not provider_id:
            return jsonify({"error": "provider_id is required"}), 400
        if not api_key:
            return jsonify({"error": "api_key is required"}), 400

        llm_config = get_llm_config()
        valid, message = llm_config.validate_api_key(provider_id, api_key)

        if valid:
            old_key = llm_config.get_api_key(provider_id)
            env_var = llm_config.PROVIDERS.get(provider_id, {}).get('key_env')
            old_env_value = os.environ.get(env_var) if env_var else None

            if env_var:
                os.environ[env_var] = api_key

            try:
                models = llm_config.fetch_models(provider_id)
            finally:
                if env_var:
                    if old_env_value is not None:
                        os.environ[env_var] = old_env_value
                    elif env_var in os.environ:
                        del os.environ[env_var]

            return jsonify({
                "valid": True,
                "message": message,
                "models": models
            })
        else:
            return jsonify({
                "valid": False,
                "error": message
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/models/<provider_id>')
def api_llm_models(provider_id):
    """Fetch available models for a provider."""
    try:
        llm_config = get_llm_config()
        models = llm_config.fetch_models(provider_id)

        if not models:
            provider = llm_config.PROVIDERS.get(provider_id)
            if provider:
                models = provider.get('models', [])

        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/active', methods=['POST'])
def api_llm_set_active():
    """Set the active provider and model."""
    try:
        data = request.json
        provider_id = data.get('provider_id')
        model_id = data.get('model_id')

        if not provider_id:
            return jsonify({"error": "provider_id is required"}), 400
        if not model_id:
            return jsonify({"error": "model_id is required"}), 400

        llm_config = get_llm_config()

        if llm_config.set_active_model(provider_id, model_id):
            refresh_active_agents()

            # Get fresh stats for the current session to push to client
            from .shared import get_agent
            stats = {}
            try:
                agent = get_agent()
                stats = agent.get_context_stats()
            except:
                pass

            # Broadcast to clients
            if _socketio:
                _socketio.emit('provider_changed', {
                    'provider_id': provider_id,
                    'model_id': model_id,
                    'message': f'Switched to {model_id}',
                    'stats': stats
                })

            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Invalid provider"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/custom', methods=['POST'])
def api_llm_add_custom():
    """Add a custom LiteLLM provider."""
    try:
        data = request.json
        model_string = data.get('model_string', '').strip()
        name = data.get('name', '').strip() or None
        api_key = data.get('api_key', '').strip() or None
        api_key_env = data.get('api_key_env', '').strip() or None

        if not model_string:
            return jsonify({"error": "model_string is required"}), 400

        llm_config = get_llm_config()
        success, message = llm_config.add_custom_provider(
            model_string=model_string,
            name=name,
            api_key=api_key,
            api_key_env=api_key_env
        )

        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "error": message}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/custom/<provider_id>', methods=['DELETE'])
def api_llm_remove_custom(provider_id):
    """Remove a custom provider."""
    try:
        llm_config = get_llm_config()

        if llm_config.remove_custom_provider(provider_id):
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Provider not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/custom/<provider_id>/activate', methods=['POST'])
def api_llm_activate_custom(provider_id):
    """Set a custom provider as active."""
    try:
        llm_config = get_llm_config()

        if llm_config.set_custom_provider_active(provider_id):
            refresh_active_agents()

            custom = next((c for c in llm_config.get_custom_providers() if c['id'] == provider_id), None)
            if _socketio:
                _socketio.emit('provider_changed', {
                    'provider_id': provider_id,
                    'model_id': custom['model_string'] if custom else provider_id,
                    'message': f'Switched to {custom["name"] if custom else provider_id}'
                })

            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Provider not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/ollama/test', methods=['POST'])
def api_llm_ollama_test():
    """Test Ollama connection."""
    try:
        data = request.json or {}
        url = data.get('url')

        llm_config = get_llm_config()
        success, message, models = llm_config.test_ollama_connection(url)

        return jsonify({
            "success": success,
            "message": message,
            "models": models
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@llm_bp.route('/api/llm/ollama/url', methods=['POST'])
def api_llm_ollama_url():
    """Save Ollama server URL."""
    try:
        data = request.json
        url = data.get('url', '').strip()

        if not url:
            return jsonify({"error": "url is required"}), 400

        llm_config = get_llm_config()
        llm_config.set_ollama_url(url)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
