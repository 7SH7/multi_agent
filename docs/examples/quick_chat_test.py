#!/usr/bin/env python3
"""
⚡ 빠른 챗봇 테스트 - 원하는 질문으로 바로 테스트

사용법:
    python quick_chat_test.py "컨베이어 벨트가 멈춰요"
    python quick_chat_test.py
"""

import sys
import requests
from datetime import datetime

def quick_test(user_message=None):
    # 사용자 질문 받기
    if not user_message:
        if len(sys.argv) > 1:
            user_message = sys.argv[1]
        else:
            print("🤖 Multi-Agent 챗봇 빠른 테스트")
            print("=" * 40)
            user_message = input("❓ 제조업 관련 질문을 입력하세요: ").strip()
            
            if not user_message:
                user_message = "기계에서 이상한 소음이 나요. 어떻게 해야 할까요?"
                print(f"기본 질문 사용: {user_message}")
    
    print(f"\n📤 질문: {user_message}")
    
    # 서버 상태 빠른 확인
    try:
        requests.get("http://localhost:8000/ping", timeout=2)
        print("✅ 서버 연결됨")
    except Exception:
        print("❌ 서버 실행 필요: python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
        return
    
    # 테스트 데이터 준비
    test_data = {
        "user_message": user_message,
        "issue_code": f"TEST-{datetime.now().strftime('%H%M%S')}",
        "user_id": "quick_test_user"
    }
    
    print(f"⏰ 시작: {datetime.now().strftime('%H:%M:%S')}")
    print("🔄 AI 전문가들이 협업 중... (1-3분 소요)")
    
    try:
        # API 호출
        response = requests.post(
            "http://localhost:8000/chat/test",
            json=test_data,
            timeout=180
        )
        
        print(f"⏰ 완료: {datetime.now().strftime('%H:%M:%S')}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n🎉 AI 전문가 팀 분석 완료!")
            print("=" * 50)
            
            # 간단한 결과 출력
            agents = result.get('participating_agents', [])
            print(f"👥 참여 전문가: {', '.join(agents)}")
            print(f"⚡ 처리시간: {result.get('processing_time', 0):.1f}초")
            print(f"🎯 신뢰도: {result.get('confidence_level', 0):.0%}")
            
            # 핵심 답변
            summary = result.get('executive_summary', '')
            if summary:
                print("\n💡 전문가 종합 의견:")
                print(f"   {summary}")
            
            # 즉시 조치
            actions = result.get('immediate_actions', [])
            if actions:
                print("\n🔧 즉시 조치사항:")
                for i, action in enumerate(actions[:2], 1):
                    if isinstance(action, dict):
                        print(f"   {i}. {action.get('action', 'N/A')}")
            
            # 상세 결과 안내
            print("\n📋 상세 결과는 다음에서 확인:")
            print("   • 웹 UI: http://localhost:8000/docs")
            print(f"   • 세션 ID: {result.get('session_id', 'N/A')}")
            
        else:
            print(f"❌ 오류: {response.status_code}")
            error_msg = response.text
            if len(error_msg) > 200:
                print(f"   {error_msg[:200]}...")
            else:
                print(f"   {error_msg}")
                
    except requests.exceptions.Timeout:
        print("⏰ 시간 초과 - AI가 복잡한 분석 중일 수 있습니다")
        print("💡 http://localhost:8000/docs 에서 직접 시도해보세요")
        
    except Exception as e:
        print(f"❌ 오류: {e}")

# 미리 정의된 빠른 테스트들
QUICK_TESTS = {
    "1": "컨베이어 벨트가 갑자기 멈췄어요",
    "2": "용접 부위에 균열이 발견되었습니다",
    "3": "CNC 머신 정밀도가 떨어져요",
    "4": "펌프에서 이상한 진동이 발생해요",
    "5": "제품 표면에 기포가 생깁니다"
}

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in QUICK_TESTS:
        # 숫자로 빠른 선택
        quick_test(QUICK_TESTS[sys.argv[1]])
    else:
        quick_test()