"""메모리 기능 테스트 스크립트"""
import asyncio
import httpx
import json
import time
from datetime import datetime

async def test_agent_memory():
    """각 에이전트의 메모리 기능을 테스트합니다."""
    
    base_url = "http://localhost:8000"
    
    print("🧠 에이전트 메모리 테스트 시작")
    print("=" * 50)
    
    # 각 에이전트별 테스트
    agents = ["gpt", "gemini", "clova"]
    test_results = {}
    
    for agent in agents:
        print(f"\n🤖 {agent.upper()} 에이전트 메모리 테스트")
        print("-" * 30)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 1단계: 자기소개 (이름과 문제 언급)
                first_message = "안녕하세요! 제 이름은 박서울이고, 지금 설비에 금이 간 것에 대해 고민하고 있어요. 이 문제를 어떻게 해결해야 할까요?"
                
                response1 = await client.post(
                    f"{base_url}/api/{agent}",
                    json={
                        "message": first_message,
                        "session_id": None
                    }
                )
                
                if response1.status_code == 200:
                    result1 = response1.json()
                    session_id = result1.get("session_id")
                    print(f"✅ 1단계 완료 - 세션 ID: {session_id}")
                    print(f"🤖 응답: {result1.get('response', '')[:100]}...")
                    
                    # 잠시 대기
                    await asyncio.sleep(2)
                    
                    # 2단계: 기억 테스트 (이름과 문제 기억하는지 확인)
                    memory_test_message = "제 이름이 뭐라고 했죠? 그리고 저는 지금 무슨 문제를 고민하고 있다고 했나요?"
                    
                    response2 = await client.post(
                        f"{base_url}/api/{agent}",
                        json={
                            "message": memory_test_message,
                            "session_id": session_id
                        }
                    )
                    
                    if response2.status_code == 200:
                        result2 = response2.json()
                        response_text = result2.get('response', '')
                        
                        print(f"✅ 2단계 완료")
                        print(f"🧠 메모리 테스트 응답: {response_text}")
                        
                        # 메모리 성능 평가
                        name_remembered = "박서울" in response_text
                        problem_remembered = any(keyword in response_text for keyword in ["금", "균열", "크랙", "설비"])
                        
                        test_results[agent] = {
                            "session_id": session_id,
                            "name_remembered": name_remembered,
                            "problem_remembered": problem_remembered,
                            "response": response_text,
                            "success": name_remembered and problem_remembered
                        }
                        
                        print(f"📊 평가 결과:")
                        print(f"   - 이름 기억: {'✅' if name_remembered else '❌'}")
                        print(f"   - 문제 기억: {'✅' if problem_remembered else '❌'}")
                        print(f"   - 전체 성공: {'✅' if name_remembered and problem_remembered else '❌'}")
                        
                    else:
                        print(f"❌ 2단계 실패: {response2.status_code}")
                        test_results[agent] = {"success": False, "error": "Stage 2 failed"}
                        
                else:
                    print(f"❌ 1단계 실패: {response1.status_code}")
                    test_results[agent] = {"success": False, "error": "Stage 1 failed"}
                    
        except Exception as e:
            print(f"❌ {agent} 테스트 중 오류: {str(e)}")
            test_results[agent] = {"success": False, "error": str(e)}
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("🏆 메모리 테스트 최종 결과")
    print("=" * 50)
    
    successful_agents = []
    failed_agents = []
    
    for agent, result in test_results.items():
        if result.get("success", False):
            successful_agents.append(agent)
            print(f"✅ {agent.upper()}: 메모리 기능 정상 작동")
        else:
            failed_agents.append(agent)
            error_msg = result.get("error", "Unknown error")
            print(f"❌ {agent.upper()}: 메모리 기능 문제 - {error_msg}")
    
    print(f"\n📈 성공률: {len(successful_agents)}/{len(agents)} ({len(successful_agents)/len(agents)*100:.1f}%)")
    
    if successful_agents:
        print(f"✅ 성공한 에이전트: {', '.join([a.upper() for a in successful_agents])}")
    if failed_agents:
        print(f"❌ 실패한 에이전트: {', '.join([a.upper() for a in failed_agents])}")
    
    return test_results

if __name__ == "__main__":
    print("서버가 실행 중인지 확인하세요 (http://localhost:8000)")
    print("3초 후 테스트를 시작합니다...")
    
    time.sleep(3)
    results = asyncio.run(test_agent_memory())