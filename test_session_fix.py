import asyncio
from core.session_manager import SessionManager

async def test_session():
    sm = SessionManager()
    
    # 세션 생성
    sess = await sm.create_session('test_user', 'TEST_ISSUE')
    print(f'✅ 세션 생성됨: {sess.session_id}')
    print(f'   - 대화수: {sess.conversation_count}')
    
    # 세션 조회
    test_sess = await sm.get_session(sess.session_id)
    print(f'✅ 세션 조회됨: {test_sess is not None}')
    
    # 대화 추가
    add_result = await sm.add_conversation(sess.session_id, "안녕하세요", "안녕하세요! 무엇을 도와드릴까요?")
    print(f'✅ 대화 추가 결과: {add_result}')
    
    # 세션 재조회 (업데이트 확인)
    updated_sess = await sm.get_session(sess.session_id)
    if updated_sess:
        print(f'✅ 업데이트된 대화수: {updated_sess.conversation_count}')
        print(f'✅ 히스토리 개수: {len(updated_sess.metadata.get("conversation_history", []))}')
    
    # 대화 기록 조회
    history = await sm.get_conversation_history(sess.session_id)
    print(f'✅ 대화 기록 개수: {len(history)}')
    if history:
        print(f'   - 첫 번째 대화: {history[0]}')
    
    return sess.session_id

if __name__ == "__main__":
    session_id = asyncio.run(test_session())
    print(f"\n🎯 생성된 세션 ID: {session_id}")