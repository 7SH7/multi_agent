#!/usr/bin/env python3
"""
실제 Multi-Agent + RAG + Memory 통합 테스트
"""

import asyncio
import sys
sys.path.append('.')

from models.agent_state import AgentState
from core.enhanced_workflow import EnhancedWorkflowManager
from core.session_manager import SessionManager
from datetime import datetime

async def integration_test():
    print("=" * 60)
    print("🧪 Multi-Agent + RAG + Memory 통합 테스트")
    print("=" * 60)
    
    try:
        # 1. 세션 생성
        session_manager = SessionManager()
        test_session = await session_manager.create_session("integration_test_user")
        session_id = test_session.session_id
        
        print(f"✅ 테스트 세션 생성: {session_id[:8]}...")
        
        # 2. 첫 번째 질문 (메모리 없음)
        print("\n1️⃣ 첫 번째 질문 - 메모리 없는 상태")
        print("-" * 40)
        
        first_state = AgentState({
            'user_message': '모터에서 이상한 진동이 발생하고 있어요. 어떻게 해야 할까요?',
            'session_id': session_id,
            'conversation_history': []  # 빈 히스토리
        })
        
        workflow = EnhancedWorkflowManager()
        first_result_obj = await workflow.execute(first_state)
        first_result = first_result_obj.final_state
        
        print(f"📤 첫 질문: {first_state.get('user_message')}")
        print(f"🤖 참여 Agent: {', '.join(first_result.get('selected_agents', []))}")
        
        if first_result.get('final_recommendation'):
            summary = first_result['final_recommendation'].get('executive_summary', '응답 없음')
            print(f"💡 답변 요약: {summary[:100]}...")
        
        # 대화 기록 저장
        await session_manager.add_conversation_detailed(session_id, {
            'user_message': first_state.get('user_message'),
            'agents_used': first_result.get('selected_agents', []),
            'timestamp': datetime.now().isoformat(),
            'final_recommendation': first_result.get('final_recommendation', {})
        })
        
        # 3. 두 번째 질문 (메모리 있음)
        print("\n2️⃣ 두 번째 질문 - 이전 대화 기억하는 상태")
        print("-" * 40)
        
        # 대화 기록 조회
        conversation_history = await session_manager.get_conversation_history(session_id)
        print(f"📚 불러온 대화 기록: {len(conversation_history)}개")
        
        second_state = AgentState({
            'user_message': '그런데 진동이 더 심해졌어요. 베어링 교체가 필요한 건가요?',
            'session_id': session_id,
            'conversation_history': conversation_history  # 이전 대화 포함
        })
        
        second_result_obj = await workflow.execute(second_state)
        second_result = second_result_obj.final_state

        print(f"📤 두번째 질문: {second_state.get('user_message')}")
        print(f"🤖 참여 Agent: {', '.join(second_result.get('selected_agents', []))}")
        
        if second_result.get('final_recommendation'):
            summary = second_result['final_recommendation'].get('executive_summary', '응답 없음')
            print(f"💡 답변 요약: {summary[:100]}...")
        
        # 4. RAG 데이터 활용 확인
        print("\n3️⃣ RAG 데이터 활용 확인")
        print("-" * 40)
        
        rag_context = first_result.get('rag_context', {})
        chroma_results = rag_context.get('chroma_results', [])
        es_results = rag_context.get('elasticsearch_results', [])
        
        print(f"📊 ChromaDB 검색 결과: {len(chroma_results)}개")
        print(f"📊 Elasticsearch 검색 결과: {len(es_results)}개")
        
        if chroma_results:
            print(f"   ChromaDB 샘플: {chroma_results[0].content[:60]}...")
        if es_results:
            print(f"   Elasticsearch 샘플: {es_results[0].content[:60]}...")
        
        # 5. 메모리 연속성 테스트
        print("\n4️⃣ 메모리 연속성 테스트")
        print("-" * 40)
        
        # Agent별 메모리 사용 확인
        agent_responses = second_result.get('agent_responses', {})
        
        for agent_name, response_data in agent_responses.items():
            if hasattr(response_data, 'response'):
                response_text = response_data.response
            else:
                response_text = response_data.get('response', '')
                
            # 이전 대화 언급 여부 확인 (두 번째 질문에서)
            if len(conversation_history) > 0:
                memory_keywords = ['이전', '앞서', '전에', '먼저', '방금']
                has_memory_reference = any(keyword in response_text for keyword in memory_keywords)
                print(f"🧠 {agent_name} 메모리 활용: {'✅' if has_memory_reference else '⚠️'}")
        
        print("\n" + "=" * 60)
        print("🎯 통합 테스트 결과")
        print("=" * 60)
        
        success_indicators = [
            ('세션 생성', test_session is not None),
            ('첫 번째 질문 처리', first_result.get('final_recommendation') is not None),
            ('대화 기록 저장', len(conversation_history) > 0),
            ('두 번째 질문 처리', second_result.get('final_recommendation') is not None),
            ('RAG 데이터 활용', len(chroma_results) > 0 or len(es_results) > 0),
            ('Agent 참여', len(first_result.get('selected_agents', [])) > 0)
        ]
        
        passed = sum(1 for _, success in success_indicators if success)
        total = len(success_indicators)
        
        for test_name, success in success_indicators:
            icon = "✅" if success else "❌"
            print(f"{icon} {test_name}")
        
        print(f"\n🏆 통합 테스트 성공률: {passed}/{total} ({passed/total*100:.1f}%) ")
        
        if passed == total:
            print("\n🎉🎉🎉 완전한 통합 시스템이 정상 작동합니다! 🎉🎉🎉")
            print("🚀 Multi-Agent + RAG + Memory 시스템 준비 완료!")
        else:
            print("\n⚠️  일부 기능에 문제가 있을 수 있습니다.")
        
    except Exception as e:
        print(f"\n❌ 통합 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(integration_test())