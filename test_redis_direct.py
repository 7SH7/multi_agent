"""Redis 연결 직접 테스트"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.session_manager import SessionManager

async def test_redis_connection():
    print("=== Redis 연결 및 세션 저장 테스트 ===")
    
    session_manager = SessionManager()
    
    # 1. 새 세션 생성
    print("\n1. 새 세션 생성...")
    session_data = await session_manager.create_session(
        user_id="test_user",
        issue_code="TEST"
    )
    print(f"생성된 세션 ID: {session_data.session_id}")
    
    # 2. 세션 조회
    print("\n2. 세션 조회...")
    retrieved_session = await session_manager.get_session(session_data.session_id)
    print(f"조회된 세션: {retrieved_session.session_id if retrieved_session else 'None'}")
    print(f"대화 수: {retrieved_session.conversation_count if retrieved_session else 'None'}")
    
    # 3. 대화 추가
    print("\n3. 대화 추가...")
    success = await session_manager.add_conversation(
        session_data.session_id,
        "테스트 사용자 메시지",
        "테스트 봇 응답"
    )
    print(f"대화 추가 결과: {success}")
    
    # 4. 업데이트된 세션 조회
    print("\n4. 업데이트된 세션 조회...")
    updated_session = await session_manager.get_session(session_data.session_id)
    if updated_session:
        print(f"업데이트된 대화 수: {updated_session.conversation_count}")
        print(f"메타데이터: {updated_session.metadata}")
    else:
        print("업데이트된 세션을 찾을 수 없음")
    
    # 5. 대화 기록 조회
    print("\n5. 대화 기록 조회...")
    history = await session_manager.get_conversation_history(session_data.session_id)
    print(f"대화 기록 수: {len(history)}")
    for i, conv in enumerate(history):
        print(f"  {i+1}. 사용자: {conv.get('user_message', '')}")
        print(f"     봇: {conv.get('bot_response', '')}")

if __name__ == "__main__":
    asyncio.run(test_redis_connection())