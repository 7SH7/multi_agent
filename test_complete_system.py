#!/usr/bin/env python3
"""전체 시스템 메모리 기능 최종 검증"""

import asyncio
import requests
import json
import time

def test_complete_system_memory():
    """전체 시스템 메모리 기능 최종 통합 테스트"""
    
    print("🚀 전체 시스템 메모리 기능 최종 검증")
    print("=" * 70)
    
    base_url = "http://localhost:8000"
    test_results = {
        "multi_agent": {"passed": False, "details": ""},
        "individual_agents": {"gpt": False, "gemini": False, "clova": False},
        "session_management": {"passed": False, "details": ""},
        "overall_score": 0
    }
    
    # ===== 1. Multi-Agent 메모리 테스트 =====
    print("\n🔥 1. Multi-Agent 메모리 테스트")
    print("-" * 50)
    
    try:
        # 첫 번째 대화
        response_1 = requests.post(
            f"{base_url}/chat/test",
            json={
                "user_message": "안녕하세요. 제 이름은 박서울입니다. 저희 공장의 설비에 금이 자꾸 생기는 문제로 고민 중입니다.",
                "issue_code": "QUALITY-CRACK-001"
            },
            timeout=60
        )
        
        if response_1.status_code == 200:
            result_1 = response_1.json()
            session_id = result_1.get('session_id')
            
            # 두 번째 대화 (메모리 테스트)
            response_2 = requests.post(
                f"{base_url}/chat/test",
                json={
                    "user_message": "제 이름과 문제를 기억하고 계시나요?",
                    "session_id": session_id
                },
                timeout=60
            )
            
            if response_2.status_code == 200:
                result_2 = response_2.json()
                response_text = result_2.get('executive_summary', '').lower()
                
                name_remembered = '박서울' in response_text or '서울' in response_text
                problem_remembered = any(keyword in response_text for keyword in ['금', '균열', '크랙', '설비', '장비'])
                
                if name_remembered and problem_remembered:
                    test_results["multi_agent"]["passed"] = True
                    test_results["multi_agent"]["details"] = "✅ 이름과 문제 모두 정확히 기억"
                    print("✅ Multi-Agent 메모리 테스트 성공")
                else:
                    test_results["multi_agent"]["details"] = f"❌ 이름기억: {name_remembered}, 문제기억: {problem_remembered}"
                    print("❌ Multi-Agent 메모리 테스트 실패")
            else:
                test_results["multi_agent"]["details"] = f"❌ 두 번째 요청 실패: {response_2.status_code}"
        else:
            test_results["multi_agent"]["details"] = f"❌ 첫 번째 요청 실패: {response_1.status_code}"
            
    except Exception as e:
        test_results["multi_agent"]["details"] = f"❌ 오류: {str(e)}"
    
    # ===== 2. 개별 Agent 메모리 테스트 =====
    print("\n🤖 2. 개별 Agent 메모리 테스트")
    print("-" * 50)
    
    for agent in ["gpt", "gemini", "clova"]:
        print(f"\n테스트 중: {agent.upper()} Agent")
        try:
            # 첫 번째 대화
            response_1 = requests.post(
                f"{base_url}/api/{agent}",
                json={"message": "안녕하세요. 제 이름은 박서울입니다. 설비 금 문제로 고민입니다."},
                timeout=30
            )
            
            if response_1.status_code == 200:
                result_1 = response_1.json()
                session_id = result_1.get('session_id')
                
                # 두 번째 대화 (메모리 테스트)
                response_2 = requests.post(
                    f"{base_url}/api/{agent}",
                    json={
                        "message": "제 이름과 문제를 기억하시나요?",
                        "session_id": session_id
                    },
                    timeout=30
                )
                
                if response_2.status_code == 200:
                    result_2 = response_2.json()
                    response_text = result_2.get('response', '').lower()
                    
                    name_remembered = '박서울' in response_text or '서울' in response_text
                    problem_remembered = any(keyword in response_text for keyword in ['금', '균열', '크랙', '설비', '장비'])
                    
                    if name_remembered and problem_remembered:
                        test_results["individual_agents"][agent] = True
                        print(f"✅ {agent.upper()} Agent 메모리 성공")
                    else:
                        print(f"❌ {agent.upper()} Agent 메모리 실패")
                else:
                    print(f"❌ {agent.upper()} Agent 두 번째 요청 실패")
            else:
                print(f"❌ {agent.upper()} Agent 첫 번째 요청 실패")
                
        except Exception as e:
            print(f"❌ {agent.upper()} Agent 오류: {str(e)}")
    
    # ===== 3. 세션 관리 기능 테스트 =====
    print("\n🗄️ 3. 세션 관리 기능 테스트")
    print("-" * 50)
    
    try:
        # 세션 생성 테스트
        from core.session_manager import SessionManager
        
        async def test_session_operations():
            sm = SessionManager()
            
            # 세션 생성
            session = await sm.create_session('test_user', 'TEST_ISSUE')
            session_id = session.session_id
            
            # 대화 추가
            add_result = await sm.add_conversation(
                session_id, 
                "테스트 메시지", 
                "테스트 응답"
            )
            
            # 세션 조회
            retrieved_session = await sm.get_session(session_id)
            
            # 대화 기록 조회
            history = await sm.get_conversation_history(session_id)
            
            return {
                "session_created": session is not None,
                "conversation_added": add_result,
                "session_retrieved": retrieved_session is not None,
                "history_count": len(history),
                "conversation_count": retrieved_session.conversation_count if retrieved_session else 0
            }
        
        session_test_result = asyncio.run(test_session_operations())
        
        if (session_test_result["session_created"] and 
            session_test_result["conversation_added"] and 
            session_test_result["session_retrieved"] and 
            session_test_result["history_count"] > 0 and 
            session_test_result["conversation_count"] > 0):
            
            test_results["session_management"]["passed"] = True
            test_results["session_management"]["details"] = "✅ 모든 세션 관리 기능 정상"
            print("✅ 세션 관리 기능 테스트 성공")
        else:
            test_results["session_management"]["details"] = f"❌ 일부 기능 실패: {session_test_result}"
            print("❌ 세션 관리 기능 테스트 실패")
            
    except Exception as e:
        test_results["session_management"]["details"] = f"❌ 오류: {str(e)}"
        print(f"❌ 세션 관리 테스트 오류: {str(e)}")
    
    # ===== 최종 결과 계산 및 보고 =====
    print("\n📊 최종 테스트 결과 요약")
    print("=" * 70)
    
    # 점수 계산
    score = 0
    total_tests = 6  # Multi-Agent(1) + Individual Agents(3) + Session Management(1) + Redis(1)
    
    # Multi-Agent 점수
    if test_results["multi_agent"]["passed"]:
        score += 2  # 가중치 2배
        print("✅ Multi-Agent 메모리: PASS (가중치 2)")
    else:
        print(f"❌ Multi-Agent 메모리: FAIL - {test_results['multi_agent']['details']}")
    
    # 개별 Agent 점수
    for agent, result in test_results["individual_agents"].items():
        if result:
            score += 1
            print(f"✅ {agent.upper()} Agent 메모리: PASS")
        else:
            print(f"❌ {agent.upper()} Agent 메모리: FAIL")
    
    # 세션 관리 점수
    if test_results["session_management"]["passed"]:
        score += 1
        print("✅ 세션 관리: PASS")
    else:
        print(f"❌ 세션 관리: FAIL - {test_results['session_management']['details']}")
    
    # Redis 연결 확인
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        if r.ping():
            score += 1
            print("✅ Redis 연결: PASS")
        else:
            print("❌ Redis 연결: FAIL")
    except:
        print("❌ Redis 연결: FAIL")
    
    # 최종 점수 및 등급 계산
    test_results["overall_score"] = (score / 7) * 100  # 총 7점 만점
    
    print(f"\n🎯 전체 시스템 점수: {score}/7 ({test_results['overall_score']:.1f}%)")
    
    if test_results["overall_score"] >= 90:
        grade = "🏆 EXCELLENT - 모든 메모리 기능이 완벽히 작동합니다!"
    elif test_results["overall_score"] >= 75:
        grade = "🥇 GOOD - 대부분의 메모리 기능이 정상 작동합니다!"
    elif test_results["overall_score"] >= 50:
        grade = "🥈 FAIR - 일부 메모리 기능에 문제가 있습니다."
    else:
        grade = "🥉 POOR - 메모리 기능에 심각한 문제가 있습니다."
    
    print(f"\n{grade}")
    
    print(f"\n🔧 개선 사항:")
    if not test_results["multi_agent"]["passed"]:
        print("   - Multi-Agent 시스템의 대화 기록 전달 개선 필요")
    
    failed_agents = [agent for agent, result in test_results["individual_agents"].items() if not result]
    if failed_agents:
        print(f"   - {', '.join(failed_agents).upper()} Agent의 메모리 기능 개선 필요")
    
    if not test_results["session_management"]["passed"]:
        print("   - 세션 관리 시스템 안정성 개선 필요")
    
    print("\n" + "=" * 70)
    print("🎉 전체 시스템 메모리 기능 검증 완료!")
    
    return test_results

if __name__ == "__main__":
    results = test_complete_system_memory()