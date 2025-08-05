import requests

test_data = {
    "user_message": "제품에 균열이 자꾸 생겨요. 원인을 찾아주세요.",
    "issue_code": "QUALITY-CRACK-003",
    "user_id": "qc_03"
}

response = requests.post(
    "http://localhost:8000/chat/test",
    json=test_data,
    headers={"Content-Type": "application/json"},
    timeout=300  # Increased timeout to 5 minutes for multi-agent processing
)

print(response.text)
