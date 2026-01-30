import os
import litellm
from dotenv import load_dotenv

# 1. Load the environment variables we proved work
load_dotenv()

# Ensure we have the critical variables
api_key = os.getenv("GOOGLE_CLOUD_API_KEY")

if not api_key:
    print("Error: Missing GOOGLE_CLOUD_API_KEY")
    exit(1)

# 2. Setup the Chat
print(f"🤖 Connected to Gemini 3 Pro (Vertex AI via API Key)")
messages = [{"role": "system", "content": "You are a helpful AI assistant."}]

# Enable debug to see what LiteLLM is actually doing
litellm.set_verbose = False

while True:
    try:
        user_input = input("\nYou: ")
        if user_input.lower() in ["quit", "exit"]: break
        
        messages.append({"role": "user", "content": user_input})
        
        # 3. Call LiteLLM 
        # Strategy: Use 'gemini/' prefix (which uses api_key) but point api_base to Vertex
        # The curl worked at: https://aiplatform.googleapis.com/v1/publishers/google/models/gemini-3-pro-preview:streamGenerateContent
        
        # IMPORTANT: LiteLLM Gemini provider usually expects api_base to be "https://generativelanguage.googleapis.com/v1beta"
        # and it appends "/models/{model}:{action}"
        
        # Since we are using Vertex with API key, we need to trick it.
        # If we set api_base to "https://aiplatform.googleapis.com/v1/publishers/google", 
        # LiteLLM appends "/models/gemini-3-pro-preview:streamGenerateContent"
        # resulting in the correct URL.
        
        response = litellm.completion(
            model="gemini/gemini-3-pro-preview",
            messages=messages,
            api_key=api_key,
            api_base="https://aiplatform.googleapis.com/v1/publishers/google",
            stream=True
        )

        print("AI: ", end="", flush=True)
        full_content = ""
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
            full_content += content
            
        messages.append({"role": "assistant", "content": full_content})
        print() # Newline

    except Exception as e:
        print(f"\n❌ Error: {e}")
