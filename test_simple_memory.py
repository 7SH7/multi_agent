"""Simple memory test without complex session management"""

import requests
import json
import time

def test_memory_with_simple_approach():
    """간단한 방식으로 메모리 테스트"""
    
    base_url = "http://localhost:8000"
    session_id = "simple_memory_test"
    
    # 첫 번째 질문
    print("=== 첫 번째 질문 ===")
    first_response = requests.post(
        f"{base_url}/api/gpt",
        json={
            "message": "나는 김상방이야. 지금 틈이 생겨서 고민중이야.",
            "session_id": session_id
        }
    )
    
    if first_response.status_code == 200:
        result = first_response.json()
        print(f"응답: {result['response'][:200]}...")
    else:
        print(f"오류: {first_response.text}")
    
    time.sleep(2)
    
    # 두 번째 질문
    print("\n=== 두 번째 질문 ===")
    second_response = requests.post(
        f"{base_url}/api/gpt",
        json={
            "message": "내 이름이 뭐라고? 그리고 지금 무슨 문제를 고민하고 있다고?",
            "session_id": session_id
        }
    )
    
    if second_response.status_code == 200:
        result = second_response.json()
        print(f"응답: {result['response'][:200]}...")
        
        # 메모리 기능 테스트
        if "김상방" in result['response'] and "틈" in result['response']:
            print("✅ 메모리 기능이 정상 작동합니다!")
        else:
            print("❌ 메모리 기능이 작동하지 않습니다.")
            print("김상방이 포함되어 있나?", "김상방" in result['response'])
            print("틈이 포함되어 있나?", "틈" in result['response'])
    else:
        print(f"오류: {second_response.text}")
    
    # 세션 히스토리 확인
    print("\n=== 세션 히스토리 확인 ===")
    history_response = requests.get(f"{base_url}/api/session/{session_id}/history")
    
    if history_response.status_code == 200:
        history = history_response.json()
        print(f"대화 기록 수: {len(history['messages'])}")
        for i, msg in enumerate(history['messages']):
            print(f"{i+1}. 사용자: {msg.get('user_message', '')[:50]}...")
            print(f"   봇: {msg.get('bot_response', '')[:50]}...")
    else:
        print(f"히스토리 조회 오류: {history_response.text}")

if __name__ == "__main__":
    test_memory_with_simple_approach()