"""SQLite를 사용한 메모리 기능 테스트 (Redis 없이)"""

import asyncio
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List


class SimpleSQLiteSession:
    def __init__(self, db_path="temp_session_test.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """SQLite 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                issue_code TEXT,
                conversation_count INTEGER DEFAULT 0,
                conversations TEXT,
                created_at TEXT,
                updated_at TEXT,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def create_session(self, user_id: str, issue_code: str = "GENERAL"):
        """새 세션 생성"""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions 
            (session_id, user_id, issue_code, conversation_count, conversations, created_at, updated_at, metadata)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?)
        ''', (session_id, user_id, issue_code, "[]", now, now, "{}"))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 세션 생성: {session_id}")
        return session_id
    
    async def add_conversation(self, session_id: str, user_message: str, bot_response: str):
        """대화 추가"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 현재 세션 정보 조회
        cursor.execute('SELECT conversations, conversation_count FROM sessions WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ 세션을 찾을 수 없음: {session_id}")
            conn.close()
            return False
        
        conversations_json, current_count = result
        conversations = json.loads(conversations_json) if conversations_json else []
        
        # 새 대화 추가
        new_conversation = {
            "user_message": user_message,
            "bot_response": bot_response,
            "timestamp": datetime.now().isoformat()
        }
        conversations.append(new_conversation)
        
        # 업데이트
        new_count = current_count + 1
        updated_conversations = json.dumps(conversations, ensure_ascii=False)
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE sessions 
            SET conversations = ?, conversation_count = ?, updated_at = ?
            WHERE session_id = ?
        ''', (updated_conversations, new_count, now, session_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ 대화 저장 성공: {new_count}번째 대화")
        return True
    
    async def get_session(self, session_id: str):
        """세션 정보 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        # 결과를 딕셔너리로 변환
        columns = ['session_id', 'user_id', 'issue_code', 'conversation_count', 'conversations', 'created_at', 'updated_at', 'metadata']
        session_data = dict(zip(columns, result))
        
        # conversations JSON 파싱
        session_data['conversations'] = json.loads(session_data['conversations']) if session_data['conversations'] else []
        session_data['metadata'] = json.loads(session_data['metadata']) if session_data['metadata'] else {}
        
        return session_data


async def test_sqlite_memory():
    """SQLite를 사용한 메모리 기능 테스트"""
    print("🧪 SQLite 메모리 기능 테스트")
    print("=" * 40)
    
    try:
        # SQLite 세션 매니저 초기화
        session_manager = SimpleSQLiteSession()
        
        # 1. 첫 번째 질문 - 새 세션 생성
        print("\n1️⃣ 첫 번째 질문: '나는 김상방이야. 지금 틈이 생겨서 고민중이야.'")
        session_id = await session_manager.create_session(
            user_id="김상방",
            issue_code="GENERAL"
        )
        
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
            print(f"저장된 세션 확인 - 대화수: {saved_session['conversation_count']}")
            conversations = saved_session['conversations']
            print(f"대화 리스트: {len(conversations)}개")
            if conversations:
                print(f"첫 번째 대화: '{conversations[0]['user_message'][:30]}...'")
        
        # 2. 두 번째 질문 - 메모리 테스트
        print("\n2️⃣ 두 번째 질문: '내 이름이 머라고? 그리고 지금 무슨 문제를 고민하고 있다고?'")
        
        # 세션에서 대화 히스토리 가져오기
        current_session = await session_manager.get_session(session_id)
        if current_session:
            conversations = current_session['conversations']
            print(f"메모리에서 가져온 대화 히스토리: {len(conversations)}개")
            
            # 메모리에서 정보 추출
            name_found = False
            problem_found = False
            
            for conv in conversations:
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
            print(f"  - 총 대화수: {final_session['conversation_count']}")
            print(f"  - 대화 리스트: {len(final_session['conversations'])}개")
            
            # 전체 대화 내용 출력
            all_conversations = final_session['conversations']
            for i, conv in enumerate(all_conversations, 1):
                print(f"  대화 {i}: '{conv.get('user_message', '')[:25]}...' -> '{conv.get('bot_response', '')[:25]}...'")
        
        print("\n" + "=" * 40)
        print("🎉 SQLite 메모리 테스트 완료!")
        
        # 마지막에 메모리 기능이 정상 작동했는지 여부 반환
        final_session = await session_manager.get_session(session_id)
        if final_session and len(final_session['conversations']) >= 2:
            # 첫 번째 대화에서 이름과 문제가 있는지 확인
            first_conv = final_session['conversations'][0]
            first_user_msg = first_conv.get('user_message', '')
            name_in_first = '김상방' in first_user_msg
            problem_in_first = '고민' in first_user_msg
            
            # 두 번째 대화 응답에서 메모리가 작동했는지 확인
            second_conv = final_session['conversations'][1]
            second_bot_response = second_conv.get('bot_response', '')
            name_remembered = '김상방' in second_bot_response
            problem_remembered = '고민' in second_bot_response
            
            memory_success = name_in_first and problem_in_first and name_remembered and problem_remembered
            return memory_success
        
        return False
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_sqlite_memory())
    print(f"\n최종 결과: {'✅ 메모리 기능 정상' if result else '❌ 메모리 기능 문제'}")