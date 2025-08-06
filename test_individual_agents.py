import requests
import json

def test_individual_agent_memory():
    """개별 Agent 메모리 기능 테스트"""
    
    print("🧪 개별 Agent 메모리 기능 테스트 시작")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api"
    agents_to_test = ["gpt", "gemini", "clova"]
    
    for agent in agents_to_test:
        print(f"\n🤖 {agent.upper()} Agent 메모리 테스트")
        print("-" * 40)
        
        # 1. 첫 번째 질문 - 이름과 문제 소개
        print(f"1️⃣ {agent} - 첫 번째 질문 (이름과 문제 소개)")
        test_data_1 = {
            "message": "안녕하세요. 제 이름은 박서울입니다. 저희 공장의 설비에 금이 자꾸 생기는 문제로 고민 중입니다.",
            "session_id": None  # 새 세션
        }
        
        try:
            response_1 = requests.post(
                f"{base_url}/{agent}",
                json=test_data_1,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response_1.status_code == 200:
                result_1 = response_1.json()
                session_id = result_1.get('session_id')
                print(f"✅ 첫 번째 응답 성공")
                print(f"   - 세션 ID: {session_id}")
                print(f"   - 대화길이: {result_1.get('conversation_length')}")
                print(f"   - 응답 일부: {result_1.get('response', '')[:150]}...")
            else:
                print(f"❌ 첫 번째 질문 실패: {response_1.status_code}")
                print(f"   응답: {response_1.text}")
                continue
                
        except Exception as e:
            print(f"❌ 첫 번째 질문 중 오류: {str(e)}")
            continue
        
        # 2. 두 번째 질문 - 메모리 테스트 (같은 세션 사용)
        print(f"2️⃣ {agent} - 두 번째 질문 (메모리 테스트)")
        test_data_2 = {
            "message": "제 이름이 뭐라고 했었죠? 그리고 제가 무슨 문제로 고민한다고 했나요?",
            "session_id": session_id  # 같은 세션 ID 사용
        }
        
        try:
            response_2 = requests.post(
                f"{base_url}/{agent}",
                json=test_data_2,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response_2.status_code == 200:
                result_2 = response_2.json()
                print(f"✅ 두 번째 응답 성공")
                print(f"   - 세션 ID: {result_2.get('session_id')}")
                print(f"   - 대화길이: {result_2.get('conversation_length')}")
                
                # 메모리 테스트 검증
                response_text = result_2.get('response', '').lower()
                name_remembered = '박서울' in response_text or 'park' in response_text or '서울' in response_text
                problem_remembered = any(keyword in response_text for keyword in ['금', '균열', '크랙', '설비', '장비'])
                
                print(f"\n🧠 {agent.upper()} 메모리 테스트 결과:")
                print(f"   - 이름 기억: {'✅' if name_remembered else '❌'}")
                print(f"   - 문제 기억: {'✅' if problem_remembered else '❌'}")
                print(f"   - 응답 내용: {result_2.get('response', '')[:200]}...")
                
                if name_remembered and problem_remembered:
                    print(f"🎉 {agent.upper()} Agent 메모리 기능이 정상 작동합니다!")
                else:
                    print(f"⚠️ {agent.upper()} Agent 메모리 기능에 문제가 있습니다.")
                    
            else:
                print(f"❌ 두 번째 질문 실패: {response_2.status_code}")
                print(f"   응답: {response_2.text}")
                
        except Exception as e:
            print(f"❌ 두 번째 질문 중 오류: {str(e)}")
        
        # 3. 세션 상태 확인
        print(f"3️⃣ {agent} - 세션 상태 확인")
        try:
            session_response = requests.get(
                f"{base_url}/session/{session_id}",
                timeout=10
            )
            
            if session_response.status_code == 200:
                session_info = session_response.json()
                print(f"✅ 세션 정보 조회 성공")
                print(f"   - 사용자 ID: {session_info.get('user_id')}")
                print(f"   - 생성 시간: {session_info.get('created_at')}")
            else:
                print(f"❌ 세션 정보 조회 실패: {session_response.status_code}")
                
        except Exception as e:
            print(f"❌ 세션 정보 조회 중 오류: {str(e)}")
        
        print(f"\n{'='*60}")

if __name__ == "__main__":
    test_individual_agent_memory()