import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.session_manager import SessionManager

async def test_simple_memory():
    """간단한 메모리 기능 테스트"""
    print("🧪 간단한 메모리 기능 테스트")
    print("=" * 40)
    
    try:
        # SessionManager 초기화
        session_manager = SessionManager()
        print("SessionManager 초기화 완료")
        
        # 1. 첫 번째 질문 - 새 세션 생성
        print("\n1️⃣ 첫 번째 질문: '나는 김상방이야. 지금 틈이 생겨서 고민중이야.'")
        session_data = await session_manager.create_session(
            user_id="김상방",
            issue_code="GENERAL"
        )
        session_id = session_data.session_id
        print(f"✅ 세션 생성 성공: {session_id}")
        
        # 첫 번째 대화 저장
        user_message_1 = "나는 김상방이야. 지금 틈이 생겨서 고민중이야."
        bot_response_1 = "안녕하세요 김상방님! 틈이 생겨서 고민이시는군요. 어떤 고민인지 자세히 말씀해주시면 도움을 드릴 수 있을 것 같습니다."
        
        save_success = await session_manager.add_conversation(
            session_id, user_message_1, bot_response_1
        )
        print(f"첫 번째 대화 저장: {'✅ 성공' if save_success else '❌ 실패'}")
        
        # 세션 확인
        saved_session = await session_manager.get_session(session_id)
        if saved_session:
            print(f"저장된 세션 확인 - 대화수: {saved_session.conversation_count}")
            history = saved_session.metadata.get('conversation_history', [])
            print(f"대화 히스토리: {len(history)}개")
            if history:
                print(f"첫 번째 대화: '{history[0].get('user_message', '')[:30]}...'")
        
        # 2. 두 번째 질문 - 메모리 테스트
        print("\n2️⃣ 두 번째 질문: '내 이름이 머라고? 그리고 지금 무슨 문제를 고민하고 있다고?'")
        
        # 세션에서 대화 히스토리 가져오기
        current_session = await session_manager.get_session(session_id)
        if current_session:
            conversation_history = current_session.metadata.get('conversation_history', [])
            print(f"메모리에서 가져온 대화 히스토리: {len(conversation_history)}개")
            
            # 메모리에서 정보 추출
            name_found = False
            problem_found = False
            
            for conv in conversation_history:
                user_msg = conv.get('user_message', '')
                if '김상방' in user_msg:
                    name_found = True
                if '고민' in user_msg:
                    problem_found = True
            
            print(f"메모리 테스트 결과:")
            print(f"  - 이름 기억: {'✅' if name_found else '❌'}")
            print(f"  - 문제 기억: {'✅' if problem_found else '❌'}")
            
            # 메모리 기반 응답 생성
            if name_found and problem_found:
                bot_response_2 = "네, 당신의 이름은 김상방이고, 지금 틈이 생겨서 고민중이라고 말씀하셨습니다."
                print(f"✅ 메모리 기반 응답 생성 성공")
            else:
                bot_response_2 = "죄송합니다, 이전 대화 내용을 기억하지 못하겠습니다."
                print(f"❌ 메모리 기반 응답 생성 실패")
            
            # 두 번째 대화 저장
            user_message_2 = "내 이름이 머라고? 그리고 지금 무슨 문제를 고민하고 있다고?"
            save_success_2 = await session_manager.add_conversation(
                session_id, user_message_2, bot_response_2
            )
            print(f"두 번째 대화 저장: {'✅ 성공' if save_success_2 else '❌ 실패'}")
            
            # 최종 검증
            print(f"\n🎯 최종 메모리 테스트 결과: {'✅ 성공' if (name_found and problem_found) else '❌ 실패'}")
            
        else:
            print("❌ 세션을 찾을 수 없습니다")
            
        # 3. 최종 세션 상태
        final_session = await session_manager.get_session(session_id)
        if final_session:
            print(f"\n📊 최종 세션 상태:")
            print(f"  - 총 대화수: {final_session.conversation_count}")
            print(f"  - 대화 히스토리: {len(final_session.metadata.get('conversation_history', []))}개")
            print(f"  - 세션 상태: {final_session.status.value}")
            
            # 전체 대화 내용 출력
            all_history = final_session.metadata.get('conversation_history', [])
            for i, conv in enumerate(all_history, 1):
                print(f"  대화 {i}: '{conv.get('user_message', '')[:25]}...' -> '{conv.get('bot_response', '')[:25]}...'")
        
        print("\n" + "=" * 40)
        print("🎉 메모리 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_memory())