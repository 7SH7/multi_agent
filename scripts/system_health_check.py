#!/usr/bin/env python3
"""
완전한 Multi-Agent + RAG + Memory 시스템 상태 확인 스크립트
"""

import asyncio
import sys
sys.path.append('.')

from utils.rag_engines import HybridRAGEngine
from core.session_manager import SessionManager
from agents.gpt_agent import GPTAgent
from agents.gemini_agent import GeminiAgent
from agents.clova_agent import ClovaAgent
from agents.debate_moderator import DebateModerator

async def comprehensive_system_check():
    print("=" * 60)
    print("🚀 Multi-Agent + RAG + Memory 시스템 종합 점검")
    print("=" * 60)
    
    results = {}
    
    # 1. RAG 시스템 확인
    print("\n1️⃣ 하이브리드 RAG 시스템 점검")
    print("-" * 40)
    
    try:
        hybrid_rag = HybridRAGEngine()
        
        # ChromaDB 테스트
        chroma_results = await hybrid_rag.chroma_engine.search("모터 베어링", top_k=2)
        print(f"✅ ChromaDB: {len(chroma_results)}개 결과")
        
        # Elasticsearch 테스트
        es_results = await hybrid_rag.elasticsearch_engine.search("PLC 프로그래밍", top_k=2)
        print(f"✅ Elasticsearch: {len(es_results)}개 결과")
        
        # 하이브리드 테스트
        hybrid_results = await hybrid_rag.search("유압 시스템 누유", top_k=3)
        print(f"✅ 하이브리드 RAG: {len(hybrid_results)}개 통합 결과")
        
        results['rag'] = True
        await hybrid_rag.close()
        
    except Exception as e:
        print(f"❌ RAG 시스템 오류: {str(e)}")
        results['rag'] = False
    
    # 2. 메모리 시스템 확인
    print("\n2️⃣ 세션 메모리 시스템 점검")
    print("-" * 40)
    
    try:
        session_manager = SessionManager()
        
        # 테스트 세션 생성
        test_session = await session_manager.create_session("test_user")
        print(f"✅ 세션 생성: {test_session.session_id[:8]}...")
        
        # 대화 기록 추가
        await session_manager.add_conversation(
            test_session.session_id, 
            '모터에서 이상한 소리가 나요',
            'GPT와 Gemini 전문가가 분석한 결과, 베어링 마모가 의심됩니다.'
        )
        
        # 대화 기록 조회
        history = await session_manager.get_conversation_history(test_session.session_id)
        print(f"✅ 대화 기록 저장/조회: {len(history)}개 기록")
        
        results['memory'] = True
        
    except Exception as e:
        print(f"❌ 메모리 시스템 오류: {str(e)}")
        results['memory'] = False
    
    # 3. Agent 메모리 연동 확인
    print("\n3️⃣ Agent 메모리 연동 점검")
    print("-" * 40)
    
    try:
        # GPT Agent 메모리 기능 확인
        gpt_agent = GPTAgent()
        gpt_has_memory = hasattr(gpt_agent, 'build_analysis_prompt') and \
                        'conversation_history' in gpt_agent.build_analysis_prompt.__code__.co_varnames
        print(f"✅ GPT Agent 메모리: {'연동됨' if gpt_has_memory else '연동 안됨'}")
        
        # Gemini Agent 메모리 기능 확인
        gemini_agent = GeminiAgent()
        gemini_has_memory = hasattr(gemini_agent, 'build_technical_prompt') and \
                           'conversation_history' in gemini_agent.build_technical_prompt.__code__.co_varnames
        print(f"✅ Gemini Agent 메모리: {'연동됨' if gemini_has_memory else '연동 안됨'}")
        
        # Clova Agent 메모리 기능 확인
        clova_agent = ClovaAgent()
        clova_has_memory = hasattr(clova_agent, 'build_practical_prompt') and \
                          'conversation_history' in clova_agent.build_practical_prompt.__code__.co_varnames
        print(f"✅ Clova Agent 메모리: {'연동됨' if clova_has_memory else '연동 안됨'}")
        
        # Claude Debate Moderator 메모리 기능 확인
        debate_moderator = DebateModerator()
        claude_has_memory = hasattr(debate_moderator, 'synthesize_final_solution') and \
                           'conversation_history' in debate_moderator.synthesize_final_solution.__code__.co_varnames
        print(f"✅ Claude Moderator 메모리: {'연동됨' if claude_has_memory else '연동 안됨'}")
        
        results['agents'] = gpt_has_memory and gemini_has_memory and clova_has_memory and claude_has_memory
        
    except Exception as e:
        print(f"❌ Agent 연동 확인 오류: {str(e)}")
        results['agents'] = False
    
    # 4. API 엔드포인트 확인
    print("\n4️⃣ API 엔드포인트 점검")
    print("-" * 40)
    
    try:
        import requests
        
        # Health check
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Health 엔드포인트: {health_response.status_code}")
        
        # Chat test endpoint
        try:
            test_response = requests.get("http://localhost:8000/chat/test", timeout=5)
            print(f"✅ Chat Test 엔드포인트: {test_response.status_code}")
        except Exception:
            print("⚠️  Chat Test 엔드포인트: 서버가 실행되지 않음")
        
        results['api'] = health_response.status_code == 200
        
    except Exception:
        print("❌ API 연결 오류: 서버가 실행되지 않았을 수 있습니다")
        results['api'] = False
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 시스템 상태 요약")
    print("=" * 60)
    
    total_checks = len(results)
    passed_checks = sum(results.values())
    
    for component, status in results.items():
        icon = "✅" if status else "❌"
        component_name = {
            'rag': 'RAG 시스템',
            'memory': '메모리 시스템', 
            'agents': 'Agent 메모리 연동',
            'api': 'API 서버'
        }[component]
        
        print(f"{icon} {component_name}: {'정상' if status else '문제'}")
    
    print(f"\n🎯 전체 성공률: {passed_checks}/{total_checks} ({passed_checks/total_checks*100:.1f}%)")
    
    if passed_checks == total_checks:
        print("\n🎉🎉🎉 모든 시스템이 정상적으로 작동합니다! 🎉🎉🎉")
        print("🚀 완전한 Multi-Agent + RAG + Memory 시스템 준비 완료!")
    else:
        print(f"\n⚠️  {total_checks - passed_checks}개 시스템에 문제가 있습니다.")
        print("📝 문제가 있는 부분을 확인하고 해결해주세요.")

if __name__ == "__main__":
    asyncio.run(comprehensive_system_check())