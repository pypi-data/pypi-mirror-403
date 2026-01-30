import json
import os
import urllib.request
from google.oauth2 import service_account
import google.auth.transport.requests

def test():
    project = os.environ['VERTEXAI_PROJECT']
    location = os.environ['VERTEXAI_LOCATION']
    creds_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        token = credentials.token
        
        # Try a more general endpoint to list base models
        # Note: The 'publishers/google/models' endpoint usually works, but let's try 'models' directly
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/models"
        
        # Or even better, just list the Gemini models via the 'publishers/google/models' again but check the URL carefully
        # The 404 might be because the 'publishers' endpoint requires a specific publisher ID (google)
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project}/locations/{location}/publishers/google/models"
        
        print(f"Requesting URL: {url}")
        
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            models = data.get('models', [])
            print(f"SUCCESS: Total models found: {len(models)}")
            for m in models:
                mid = m['name'].split('/')[-1]
                if 'gemini' in mid.lower():
                    print(f"MODEL: {mid} | NAME: {m.get('displayName', mid)}")
                
    except Exception as e:
        print(f"FAILURE: {str(e)}")
        if hasattr(e, 'read'):
            print("Error details:", e.read().decode())

if __name__ == '__main__':
    test()
