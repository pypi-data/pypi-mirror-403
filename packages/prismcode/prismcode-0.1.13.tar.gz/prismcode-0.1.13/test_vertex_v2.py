import json
import os
import urllib.request
from google.oauth2 import service_account
import google.auth.transport.requests

def test():
    creds_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    project = os.environ['VERTEXAI_PROJECT']
    location = os.environ['VERTEXAI_LOCATION']
    
    try:
        # Get Token
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        token = credentials.token
        
        # Request models
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models"
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            gemini_models = [m for m in data.get('models', []) if 'gemini' in m['name'].lower()]
            
            if not gemini_models:
                print("FAILURE: No Gemini models found in response.")
                return

            print(f"SUCCESS: Found {len(gemini_models)} Gemini models.")
            for m in gemini_models:
                mid = m['name'].split('/')[-1]
                print(f"MODEL: {mid} | NAME: {m.get('displayName', mid)}")
                
    except Exception as e:
        print(f"FAILURE: {str(e)}")

test()
