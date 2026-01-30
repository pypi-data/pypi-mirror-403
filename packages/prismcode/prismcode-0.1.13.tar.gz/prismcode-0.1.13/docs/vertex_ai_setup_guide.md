# Vertex AI & Gemini 3 Setup Guide: Lessons Learned

## Overview

This document details the successful configuration of Google's Gemini 3 Pro (Vertex AI) within the Mobius/LiteLLM environment. The process revealed critical nuances between Google's authentication methods (Service Account vs. API Key) and how they interact with different model rollouts.

## The Problem: The "404" Trap

We initially attempted the standard Vertex AI setup using a Service Account JSON file (`GOOGLE_APPLICATION_CREDENTIALS`). While this authenticated successfully, we hit persistent `404 Not Found` errors when requesting newer models like `gemini-3-pro-preview`.

**Symptoms:**
- Authentication: ✅ Success (Token generated)
- Legacy Models (`gemini-1.5-pro`): ❌ 404 Not Found (in some regions/projects)
- New Models (`gemini-3-pro`): ❌ 404 Not Found

**Root Cause:**
Even with valid credentials, specific Google Cloud Projects requires the **Vertex AI API** to be explicitly enabled in the Google Cloud Console. Furthermore, some "Preview" models are accessible via API Key on the `aiplatform` endpoint before they fully propagate to standard Service Account OAuth flows in all regions.

## The Solution: Hybrid API Key Auth

The working solution uses a **Vertex AI-provisioned API Key**. This bypasses some of the IAM complexity and hits the endpoint that Google Studio uses.

### 1. Required Environment Variables (.env)

These three variables must exist together for LiteLLM to route the request correctly to the Vertex endpoint using an API Key.

```bash
# 1. The Project ID (Required for URL construction)
VERTEXAI_PROJECT="gen-lang-client-0821681600"

# 2. The Region (Gemini 3 is currently strictly US-Central1)
VERTEXAI_LOCATION="us-central1"

# 3. The API Key (NOT Gemini API Key, but a Vertex-scoped key)
GOOGLE_CLOUD_API_KEY="AQ.Ab8RN6I..." 
```

### 2. LiteLLM Configuration Pattern

In `core/llm_config.py`, we configured the provider to use the `gemini/` prefix (which triggers the Google logic) but supplied the Vertex environment variables. This forces LiteLLM to use the Vertex endpoint (`aiplatform.googleapis.com`) instead of the consumer Generative Language endpoint (`generativelanguage.googleapis.com`), while still using the API Key for auth.

```python
'google': {
    'name': 'Google (Gemini)',
    'key_env': 'GOOGLE_CLOUD_API_KEY', 
    'litellm_prefix': 'gemini/', 
    'default_model': 'gemini-3-pro-preview',
    'models': [
        {'id': 'gemini-3-pro-preview', 'name': 'Gemini 3 Pro Preview'},
        ...
    ]
}
```

## How to Verify (The "Golden Test")

If you are unsure if the setup is working, bypass all Python libraries and use `curl`. This tests the network path, API key, and Project permissions in one go.

```bash
export API_KEY="YOUR_KEY_HERE"
export PROJECT="YOUR_PROJECT_ID"
export LOCATION="us-central1"
export MODEL="gemini-3-pro-preview"

curl -s "https://aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOCATION}/publishers/google/models/${MODEL}:streamGenerateContent?key=${API_KEY}" \
-X POST \
-H "Content-Type: application/json" \
-d '{
  "contents": [{ "role": "user", "parts": [{ "text": "hi" }] }]
}'
```

**Success Indicators:**
- HTTP 200 OK
- JSON response containing `"thoughtSignature"` (unique to Gemini 3 Thinking models)

## Summary of Configuration for Future APIs

| API Type | Env Var | Notes |
|----------|---------|-------|
| **Anthropic** | `ANTHROPIC_API_KEY` | Simple key auth. |
| **OpenAI** | `OPENAI_API_KEY` | Simple key auth. |
| **Vertex (Service Acct)** | `GOOGLE_APPLICATION_CREDENTIALS` | **JSON Path**. Best for production/server-to-server. Requires enabled API. |
| **Vertex (API Key)** | `GOOGLE_CLOUD_API_KEY` + `VERTEXAI_PROJECT` | **Hybrid**. Best for rapid access to Preview models. What we used here. |
