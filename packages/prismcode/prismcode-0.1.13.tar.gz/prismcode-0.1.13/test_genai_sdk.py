from google import genai
from google.genai import types
import os

def generate():
    client = genai.Client(
        vertexai=True,
        project=os.environ.get("VERTEXAI_PROJECT"),
        location=os.environ.get("VERTEXAI_LOCATION"),
    )

    model = "gemini-2.0-flash-thinking-exp-01-21" # Using a known valid model ID for this SDK
    # The user provided gemini-3-pro-preview but let's see if 2.0 works first as a baseline
    
    generate_content_config = types.GenerateContentConfig(
        temperature = 1,
        thinking_config=types.ThinkingConfig(include_thoughts=True),
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents="hi",
            config=generate_content_config,
        )
        print("SUCCESS")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"FAILURE: {str(e)}")

if __name__ == '__main__':
    generate()
