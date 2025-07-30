#!/usr/bin/env python3
"""시스템 테스트 스크립트"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.enhanced_workflow import get_enhanced_workflow
from models.agent_state import AgentState
from datetime import datetime

async def test_workflow():
    """워크플로우 테스트"""
    print("🔥 Multi-Agent 워크플로우 테스트 시작...")
    
    # 테스트 상태 생성
    test_state = AgentState()
    test_state.update({
        'session_id': 'test_session_001',
        'conversation_count': 1,
        'response_type': 'first_question',
        'user_message': '도어에 스크래치가 생겼는데 어떻게 해결하면 좋을까요?',
        'issue_code': 'ASBP-DOOR-SCRATCH-20240722001',
        'user_id': 'test_user',
        'conversation_history': [],
        'processing_steps': [],
        'timestamp': datetime.now(),
        'error': None
    })
    
    try:
        # 워크플로우 매니저 가져오기
        workflow_manager = get_enhanced_workflow()
        print("✅ 워크플로우 매니저 초기화 완료")
        
        # 워크플로우 실행
        result = await workflow_manager.execute(test_state)
        
        if result.success:
            print("✅ 워크플로우 실행 성공!")
            print(f"📊 실행 시간: {result.execution_time:.2f}초")
            print(f"📝 완료된 단계: {len(result.steps_completed)}개")
            
            final_state = result.final_state
            
            # RAG 분류 결과
            if 'issue_classification' in final_state:
                issue_info = final_state['issue_classification']
                print(f"🔍 이슈 분류: {issue_info.get('category', 'N/A')}")
                print(f"🎯 분류 신뢰도: {issue_info.get('classification_confidence', 0):.2f}")
            
            # 선택된 Agent들
            if 'selected_agents' in final_state:
                agents = final_state['selected_agents']
                print(f"🤖 선택된 Agent: {', '.join(agents)}")
                
            # Agent 응답
            if 'agent_responses' in final_state:
                responses = final_state['agent_responses']
                print(f"💬 Agent 응답 수: {len(responses)}개")
                for agent_name, response_data in responses.items():
                    confidence = response_data.get('confidence', 0)
                    print(f"  - {agent_name}: 신뢰도 {confidence:.2f}")
            
            # 최종 권장사항
            if 'final_recommendation' in final_state:
                recommendation = final_state['final_recommendation']
                print("🎯 최종 권장사항 생성됨")
                if 'executive_summary' in recommendation:
                    summary = recommendation['executive_summary'][:100]
                    print(f"📋 요약: {summary}...")
            
            print("\n🎉 테스트 완료!")
            return True
            
        else:
            print(f"❌ 워크플로우 실행 실패: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"💥 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """의존성 테스트"""
    print("📦 의존성 테스트...")
    
    success_count = 0
    total_count = 0
    
    # 핵심 모듈 import 테스트
    modules_to_test = [
        'config.settings',
        'models.agent_state',
        'agents.gpt_agent',
        'agents.gemini_agent', 
        'agents.clova_agent',
        'agents.rag_classifier',
        'agents.debate_moderator',
        'core.enhanced_workflow',
        'core.session_manager',
        'core.dynamic_branch',
        'utils.rag_engines',
        'utils.llm_clients'
    ]
    
    for module_name in modules_to_test:
        total_count += 1
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}: {str(e)}")
    
    print(f"\n📊 의존성 테스트 결과: {success_count}/{total_count} 성공")
    return success_count == total_count

async def main():
    """메인 테스트 함수"""
    print("🚀 Multi-Agent 챗봇 시스템 테스트")
    print("=" * 50)
    
    # 1. 의존성 테스트
    deps_ok = test_dependencies()
    if not deps_ok:
        print("❌ 의존성 테스트 실패. 시스템을 점검해주세요.")
        return
    
    print("\n" + "=" * 50)
    
    # 2. 워크플로우 테스트 (API 키가 없어도 기본 구조는 테스트 가능)
    workflow_ok = await test_workflow()
    
    print("\n" + "=" * 50)
    
    if deps_ok and workflow_ok:
        print("🎉 전체 테스트 성공! 시스템이 정상적으로 구성되었습니다.")
        print("💡 API 키를 설정하면 실제 LLM과 연동하여 완전한 기능을 사용할 수 있습니다.")
    else:
        print("⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(main())