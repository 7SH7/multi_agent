#!/usr/bin/env python3
"""API 키가 설정된 상태에서 빠른 테스트"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.gpt_agent import GPTAgent
from agents.gemini_agent import GeminiAgent
from agents.clova_agent import ClovaAgent
from models.agent_state import AgentState
from datetime import datetime

async def test_individual_agents():
    """각 Agent 개별 테스트"""
    print("🤖 개별 Agent 테스트...")
    
    # 테스트 상태 생성
    test_state = AgentState()
    test_state.update({
        'session_id': 'test_session_001',
        'user_message': '도어에 스크래치가 생겼는데 어떻게 해결하면 좋을까요?',
        'issue_code': 'ASBP-DOOR-SCRATCH-20240722001',
        'conversation_history': [],
        'processing_steps': [],
        'timestamp': datetime.now()
    })
    
    agents = [
        ("GPT Agent", GPTAgent()),
        ("Gemini Agent", GeminiAgent()),  
        ("Clova Agent", ClovaAgent())
    ]
    
    results = []
    
    for agent_name, agent in agents:
        try:
            print(f"\n🔄 {agent_name} 테스트 중...")
            
            # 안전한 분석 실행 (재시도 포함)
            response = await agent.safe_analyze(test_state)
            
            if response.error:
                print(f"❌ {agent_name} 실패: {response.error}")
                results.append((agent_name, False, response.error))
            else:
                print(f"✅ {agent_name} 성공!")
                print(f"   - 신뢰도: {response.confidence:.2f}")
                print(f"   - 처리시간: {response.processing_time:.2f}초")
                print(f"   - 응답 길이: {len(response.response)}자")
                if response.token_usage:
                    total_tokens = response.token_usage.get('total_tokens', 0)
                    print(f"   - 토큰 사용: {total_tokens}")
                
                # 응답 미리보기
                preview = response.response[:100].replace('\n', ' ')
                print(f"   - 응답 미리보기: {preview}...")
                
                results.append((agent_name, True, None))
                
        except Exception as e:
            print(f"💥 {agent_name} 예외 발생: {str(e)}")
            results.append((agent_name, False, str(e)))
    
    return results

def test_api_keys():
    """API 키 유효성 테스트"""
    print("🔑 API 키 설정 확인...")
    
    from config.settings import LLM_CONFIGS
    
    api_keys = {
        "OpenAI": LLM_CONFIGS["openai"]["api_key"],
        "Google (Gemini)": LLM_CONFIGS["google"]["api_key"], 
        "Naver (Clova)": LLM_CONFIGS["naver"]["api_key"],
        "Anthropic": LLM_CONFIGS["anthropic"]["api_key"]
    }
    
    for service, key in api_keys.items():
        if key and not key.startswith('your_') and len(key) > 10:
            print(f"✅ {service}: 설정됨 ({key[:10]}...)")
        else:
            print(f"❌ {service}: 미설정 또는 기본값")
    
    return all(key and not key.startswith('your_') and len(key) > 10 
              for key in api_keys.values())

async def main():
    """메인 테스트"""
    print("🚀 Multi-Agent 챗봇 API 키 테스트")
    print("=" * 60)
    
    # 1. API 키 확인
    keys_ok = test_api_keys()
    if not keys_ok:
        print("\n⚠️  일부 API 키가 설정되지 않았습니다.")
        print("하지만 설정된 API 키로 테스트를 계속 진행합니다.\n")
    
    print("\n" + "=" * 60)
    
    # 2. 개별 Agent 테스트
    results = await test_individual_agents()
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    
    successful = 0
    for agent_name, success, error in results:
        status = "✅ 성공" if success else f"❌ 실패: {error}"
        print(f"  - {agent_name}: {status}")
        if success:
            successful += 1
    
    print(f"\n🎯 성공률: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    
    if successful > 0:
        print("\n🎉 일부 또는 모든 Agent가 정상 작동합니다!")
        print("💡 이제 full workflow 테스트나 API 서버 테스트를 해볼 수 있습니다.")
    else:
        print("\n⚠️  모든 Agent 테스트가 실패했습니다.")
        print("💡 API 키 설정이나 네트워크 연결을 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(main())