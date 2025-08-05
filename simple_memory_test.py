"""간단한 메모리 테스트 - Redis 없이"""
import asyncio
import sys
import os
sys.path.append('.')

from core.session_manager import SessionManager
from agents.gpt_agent import GPTAgent
from agents.gemini_agent import GeminiAgent
from agents.clova_agent import ClovaAgent
from models.agent_state import AgentState
from datetime import datetime

async def test_agent_memory_direct():
    """Redis 없이 직접 메모리 테스트"""
    
    print("🧠 에이전트 메모리 직접 테스트")
    print("=" * 50)
    
    # 메모리 기반 세션 (Redis 없이)
    conversations = {}
    
    agents = {
        "gpt": GPTAgent(),
        "gemini": GeminiAgent(), 
        "clova": ClovaAgent()
    }
    
    for agent_name, agent in agents.items():
        print(f"\n🤖 {agent_name.upper()} 에이전트 테스트")
        print("-" * 30)
        
        try:
            # 1단계: 자기소개
            first_message = "안녕하세요! 제 이름은 박서울이고, 지금 설비에 금이 간 것에 대해 고민하고 있어요."
            
            # 첫 번째 AgentState 생성
            state1 = AgentState(
                session_id=f"{agent_name}_test_session",
                conversation_count=1,
                response_type="first_question",
                user_message=first_message,
                issue_code="MEMORY_TEST",
                user_id="박서울",
                issue_classification={},
                question_category=None,
                rag_context={},
                selected_agents=[agent_name],
                selection_reasoning=f"Direct {agent_name} test",
                agent_responses=None,
                response_quality_scores=None,
                debate_rounds=None,
                consensus_points=None,
                final_recommendation=None,
                equipment_type=None,
                equipment_kr=None,
                problem_type=None,
                root_causes=None,
                severity_level=None,
                analysis_confidence=None,
                conversation_history=[],
                processing_steps=[],
                total_processing_time=0.0,
                timestamp=datetime.now().isoformat(),
                error=None,
                performance_metrics={},
                resource_usage={},
                failed_agents=None
            )
            
            print(f"📤 1단계 메시지: {first_message}")
            
            # Agent 실행
            if hasattr(agent, 'analyze_and_respond'):
                response1 = await agent.analyze_and_respond(state1)
                # AgentResponse 객체에서 response 속성 가져오기
                if hasattr(response1, 'response'):
                    response_text1 = response1.response
                elif isinstance(response1, dict):
                    response_text1 = response1.get('response', '응답 없음')
                else:
                    response_text1 = str(response1)
            else:
                response_text1 = f"{agent_name} Agent에 적절한 메서드가 없습니다."
            
            print(f"📥 1단계 응답: {response_text1[:100]}...")
            
            # 대화 기록 저장
            conversations[agent_name] = [
                {"role": "user", "content": first_message},
                {"role": "assistant", "content": response_text1}
            ]
            
            # 2단계: 메모리 테스트
            memory_test_message = "제 이름이 뭐라고 했죠? 그리고 저는 지금 무슨 문제를 고민하고 있다고 했나요?"
            
            # 두 번째 AgentState 생성 (이전 대화 포함)
            state2 = AgentState(
                session_id=f"{agent_name}_test_session",
                conversation_count=2,
                response_type="follow_up",
                user_message=memory_test_message,
                issue_code="MEMORY_TEST",
                user_id="박서울",
                issue_classification={},
                question_category=None,
                rag_context={},
                selected_agents=[agent_name],
                selection_reasoning=f"Direct {agent_name} test",
                agent_responses=None,
                response_quality_scores=None,
                debate_rounds=None,
                consensus_points=None,
                final_recommendation=None,
                equipment_type=None,
                equipment_kr=None,
                problem_type=None,
                root_causes=None,
                severity_level=None,
                analysis_confidence=None,
                conversation_history=conversations[agent_name],  # 이전 대화 포함
                processing_steps=[],
                total_processing_time=0.0,
                timestamp=datetime.now().isoformat(),
                error=None,
                performance_metrics={},
                resource_usage={},
                failed_agents=None
            )
            
            print(f"📤 2단계 메시지: {memory_test_message}")
            
            # Agent 실행
            if hasattr(agent, 'analyze_and_respond'):
                response2 = await agent.analyze_and_respond(state2)
                # AgentResponse 객체에서 response 속성 가져오기
                if hasattr(response2, 'response'):
                    response_text2 = response2.response
                elif isinstance(response2, dict):
                    response_text2 = response2.get('response', '응답 없음')
                else:
                    response_text2 = str(response2)
            else:
                response_text2 = f"{agent_name} Agent에 적절한 메서드가 없습니다."
            
            print(f"📥 2단계 응답: {response_text2}")
            
            # 메모리 성능 평가
            name_remembered = "박서울" in response_text2
            problem_remembered = any(keyword in response_text2 for keyword in ["금", "균열", "크랙", "설비", "문제"])
            
            print(f"📊 메모리 테스트 결과:")
            print(f"   - 이름 기억: {'✅' if name_remembered else '❌'}")
            print(f"   - 문제 기억: {'✅' if problem_remembered else '❌'}")
            print(f"   - 전체 성공: {'✅' if name_remembered and problem_remembered else '❌'}")
            
        except Exception as e:
            print(f"❌ {agent_name} 테스트 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_memory_direct())