import requests
import json
import time
from typing import Optional

BASE_URL = "http://localhost:8000"
API_KEY = "user-key-456"

def send_chat_message(user_message: str, session_id: Optional[str] = None, user_id: str = "test_user"):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    payload = {
        "user_message": user_message,
        "user_id": user_id
    }
    if session_id:
        payload["session_id"] = session_id

    print(f"\n--- Sending Request ---\nURL: {BASE_URL}/chat\nPayload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/chat", headers=headers, json=payload, timeout=180)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        result = response.json()
        print(f"\n--- Received Response ---\nStatus: {response.status_code}\nResponse: {json.dumps(result, indent=2)}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"\n--- Request Failed ---\nError: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        return None

def run_memory_test():
    print("메모리 테스트 시작...")

    # 1단계: 첫 번째 질문
    first_message = "내 이름은 박서울이야. 그리고 나는 지금 금이 간 것에 대해 고민을 하고 있어."
    response1 = send_chat_message(first_message)

    if not response1 or "session_id" not in response1:
        print("첫 번째 요청 실패 또는 session_id를 얻지 못했습니다. 테스트를 중단합니다.")
        return

    session_id = response1["session_id"]
    print(f"새로운 세션 ID: {session_id}")
    
    # Agent가 응답을 처리할 시간을 줍니다。
    time.sleep(5) 

    # 2단계: 두 번째 질문 (메모리 확인)
    second_message = "내 이름이 뭐라고? 그리고 난 무슨 문제를 고민하고 있다고?"
    response2 = send_chat_message(second_message, session_id=session_id)

    if not response2:
        print("두 번째 요청 실패. 테스트를 중단합니다.")
        return

    executive_summary = response2.get("executive_summary", "").lower()
    
    print("\n--- 메모리 확인 결과 ---")
    name_remembered = "박서울" in executive_summary
    problem_remembered = "금이 간 것" in executive_summary

    if name_remembered and problem_remembered:
        print("✅ Agent가 이전 대화 내역(이름, 문제)을 성공적으로 기억하고 있습니다.")
    else:
        print("❌ Agent가 이전 대화 내역을 제대로 기억하지 못했습니다.")
        print(f"Agent 응답 요약: {executive_summary}")
        print(f"Agent 전체 응답: {response2.get('response', 'N/A')}")

    print("\n메모리 테스트 완료.")

if __name__ == "__main__":
    run_memory_test()
