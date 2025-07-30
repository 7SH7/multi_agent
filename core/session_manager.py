import redis.asyncio as redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from config.settings import REDIS_CONFIG


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


class SessionManager:
    def __init__(self):
        self.redis_client = None
        self.session_timeout = timedelta(hours=24)

    async def _get_redis_client(self):
        if self.redis_client is None:
            self.redis_client = redis.Redis(
                host=REDIS_CONFIG['host'],
                port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'],
                password=REDIS_CONFIG.get('password'),
                decode_responses=True
            )
        return self.redis_client

    async def create_session(self, user_id: str = None, issue_code: str = None) -> SessionData:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        session_data = SessionData(
            session_id=session_id,
            user_id=user_id,
            issue_code=issue_code,
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

        await self._save_session(session_data)
        return session_data

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        redis_client = await self._get_redis_client()
        session_key = f"chatbot_session:{session_id}"

        try:
            session_raw = await redis_client.hgetall(session_key)
            if not session_raw:
                return None

            # Convert Redis data back to SessionData
            session_dict = {}
            for key, value in session_raw.items():
                try:
                    session_dict[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    session_dict[key] = value

            # Handle datetime conversion
            if 'created_at' in session_dict:
                session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
            if 'updated_at' in session_dict:
                session_dict['updated_at'] = datetime.fromisoformat(session_dict['updated_at'])

            # Handle enum conversion
            if 'status' in session_dict:
                session_dict['status'] = SessionStatus(session_dict['status'])

            return SessionData(**session_dict)

        except Exception as e:
            print(f"Error retrieving session {session_id}: {e}")
            return None

    async def update_session(self, session_data: SessionData) -> bool:
        session_data.updated_at = datetime.now()
        return await self._save_session(session_data)

    async def _save_session(self, session_data: SessionData) -> bool:
        redis_client = await self._get_redis_client()
        session_key = f"chatbot_session:{session_data.session_id}"

        try:
            # Convert SessionData to dict and handle special types
            session_dict = asdict(session_data)
            session_dict['created_at'] = session_data.created_at.isoformat()
            session_dict['updated_at'] = session_data.updated_at.isoformat()
            session_dict['status'] = session_data.status.value

            # Convert to Redis format
            redis_data = {}
            for key, value in session_dict.items():
                if isinstance(value, (dict, list)):
                    redis_data[key] = json.dumps(value)
                else:
                    redis_data[key] = str(value)

            await redis_client.hset(session_key, mapping=redis_data)
            await redis_client.expire(session_key, int(self.session_timeout.total_seconds()))

            return True

        except Exception as e:
            print(f"Error saving session {session_data.session_id}: {e}")
            return False

    async def end_session(self, session_id: str) -> bool:
        session_data = await self.get_session(session_id)
        if not session_data:
            return False

        session_data.status = SessionStatus.COMPLETED
        return await self.update_session(session_data)

    async def delete_session(self, session_id: str) -> bool:
        redis_client = await self._get_redis_client()
        session_key = f"chatbot_session:{session_id}"

        try:
            result = await redis_client.delete(session_key)
            return bool(result)
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    async def list_active_sessions(self, user_id: str = None) -> List[SessionData]:
        redis_client = await self._get_redis_client()

        try:
            # Get all session keys
            pattern = "chatbot_session:*"
            keys = await redis_client.keys(pattern)

            sessions = []
            for key in keys:
                session_id = key.split(":")[-1]
                session_data = await self.get_session(session_id)

                if session_data and session_data.status == SessionStatus.ACTIVE:
                    if user_id is None or session_data.user_id == user_id:
                        sessions.append(session_data)

            return sessions

        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []

    async def cleanup_expired_sessions(self) -> int:
        redis_client = await self._get_redis_client()
        cleaned_count = 0

        try:
            pattern = "chatbot_session:*"
            keys = await redis_client.keys(pattern)

            for key in keys:
                session_id = key.split(":")[-1]
                session_data = await self.get_session(session_id)

                if session_data:
                    # Check if session is expired
                    time_since_update = datetime.now() - session_data.updated_at
                    if time_since_update > self.session_timeout:
                        session_data.status = SessionStatus.EXPIRED
                        await self.update_session(session_data)
                        cleaned_count += 1

            return cleaned_count

        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            return 0

    async def increment_conversation_count(self, session_id: str) -> bool:
        """세션의 대화 카운트 증가"""
        session_data = await self.get_session(session_id)
        if not session_data:
            return False
        
        session_data.conversation_count += 1
        return await self.update_session(session_data)

    async def add_conversation(self, session_id: str, user_message: str, bot_response: str) -> bool:
        """세션에 대화 기록 추가"""
        session_data = await self.get_session(session_id)
        if not session_data:
            return False
        
        # 대화 기록을 metadata에 저장
        if 'conversation_history' not in session_data.metadata:
            session_data.metadata['conversation_history'] = []
        
        session_data.metadata['conversation_history'].append({
            'user_message': user_message,
            'bot_response': bot_response,
            'timestamp': datetime.now().isoformat()
        })
        
        session_data.conversation_count += 1
        return await self.update_session(session_data)

    async def get_session_stats(self) -> Dict[str, Any]:
        redis_client = await self._get_redis_client()

        try:
            pattern = "chatbot_session:*"
            keys = await redis_client.keys(pattern)

            stats = {
                'total_sessions': len(keys),
                'active_sessions': 0,
                'completed_sessions': 0,
                'error_sessions': 0,
                'expired_sessions': 0
            }

            for key in keys:
                session_id = key.split(":")[-1]
                session_data = await self.get_session(session_id)

                if session_data:
                    if session_data.status == SessionStatus.ACTIVE:
                        stats['active_sessions'] += 1
                    elif session_data.status == SessionStatus.COMPLETED:
                        stats['completed_sessions'] += 1
                    elif session_data.status == SessionStatus.ERROR:
                        stats['error_sessions'] += 1
                    elif session_data.status == SessionStatus.EXPIRED:
                        stats['expired_sessions'] += 1

            return stats

        except Exception as e:
            print(f"Error getting session stats: {e}")
            return {'error': str(e)}