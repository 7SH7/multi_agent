"""대화 히스토리 관리 시스템"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from models.response_models import BaseModel

class ConversationMessage(BaseModel):
    """대화 메시지 모델"""
    role: str  # 'user' or 'assistant'
    content: str
    agent_name: Optional[str] = None
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class ConversationHistory:
    """세션별 대화 히스토리 관리"""
    
    def __init__(self):
        # 메모리 기반 저장 (실제 환경에서는 Redis나 DB 사용)
        self.sessions: Dict[str, List[ConversationMessage]] = {}
        
    def create_session(self) -> str:
        """새 세션 생성"""
        session_id = f"conv_{uuid.uuid4().hex[:12]}"
        self.sessions[session_id] = []
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, 
                   agent_name: Optional[str] = None, metadata: Optional[Dict] = None) -> None:
        """메시지 추가"""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            
        message = ConversationMessage(
            role=role,
            content=content,
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        self.sessions[session_id].append(message)
    
    def get_history(self, session_id: str) -> List[ConversationMessage]:
        """세션 히스토리 조회"""
        return self.sessions.get(session_id, [])
    
    def get_messages_for_model(self, session_id: str) -> List[Dict[str, str]]:
        """모델용 메시지 형식으로 변환"""
        history = self.get_history(session_id)
        messages = []
        
        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
            
        return messages
    
    def clear_session(self, session_id: str) -> bool:
        """세션 초기화"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """세션 정보 조회"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
            
        history = self.sessions[session_id]
        return {
            "session_id": session_id,
            "message_count": len(history),
            "created_at": history[0].timestamp if history else None,
            "last_updated": history[-1].timestamp if history else None,
            "agents_used": list(set([msg.agent_name for msg in history if msg.agent_name]))
        }

# Global conversation manager instance
conversation_manager = ConversationHistory()