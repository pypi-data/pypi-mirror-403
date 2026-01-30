import json
import os
import time
import base64
import hmac
import hashlib
import urllib.request
import urllib.parse

def get_access_token(creds_path):
    with open(creds_path, 'r') as f:
        creds = json.load(f)
    
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": creds["client_email"],
        "sub": creds["client_email"],
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
        "scope": "https://www.googleapis.com/auth/cloud-platform"
    }
    
    def b64_encode(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")

    # Note: RSA signing is hard in pure python without libraries like 'cryptography' or 'PyJWT'.
    # Since I cannot install new libs, I'll check if 'google-auth' is available in the environment first.
    try:
        from google.oauth2 import service_account
        import google.auth.transport.requests
        import requests
        
        credentials = service_account.Credentials.from_service_account_file(
            creds_path, scopes=['https://www.googleapis.com/auth/cloud-platform'])
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token
    except ImportError:
        return None

token = get_access_token(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
if not token:
    print("FAILURE: Could not import google-auth to sign request.")
    exit(1)

url = f"https://{os.environ['VERTEXAI_LOCATION']}-aiplatform.googleapis.com/v1/projects/{os.environ['VERTEXAI_PROJECT']}/locations/{os.environ['VERTEXAI_LOCATION']}/publishers/google/models"
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print("SUCCESS")
        for m in data.get('models', []):
            mid = m['name'].split('/')[-1]
            if 'gemini' in mid:
                print(f"MODEL: {mid} | NAME: {m.get('displayName', mid)}")
except Exception as e:
    print(f"FAILURE: {e}")
