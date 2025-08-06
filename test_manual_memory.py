import requests
import json
import time

def test_manual_memory():
    """수동으로 메모리 기능 테스트 (Redis/MySQL 의존성 없이)"""
    
    print("🧪 수동 메모리 기능 테스트 시작")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # 1. 서버 상태 확인
    print("\n📊 서버 상태 확인...")
    try:
        response = requests.get(f"{base_url}/ping", timeout=5)
        if response.status_code == 200:
            print("✅ 서버 실행 중")
        else:
            print("❌ 서버 상태 불안정")
            return
    except Exception as e:
        print(f"❌ 서버 연결 실패: {str(e)}")
        print("💡 FastAPI 서버를 먼저 실행해주세요: python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
        return
    
    # 2. 첫 번째 질문 - 이름과 문제 소개
    print("\n1️⃣ 첫 번째 질문: '나는 김상방이야. 지금 틈이 생겨서 고민중이야.'")
    test_data_1 = {
        "user_message": "나는 김상방이야. 지금 틈이 생겨서 고민중이야.",
        "issue_code": "GENERAL",
        "user_id": "김상방"
    }
    
    try:
        response_1 = requests.post(
            f"{base_url}/chat/test",  # 테스트 엔드포인트 사용
            json=test_data_1,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response_1.status_code == 200:
            result_1 = response_1.json()
            session_id = result_1.get('session_id')
            print(f"✅ 첫 번째 응답 성공")
            print(f"   - 세션 ID: {session_id}")
            print(f"   - 대화수: {result_1.get('conversation_count')}")
            print(f"   - 응답 일부: {result_1.get('executive_summary', '')[:200]}...")
            
            # 잠시 대기
            print("⏳ 2초 대기 중...")
            time.sleep(2)
            
        else:
            print(f"❌ 첫 번째 질문 실패: {response_1.status_code}")
            print(f"   응답: {response_1.text}")
            return
            
    except Exception as e:
        print(f"❌ 첫 번째 질문 중 오류: {str(e)}")
        return
    
    # 3. 두 번째 질문 - 메모리 테스트 (같은 세션 사용)
    print("\n2️⃣ 두 번째 질문: '내 이름이 머라고? 그리고 지금 무슨 문제를 고민하고 있다고?'")
    test_data_2 = {
        "user_message": "내 이름이 머라고? 그리고 지금 무슨 문제를 고민하고 있다고?",
        "session_id": session_id  # 같은 세션 ID 사용
    }
    
    try:
        response_2 = requests.post(
            f"{base_url}/chat/test",  # 테스트 엔드포인트 사용
            json=test_data_2,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response_2.status_code == 200:
            result_2 = response_2.json()
            print(f"✅ 두 번째 응답 성공")
            print(f"   - 세션 ID: {result_2.get('session_id')}")
            print(f"   - 대화수: {result_2.get('conversation_count')}")
            
            # 메모리 테스트 검증
            response_text = result_2.get('executive_summary', '').lower()
            name_remembered = '김상방' in response_text or '상방' in response_text
            problem_remembered = any(keyword in response_text for keyword in ['틈', '고민', '문제'])
            
            print(f"\n🧠 메모리 테스트 결과:")
            print(f"   - 이름 기억: {'✅' if name_remembered else '❌'}")
            print(f"   - 문제 기억: {'✅' if problem_remembered else '❌'}")
            print(f"   - 응답 내용: {result_2.get('executive_summary', '')[:300]}...")
            
            if name_remembered and problem_remembered:
                print("\n🎉 메모리 기능이 정상 작동합니다!")
                return True
            else:
                print("\n⚠️ 메모리 기능에 문제가 있습니다.")
                return False
                
        else:
            print(f"❌ 두 번째 질문 실패: {response_2.status_code}")
            print(f"   응답: {response_2.text}")
            return False
            
    except Exception as e:
        print(f"❌ 두 번째 질문 중 오류: {str(e)}")
        return False

if __name__ == "__main__":
    test_manual_memory()