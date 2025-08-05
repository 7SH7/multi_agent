"""Simple in-memory session store for testing without Redis"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

class SimpleMemoryStore:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
    
    async def set_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """세션 데이터 저장"""
        try:
            self.sessions[session_id] = session_data
            return True
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 데이터 조회"""
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
            if session_id in self.conversations:
                del self.conversations[session_id]
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    async def add_conversation(self, session_id: str, user_message: str, bot_response: str) -> bool:
        """대화 기록 추가"""
        try:
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            
            self.conversations[session_id].append({
                'user_message': user_message,
                'bot_response': bot_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # 세션 데이터도 업데이트
            if session_id in self.sessions:
                if 'conversation_history' not in self.sessions[session_id]:
                    self.sessions[session_id]['conversation_history'] = []
                self.sessions[session_id]['conversation_history'] = self.conversations[session_id]
                self.sessions[session_id]['conversation_count'] = len(self.conversations[session_id])
                self.sessions[session_id]['updated_at'] = datetime.now().isoformat()
            
            return True
        except Exception as e:
            print(f"Error adding conversation to session {session_id}: {e}")
            return False
    
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """대화 기록 조회"""
        return self.conversations.get(session_id, [])

# 전역 인스턴스
memory_store = SimpleMemoryStore()