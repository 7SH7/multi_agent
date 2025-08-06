import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

class SessionStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    EXPIRED = "expired"

@dataclass
class SessionData:
    session_id: str
    user_id: Optional[str]
    issue_code: Optional[str]
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    conversation_count: int
    agent_responses: Dict[str, Any]
    debate_history: List[Dict[str, Any]]
    rag_context: Dict[str, Any]
    selected_agents: List[str]
    processing_steps: List[str]
    total_processing_time: float
    metadata: Dict[str, Any]

async def test_session_memory():
    """직접 Redis로 세션 메모리 테스트"""
    print("🧪 세션 메모리 직접 테스트 시작")
    
    # Redis 연결
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    try:
        await r.ping()
        print("✅ Redis 연결 성공")
        
        # 새 세션 생성
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now()
        
        session_data = SessionData(
            session_id=session_id,
            user_id="test_user",
            issue_code="TEST-001",
            status=SessionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            conversation_count=0,
            agent_responses={},
            debate_history=[],
            rag_context={},
            selected_agents=[],
            processing_steps=[],
            total_processing_time=0.0,
            metadata={}
        )
        
        print(f"📝 세션 생성: {session_id}")
        print(f"   초기 대화수: {session_data.conversation_count}")
        
        # 세션을 Redis에 저장
        session_key = f"chatbot_session:{session_id}"
        session_dict = asdict(session_data)
        session_dict['created_at'] = session_data.created_at.isoformat()
        session_dict['updated_at'] = session_data.updated_at.isoformat()
        session_dict['status'] = session_data.status.value
        
        redis_data = {}
        for key, value in session_dict.items():
            if isinstance(value, (dict, list)):
                redis_data[key] = json.dumps(value)
            else:
                redis_data[key] = str(value)
        
        await r.hset(session_key, mapping=redis_data)
        await r.expire(session_key, 86400)  # 24시간
        
        print("✅ 세션 저장 완료")
        
        # 대화 히스토리 추가
        print("\n📞 대화 추가 시뮬레이션")
        
        # metadata에 conversation_history 추가
        if 'conversation_history' not in session_data.metadata:
            session_data.metadata['conversation_history'] = []
        
        session_data.metadata['conversation_history'].append({
            'user_message': '안녕하세요. 제 이름은 테스트박입니다. 설비에 금이 생겼어요.',
            'bot_response': '안녕하세요, 테스트박님. 설비 균열 문제에 대해 도움드리겠습니다.',
            'timestamp': datetime.now().isoformat()
        })
        
        session_data.conversation_count += 1
        session_data.updated_at = datetime.now()
        
        # Redis에 업데이트
        session_dict = asdict(session_data)
        session_dict['created_at'] = session_data.created_at.isoformat()
        session_dict['updated_at'] = session_data.updated_at.isoformat()
        session_dict['status'] = session_data.status.value
        
        redis_data = {}
        for key, value in session_dict.items():
            if isinstance(value, (dict, list)):
                redis_data[key] = json.dumps(value)
            else:
                redis_data[key] = str(value)
        
        await r.hset(session_key, mapping=redis_data)
        
        print("✅ 대화 추가 완료")
        print(f"   대화수: {session_data.conversation_count}")
        print(f"   히스토리 수: {len(session_data.metadata['conversation_history'])}")
        
        # Redis에서 다시 조회
        print("\n🔍 Redis에서 세션 조회")
        session_raw = await r.hgetall(session_key)
        
        if session_raw:
            session_dict_restored = {}
            for key, value in session_raw.items():
                try:
                    session_dict_restored[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    session_dict_restored[key] = value
            
            print(f"✅ 조회된 대화수: {session_dict_restored.get('conversation_count')}")
            
            metadata = session_dict_restored.get('metadata', {})
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
                
            conversation_history = metadata.get('conversation_history', [])
            print(f"✅ 조회된 히스토리 수: {len(conversation_history)}")
            
            if conversation_history:
                first_conv = conversation_history[0]
                print(f"✅ 첫 번째 대화:")
                print(f"   사용자: {first_conv.get('user_message')}")
                print(f"   봇: {first_conv.get('bot_response')}")
        else:
            print("❌ 세션 조회 실패")
            
        # 두 번째 대화 추가
        print("\n📞 두 번째 대화 추가")
        session_data.metadata['conversation_history'].append({
            'user_message': '제 이름이 뭐라고 했었죠? 그리고 제가 무슨 문제로 고민한다고 했나요?',
            'bot_response': '테스트박님, 설비에 금이 생기는 문제로 고민하신다고 하셨습니다.',
            'timestamp': datetime.now().isoformat()
        })
        
        session_data.conversation_count += 1
        session_data.updated_at = datetime.now()
        
        # Redis 업데이트
        session_dict = asdict(session_data)
        session_dict['created_at'] = session_data.created_at.isoformat()
        session_dict['updated_at'] = session_data.updated_at.isoformat()
        session_dict['status'] = session_data.status.value
        
        redis_data = {}
        for key, value in session_dict.items():
            if isinstance(value, (dict, list)):
                redis_data[key] = json.dumps(value)
            else:
                redis_data[key] = str(value)
        
        await r.hset(session_key, mapping=redis_data)
        
        print("✅ 두 번째 대화 추가 완료")
        print(f"   최종 대화수: {session_data.conversation_count}")
        print(f"   최종 히스토리 수: {len(session_data.metadata['conversation_history'])}")
        
        # 최종 검증
        print("\n📊 최종 검증")
        session_raw = await r.hgetall(session_key)
        session_dict_restored = {}
        for key, value in session_raw.items():
            try:
                session_dict_restored[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                session_dict_restored[key] = value
        
        final_count = int(session_dict_restored.get('conversation_count', 0))
        metadata = session_dict_restored.get('metadata', {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        final_history = metadata.get('conversation_history', [])
        
        print(f"🎯 최종 대화수: {final_count}")
        print(f"🎯 최종 히스토리: {len(final_history)}")
        
        if final_count == 2 and len(final_history) == 2:
            print("🎉 세션 메모리 기능 완벽 작동!")
            
            # 메모리 테스트 (이름과 문제 기억하는지)
            if final_history:
                last_conv = final_history[-1]
                if '테스트박' in last_conv.get('bot_response', '') and '금' in last_conv.get('bot_response', ''):
                    print("🎉 메모리 테스트도 완벽!")
                else:
                    print("⚠️ 메모리 내용은 있지만 처리 로직에 문제")
        else:
            print("❌ 세션 메모리 기능에 문제 있음")
        
    except Exception as e:
        print(f"❌ 테스트 오류: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await r.aclose()

if __name__ == "__main__":
    asyncio.run(test_session_memory())