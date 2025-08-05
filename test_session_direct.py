#!/usr/bin/env python3
"""SessionManager 직접 테스트"""

import asyncio
from core.session_manager import SessionManager

async def test_session_manager():
    """SessionManager 직접 테스트"""
    print("🔧 SessionManager 직접 테스트 시작...")
    
    session_manager = SessionManager()
    
    try:
        # 1. 새 세션 생성
        print("\n1️⃣ 새 세션 생성")
        session_data = await session_manager.create_session(
            user_id="test_user_001",
            issue_code="TEST-001"
        )
        session_id = session_data.session_id
        print(f"✅ 세션 생성됨: {session_id}")
        print(f"✅ 초기 대화 수: {session_data.conversation_count}")
        
        # 2. 첫 번째 대화 추가 (add_conversation_detailed 사용)
        print("\n2️⃣ 첫 번째 대화 추가")
        first_conversation = {
            'user_message': '테스트 질문: 모터가 이상해요',
            'bot_response': '모터 점검을 위해 다음 단계를 따라주세요: 1. 전원 확인, 2. 연결부 점검, 3. 소음 확인',
            'agents_used': ['GPT', 'Clova'],
            'processing_time': 15.5,
            'confidence_level': 0.85
        }
        
        result1 = await session_manager.add_conversation_detailed(session_id, first_conversation)
        print(f"✅ 첫 번째 대화 추가 결과: {result1}")
        
        # 세션 정보 다시 조회
        updated_session = await session_manager.get_session(session_id)
        print(f"✅ 업데이트된 대화 수: {updated_session.conversation_count}")
        
        # 3. 두 번째 대화 추가
        print("\n3️⃣ 두 번째 대화 추가")
        second_conversation = {
            'user_message': '이전 답변 감사합니다. 추가로 베어링도 확인해야 하나요?',
            'bot_response': '네, 베어링 상태도 중요합니다. 다음을 확인해보세요: 1. 베어링 소음, 2. 진동 여부, 3. 온도 상승',
            'agents_used': ['GPT', 'Gemini'],
            'processing_time': 12.3,
            'confidence_level': 0.90
        }
        
        result2 = await session_manager.add_conversation_detailed(session_id, second_conversation)
        print(f"✅ 두 번째 대화 추가 결과: {result2}")
        
        # 최종 세션 정보 조회
        final_session = await session_manager.get_session(session_id)
        print(f"✅ 최종 대화 수: {final_session.conversation_count}")
        
        # 4. 대화 기록 조회
        print("\n4️⃣ 대화 기록 조회")
        conversation_history = await session_manager.get_conversation_history(session_id)
        print(f"✅ 저장된 대화 기록 수: {len(conversation_history)}")
        
        for i, conv in enumerate(conversation_history, 1):
            print(f"  대화 {i}:")
            print(f"    사용자: {conv.get('user_message', 'N/A')[:50]}...")
            print(f"    봇: {conv.get('bot_response', 'N/A')[:50]}...")
            print(f"    Agent: {conv.get('agents_used', [])}")
            print(f"    시간: {conv.get('timestamp', 'N/A')}")
        
        # 5. 검증 결과
        print("\n📊 검증 결과:")
        if final_session.conversation_count == 2:
            print("🎉 대화 카운트 증가 기능: 정상")
        else:
            print(f"❌ 대화 카운트 오류: {final_session.conversation_count} (2 예상)")
            
        if len(conversation_history) == 2:
            print("🎉 대화 기록 저장 기능: 정상")
        else:
            print(f"❌ 대화 기록 수 오류: {len(conversation_history)} (2 예상)")
            
        bot_responses_saved = all('bot_response' in conv for conv in conversation_history)
        if bot_responses_saved:
            print("🎉 봇 응답 저장 기능: 정상")
        else:
            print("❌ 봇 응답 저장 누락")
            
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_session_manager())