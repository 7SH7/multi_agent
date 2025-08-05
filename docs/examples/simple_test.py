#!/usr/bin/env python3
"""
🤖 Multi-Agent 챗봇 간단 테스트 스크립트

사용법:
    python simple_test.py
"""

import requests
from datetime import datetime

def test_chatbot():
    print("🚀 Multi-Agent 챗봇 테스트 시작!")
    print("=" * 50)
    
    # 서버 상태 확인
    try:
        ping = requests.get("http://localhost:8000/ping", timeout=3)
        if ping.status_code != 200:
            print("❌ 서버가 실행되지 않았습니다!")
            print("다음 명령어로 서버를 시작하세요:")
            print("python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
            return
        print("✅ 서버 실행 중")
    except Exception:
        print("❌ 서버 연결 실패! localhost:8000에서 서버를 시작해주세요.")
        return
    
    # 테스트 시나리오들
    test_cases = [
        {
            "name": "🔧 기계 고장 문제",
            "data": {
                "user_message": "컨베이어 벨트가 갑자기 멈췄어요. 긴급히 해결해야 합니다!",
                "issue_code": "CONV-STOP-001",
                "user_id": "operator_01"
            }
        },
        {
            "name": "⚠️ 안전 문제", 
            "data": {
                "user_message": "작업 중 화학물질 냄새가 나는데 안전할까요?",
                "issue_code": "SAFETY-CHEM-002", 
                "user_id": "worker_02"
            }
        },
        {
            "name": "🔍 품질 문제",
            "data": {
                "user_message": "제품에 균열이 자꾸 생겨요. 원인을 찾아주세요.",
                "issue_code": "QUALITY-CRACK-003",
                "user_id": "qc_03"
            }
        }
    ]
    
    # 사용자가 시나리오 선택
    print("\n📋 테스트 시나리오를 선택하세요:")
    for i, case in enumerate(test_cases, 1):
        print(f"  {i}. {case['name']}")
        print(f"     질문: {case['data']['user_message']}")
    
    try:
        choice = int(input("\n선택 (1-3): ")) - 1
        if choice < 0 or choice >= len(test_cases):
            print("잘못된 선택입니다. 1번을 사용합니다.")
            choice = 0
    except Exception:
        print("잘못된 입력입니다. 1번을 사용합니다.")
        choice = 0
    
    selected_case = test_cases[choice]
    print(f"\n{selected_case['name']} 테스트 시작!")
    print(f"질문: {selected_case['data']['user_message']}")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%H:%M:%S')}")
    print("\n🤖 AI 전문가들이 분석 중입니다...")
    print("💡 GPT → Gemini → Claude 순으로 협업합니다. 잠시만 기다려주세요!")
    
    # API 호출
    try:
        response = requests.post(
            "http://localhost:8000/chat/test",
            json=selected_case['data'],
            headers={"Content-Type": "application/json"},
            timeout=180  # 3분 타임아웃
        )
        
        end_time = datetime.now().strftime('%H:%M:%S')
        print(f"⏰ 완료 시간: {end_time}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "🎉" * 20)
            print("SUCCESS! AI 전문가 팀 분석 완료!")
            print("🎉" * 20)
            
            # 핵심 정보 출력
            print("\n📊 분석 결과 요약:")
            print(f"   🆔 세션 ID: {result.get('session_id', 'N/A')}")
            print(f"   🤖 참여 전문가: {', '.join(result.get('participating_agents', []))}")
            print(f"   ⚡ 처리 시간: {result.get('processing_time', 0):.1f}초")
            print(f"   🎯 신뢰도: {result.get('confidence_level', 0):.0%}")
            print(f"   💬 토론 라운드: {result.get('debate_rounds', 0)}")
            
            # 핵심 해결책
            print("\n📋 전문가 종합 분석:")
            summary = result.get('executive_summary', '')
            if summary:
                print(f"   {summary}")
            
            # 즉시 조치사항
            print("\n🛠️ 즉시 조치사항:")
            actions = result.get('immediate_actions', [])
            if actions:
                for i, action in enumerate(actions[:3], 1):
                    if isinstance(action, dict):
                        priority = action.get('priority', 'medium').upper()
                        action_text = action.get('action', 'N/A')
                        time_est = action.get('time', 'N/A')
                        print(f"   {i}. [{priority}] {action_text} (소요: {time_est})")
            else:
                print("   (상세 분석 필요)")
            
            # 비용 추정
            print("\n💰 예상 비용:")
            cost = result.get('cost_estimation', {})
            if cost and any(cost.values()):
                print(f"   부품비: {cost.get('parts', 'N/A')}")
                print(f"   인건비: {cost.get('labor', 'N/A')}")
                print(f"   총 비용: {cost.get('total', 'N/A')}")
            else:
                print("   현장 확인 후 산정 예정")
            
            # 안전 수칙
            safety = result.get('safety_precautions', [])
            if safety:
                print("\n⚠️ 안전 수칙:")
                for i, rule in enumerate(safety[:3], 1):
                    print(f"   {i}. {rule}")
            
            print("\n✅ 완료! 전체 JSON 응답을 보려면 다음 URL을 확인하세요:")
            print("   http://localhost:8000/docs")
            
        else:
            print("\n❌ 오류 발생!")
            print(f"   HTTP 상태: {response.status_code}")
            print(f"   오류 내용: {response.text}")
            
    except requests.exceptions.Timeout:
        print("\n⏰ 타임아웃 발생 (3분 초과)")
        print("   💡 AI 전문가들이 복잡한 분석을 진행 중일 수 있습니다.")
        print("   💡 브라우저에서 http://localhost:8000/docs 에서 다시 시도해보세요.")
        
    except Exception as e:
        print(f"\n❌ 예외 발생: {str(e)}")

if __name__ == "__main__":
    test_chatbot()