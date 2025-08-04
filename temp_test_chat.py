import requests
import json

test_data = {
    "user_message": "컨베이어 벨트가 자꾸 멈춰요. 어떻게 해결하면 좋을까요?",
    "issue_code": "CONV-BELT-001",
    "user_id": "test_user"
}

response = requests.post(
    "http://localhost:8000/chat/test",
    json=test_data,
    headers={"Content-Type": "application/json"},
    timeout=300  # Increased timeout to 5 minutes for multi-agent processing
)

print(response.text)
