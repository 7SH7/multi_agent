"""Database relationship utilities for ChatbotSession, ChatbotIssue, ChatMessage"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, desc
from datetime import datetime

from models.database_models import ChatbotSession, ChatbotIssue, ChatMessage


class DatabaseRelationManager:
    """데이터베이스 관계 관리 클래스"""
    
    @staticmethod
    async def create_chatbot_issue_with_session(
        db: AsyncSession,
        issue_id: str,
        process_type: str,
        mode_type: str,
        mode_log_id: str,
        user_id: str,
        description: Optional[str] = None
    ) -> Dict[str, str]:
        """ChatbotIssue와 연결된 ChatbotSession 생성"""
        try:
            # 1. ChatbotIssue 생성 또는 조회
            result = await db.execute(
                select(ChatbotIssue).where(ChatbotIssue.issue == issue_id)
            )
            chatbot_issue = result.scalar_one_or_none()
            
            if not chatbot_issue:
                chatbot_issue = ChatbotIssue(
                    issue=issue_id,
                    processType=process_type,
                    modeType=mode_type,
                    modeLogId=mode_log_id,
                    description=description
                )
                db.add(chatbot_issue)
                await db.flush()  # ID 생성을 위해 flush
            
            # 2. ChatbotSession 생성
            session_id = f"sess_{issue_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            chatbot_session = ChatbotSession(
                chatbotSessionId=session_id,
                issue=issue_id,  # FK 설정
                userId=user_id
            )
            db.add(chatbot_session)
            
            await db.commit()
            
            return {
                "issue_id": issue_id,
                "session_id": session_id,
                "status": "created"
            }
            
        except Exception as e:
            await db.rollback()
            raise Exception(f"ChatbotIssue와 Session 생성 실패: {str(e)}")
    
    @staticmethod
    async def add_message_to_session(
        db: AsyncSession,
        session_id: str,
        message_content: str,
        sender: str,  # 'user' or 'bot'
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """세션에 메시지 추가 (Issue와도 자동 연결)"""
        try:
            # 1. Session 조회 (Issue 정보 포함)
            result = await db.execute(
                select(ChatbotSession)
                .options(selectinload(ChatbotSession.chatbot_issue))
                .where(ChatbotSession.chatbotSessionId == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                raise Exception(f"Session {session_id}을 찾을 수 없습니다")
            
            # 2. 메시지 ID 생성
            if not message_id:
                message_id = f"msg_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # 3. ChatMessage 생성 (Session과 Issue 모두 연결)
            chat_message = ChatMessage(
                chatMessageId=message_id,
                chatMessage=message_content,
                chatbotSessionId=session_id,  # FK to ChatbotSession
                issue=session.issue,  # FK to ChatbotIssue (Session에서 가져옴)
                sender=sender
            )
            db.add(chat_message)
            
            await db.commit()
            
            return {
                "message_id": message_id,
                "session_id": session_id,
                "issue_id": session.issue,
                "sender": sender,
                "status": "added"
            }
            
        except Exception as e:
            await db.rollback()
            raise Exception(f"메시지 추가 실패: {str(e)}")
    
    @staticmethod
    async def get_issue_with_sessions_and_messages(
        db: AsyncSession,
        issue_id: str
    ) -> Optional[Dict[str, Any]]:
        """Issue와 연결된 모든 Session, Message 조회"""
        try:
            result = await db.execute(
                select(ChatbotIssue)
                .options(
                    selectinload(ChatbotIssue.sessions).selectinload(ChatbotSession.messages),
                    selectinload(ChatbotIssue.messages)
                )
                .where(ChatbotIssue.issue == issue_id)
            )
            issue = result.scalar_one_or_none()
            
            if not issue:
                return None
            
            # 데이터 변환
            sessions_data = []
            for session in issue.sessions:
                session_messages = [
                    {
                        "message_id": msg.chatMessageId,
                        "content": msg.chatMessage,
                        "sender": msg.sender,
                        "sent_at": msg.sentAt.isoformat() if msg.sentAt else None
                    }
                    for msg in session.messages
                ]
                
                sessions_data.append({
                    "session_id": session.chatbotSessionId,
                    "user_id": session.userId,
                    "started_at": session.startedAt.isoformat() if session.startedAt else None,
                    "ended_at": session.endedAt.isoformat() if session.endedAt else None,
                    "is_terminated": session.isTerminated,
                    "is_reported": session.isReported,
                    "message_count": len(session_messages),
                    "messages": session_messages
                })
            
            return {
                "issue_id": issue.issue,
                "process_type": issue.processType,
                "mode_type": issue.modeType,
                "mode_log_id": issue.modeLogId,
                "description": issue.description,
                "created_at": issue.createdAt.isoformat() if issue.createdAt else None,
                "updated_at": issue.updatedAt.isoformat() if issue.updatedAt else None,
                "session_count": len(sessions_data),
                "total_messages": len(issue.messages),
                "sessions": sessions_data
            }
            
        except Exception as e:
            raise Exception(f"Issue 상세 조회 실패: {str(e)}")
    
    @staticmethod
    async def get_session_with_messages(
        db: AsyncSession,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Session과 연결된 모든 Message, Issue 정보 조회"""
        try:
            result = await db.execute(
                select(ChatbotSession)
                .options(
                    selectinload(ChatbotSession.messages),
                    selectinload(ChatbotSession.chatbot_issue)
                )
                .where(ChatbotSession.chatbotSessionId == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return None
            
            # 메시지 데이터 변환
            messages = [
                {
                    "message_id": msg.chatMessageId,
                    "content": msg.chatMessage,
                    "sender": msg.sender,
                    "sent_at": msg.sentAt.isoformat() if msg.sentAt else None
                }
                for msg in sorted(session.messages, key=lambda x: x.sentAt or datetime.min)
            ]
            
            # Issue 정보
            issue_info = None
            if session.chatbot_issue:
                issue_info = {
                    "issue_id": session.chatbot_issue.issue,
                    "process_type": session.chatbot_issue.processType,
                    "mode_type": session.chatbot_issue.modeType,
                    "mode_log_id": session.chatbot_issue.modeLogId,
                    "description": session.chatbot_issue.description
                }
            
            return {
                "session_id": session.chatbotSessionId,
                "user_id": session.userId,
                "started_at": session.startedAt.isoformat() if session.startedAt else None,
                "ended_at": session.endedAt.isoformat() if session.endedAt else None,
                "is_terminated": session.isTerminated,
                "is_reported": session.isReported,
                "message_count": len(messages),
                "messages": messages,
                "issue": issue_info
            }
            
        except Exception as e:
            raise Exception(f"Session 상세 조회 실패: {str(e)}")
    
    @staticmethod
    async def get_messages_by_issue(
        db: AsyncSession,
        issue_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """특정 Issue와 연결된 모든 메시지 조회 (학습 데이터용)"""
        try:
            result = await db.execute(
                select(ChatMessage)
                .options(selectinload(ChatMessage.session))
                .where(ChatMessage.issue == issue_id)
                .order_by(desc(ChatMessage.sentAt))
                .offset(offset)
                .limit(limit)
            )
            messages = result.scalars().all()
            
            return [
                {
                    "message_id": msg.chatMessageId,
                    "content": msg.chatMessage,
                    "sender": msg.sender,
                    "sent_at": msg.sentAt.isoformat() if msg.sentAt else None,
                    "session_id": msg.chatbotSessionId,
                    "session_user_id": msg.session.userId if msg.session else None
                }
                for msg in messages
            ]
            
        except Exception as e:
            raise Exception(f"Issue별 메시지 조회 실패: {str(e)}")
    
    @staticmethod
    async def close_session(
        db: AsyncSession,
        session_id: str,
        is_terminated: bool = True
    ) -> bool:
        """세션 종료 처리"""
        try:
            result = await db.execute(
                select(ChatbotSession).where(ChatbotSession.chatbotSessionId == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return False
            
            session.endedAt = datetime.now()
            session.isTerminated = is_terminated
            
            await db.commit()
            return True
            
        except Exception as e:
            await db.rollback()
            raise Exception(f"세션 종료 실패: {str(e)}")


# 편의 함수들
async def create_issue_session(
    db: AsyncSession,
    issue_id: str,
    process_type: str,
    mode_type: str,
    mode_log_id: str,
    user_id: str,
    description: Optional[str] = None
) -> Dict[str, str]:
    """Issue와 Session 생성 편의 함수"""
    manager = DatabaseRelationManager()
    return await manager.create_chatbot_issue_with_session(
        db, issue_id, process_type, mode_type, mode_log_id, user_id, description
    )


async def add_conversation_message(
    db: AsyncSession,
    session_id: str,
    message_content: str,
    sender: str
) -> Dict[str, Any]:
    """대화 메시지 추가 편의 함수"""
    manager = DatabaseRelationManager()
    return await manager.add_message_to_session(db, session_id, message_content, sender)