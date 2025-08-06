import asyncio
import requests
import json

async def test_multi_agent_memory():
    """Multi-Agent 메모리 기능 통합 테스트"""
    
    print("🧪 Multi-Agent 메모리 통합 테스트 시작")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # 1. 첫 번째 질문 - 이름과 문제 소개
    print("\n1️⃣ 첫 번째 질문 (이름과 문제 소개)")
    test_data_1 = {
        "user_message": "안녕하세요. 제 이름은 박서울입니다. 저희 공장의 설비에 금이 자꾸 생기는 문제로 고민 중입니다.",
        "issue_code": "QUALITY-CRACK-001"
    }
    
    try:
        response_1 = requests.post(
            f"{base_url}/chat",
            json=test_data_1,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "test-key"  # 테스트용 API 키
            },
            timeout=60
        )
        
        if response_1.status_code == 200:
            result_1 = response_1.json()
            session_id = result_1.get('session_id')
            print(f"✅ 첫 번째 응답 성공")
            print(f"   - 세션 ID: {session_id}")
            print(f"   - 대화수: {result_1.get('conversation_count')}")
            print(f"   - 참여 에이전트: {result_1.get('participating_agents', [])}")
            print(f"   - 응답 일부: {result_1.get('executive_summary', '')[:200]}...")
        else:
            print(f"❌ 첫 번째 질문 실패: {response_1.status_code}")
            print(f"   응답: {response_1.text}")
            return
            
    except Exception as e:
        print(f"❌ 첫 번째 질문 중 오류: {str(e)}")
        return
    
    # 2. 두 번째 질문 - 메모리 테스트 (같은 세션 사용)
    print("\n2️⃣ 두 번째 질문 (메모리 테스트)")
    test_data_2 = {
        "user_message": "제 이름이 뭐라고 했었죠? 그리고 제가 무슨 문제로 고민한다고 했나요?",
        "session_id": session_id  # 같은 세션 ID 사용
    }
    
    try:
        response_2 = requests.post(
            f"{base_url}/chat",
            json=test_data_2,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "test-key"  # 테스트용 API 키
            },
            timeout=60
        )
        
        if response_2.status_code == 200:
            result_2 = response_2.json()
            print(f"✅ 두 번째 응답 성공")
            print(f"   - 세션 ID: {result_2.get('session_id')}")
            print(f"   - 대화수: {result_2.get('conversation_count')}")
            print(f"   - 참여 에이전트: {result_2.get('participating_agents', [])}")
            
            # 메모리 테스트 검증
            response_text = result_2.get('executive_summary', '').lower()
            name_remembered = '박서울' in response_text or 'park' in response_text or '서울' in response_text
            problem_remembered = any(keyword in response_text for keyword in ['금', '균열', '크랙', '설비', '장비'])
            
            print(f"\n🧠 메모리 테스트 결과:")
            print(f"   - 이름 기억: {'✅' if name_remembered else '❌'}")
            print(f"   - 문제 기억: {'✅' if problem_remembered else '❌'}")
            print(f"   - 응답 내용: {result_2.get('executive_summary', '')[:300]}...")
            
            if name_remembered and problem_remembered:
                print("\n🎉 Multi-Agent 메모리 기능이 정상 작동합니다!")
            else:
                print("\n⚠️ Multi-Agent 메모리 기능에 문제가 있습니다.")
                
        else:
            print(f"❌ 두 번째 질문 실패: {response_2.status_code}")
            print(f"   응답: {response_2.text}")
            
    except Exception as e:
        print(f"❌ 두 번째 질문 중 오류: {str(e)}")
    
    # 3. 세션 상태 확인
    print("\n3️⃣ 세션 상태 확인")
    try:
        session_response = requests.get(
            f"{base_url}/session/{session_id}",
            timeout=10
        )
        
        if session_response.status_code == 200:
            session_info = session_response.json()
            print(f"✅ 세션 정보 조회 성공")
            print(f"   - 총 대화수: {session_info.get('conversation_count')}")
            print(f"   - 상태: {session_info.get('status')}")
            print(f"   - 사용된 에이전트: {session_info.get('agents_used', [])}")
        else:
            print(f"❌ 세션 정보 조회 실패: {session_response.status_code}")
            
    except Exception as e:
        print(f"❌ 세션 정보 조회 중 오류: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_multi_agent_memory())