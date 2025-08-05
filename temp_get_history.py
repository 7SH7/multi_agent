import requests
import json

session_id = "sess_b684ba07383a"
url = f"http://localhost:8000/api/session/{session_id}/history"

try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    history = response.json()
    print(json.dumps(history, indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response status: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
