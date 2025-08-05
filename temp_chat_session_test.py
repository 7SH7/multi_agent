import requests
import json
import time
from typing import Optional

BASE_URL = "http://localhost:8000"

def chat_with_session(user_message: str, session_id: Optional[str] = None, user_id: str = "test_user"):
    url = f"{BASE_URL}/chat"
    payload = {
        "user_message": user_message,
        "issue_code": "TEST-ISSUE",
        "user_id": user_id
    }
    if session_id:
        payload["session_id"] = session_id

    print("\n--- Request ---")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()  # Raise an exception for HTTP errors
        result = response.json()

        print("\n--- Response ---")
        print(f"Session ID: {result.get('session_id')}")
        print(f"Conversation Count: {result.get('conversation_count')}")
        print(f"Participating Agents: {', '.join(result.get('participating_agents', []))}")
        print(f"Processing Time: {result.get('processing_time'):.2f}s")
        print(f"Executive Summary: {result.get('executive_summary')[:150]}...")
        return result
    except requests.exceptions.RequestException as e:
        print("\n--- Error ---")
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None

def get_session_history(session_id: str):
    url = f"{BASE_URL}/api/session/{session_id}/history" # URL 수정
    print("\n--- Request History ---")
    print(f"URL: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        history = response.json()
        print(f"\n--- Session History for {session_id} ---")
        for msg in history.get('messages', []):
            # 'user_message'와 'bot_response' 필드가 있는지 확인
            user_msg = msg.get('user_message', '')
            bot_response = msg.get('bot_response', '')
            timestamp = msg.get('timestamp', '').split('T')[1][:8] if msg.get('timestamp') else 'N/A'
            print(f"[{timestamp}] User: {user_msg[:50]}... -> Bot: {bot_response[:50]}...")
        return history
    except requests.exceptions.RequestException as e:
        print("\n--- Error Getting History ---")
        print(f"Request failed: {e}")
        return None

if __name__ == "__main__":
    print("🚀 대화 기억 기능 테스트 시작!")

    # 1. 새 세션 시작
    print("\n--- 1단계: 새 세션 시작 ---")
    first_response = chat_with_session("우리 공장의 컨베이어 벨트가 자주 멈추는데, 원인이 뭘까요?")
    if not first_response:
        print("테스트 실패: 첫 번째 요청 실패.")
        exit()
    
    session_id = first_response.get('session_id')
    print(f"새 세션 ID: {session_id}")
    time.sleep(5) # Wait a bit for session to be fully saved

    # 2. 동일 세션으로 후속 질문
    print("\n--- 2단계: 동일 세션으로 후속 질문 ---")
    second_response = chat_with_session("그럼, 센서 오작동을 확인하려면 어떻게 해야 하나요?", session_id=session_id)
    if not second_response:
        print("테스트 실패: 두 번째 요청 실패.")
        exit()
    time.sleep(5) # Wait a bit

    # 3. 동일 세션으로 세 번째 질문 (이전 대화 맥락 활용)
    print("\n--- 3단계: 동일 세션으로 세 번째 질문 ---")
    third_response = chat_with_session("모터 과열은 어떻게 진단하고 예방할 수 있나요?", session_id=session_id)
    if not third_response:
        print("테스트 실패: 세 번째 요청 실패.")
        exit()
    time.sleep(5) # Wait a bit

    # 4. 세션 기록 조회
    print("\n--- 4단계: 세션 기록 조회 ---")
    history = get_session_history(session_id)
    if history:
        print("대화 기록 조회 성공.")
    else:
        print("대화 기록 조회 실패.")

    print("\n🚀 대화 기억 기능 테스트 완료!")