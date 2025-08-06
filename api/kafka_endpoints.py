"""Kafka 관리 API 엔드포인트"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from services.kafka_manager import kafka_manager
from services.kafka_consumer import kafka_issue_consumer
from models.database_models import ChatbotIssue, ChatbotSession, ChatMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from utils.database import get_async_db
from utils.database_relations import DatabaseRelationManager

logger = logging.getLogger(__name__)

kafka_router = APIRouter(prefix="/api/kafka", tags=["Kafka Management"])


@kafka_router.get("/status")
async def get_kafka_status() -> Dict[str, Any]:
    """Kafka Consumer 상태 조회"""
    try:
        status = kafka_manager.get_status()
        return {
            "status": "success",
            "data": status,
            "message": "Kafka Consumer 상태 조회 성공"
        }
    except Exception as e:
        logger.error(f"Kafka 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")


@kafka_router.post("/start")
async def start_kafka_consumer() -> Dict[str, Any]:
    """Kafka Consumer 수동 시작"""
    try:
        if kafka_manager.is_running:
            return {
                "status": "warning",
                "message": "Kafka Consumer가 이미 실행 중입니다"
            }
        
        await kafka_manager.start()
        return {
            "status": "success",
            "message": "Kafka Consumer 시작 완료"
        }
    except Exception as e:
        logger.error(f"Kafka Consumer 시작 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시작 실패: {str(e)}")


@kafka_router.post("/stop")
async def stop_kafka_consumer() -> Dict[str, Any]:
    """Kafka Consumer 수동 중지"""
    try:
        if not kafka_manager.is_running:
            return {
                "status": "warning",
                "message": "Kafka Consumer가 이미 중지되어 있습니다"
            }
        
        await kafka_manager.stop()
        return {
            "status": "success",
            "message": "Kafka Consumer 중지 완료"
        }
    except Exception as e:
        logger.error(f"Kafka Consumer 중지 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"중지 실패: {str(e)}")


@kafka_router.post("/restart")
async def restart_kafka_consumer() -> Dict[str, Any]:
    """Kafka Consumer 재시작"""
    try:
        if kafka_manager.is_running:
            await kafka_manager.stop()
        
        await kafka_manager.start()
        return {
            "status": "success",
            "message": "Kafka Consumer 재시작 완료"
        }
    except Exception as e:
        logger.error(f"Kafka Consumer 재시작 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"재시작 실패: {str(e)}")


@kafka_router.get("/issues")
async def get_chatbot_issues(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """ChatbotIssue 목록 조회"""
    try:
        # 총 개수 조회
        count_result = await db.execute(select(func.count(ChatbotIssue.issue)))
        total_count = count_result.scalar()
        
        # 이슈 목록 조회
        result = await db.execute(
            select(ChatbotIssue)
            .offset(offset)
            .limit(limit)
            .order_by(ChatbotIssue.issue)
        )
        issues = result.scalars().all()
        
        # 결과 변환
        issues_data = []
        for issue in issues:
            issues_data.append({
                "issue": issue.issue,
                "processType": issue.processType,
                "modeType": issue.modeType,
                "modeLogId": issue.modeLogId
            })
        
        return {
            "status": "success",
            "data": {
                "issues": issues_data,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            },
            "message": f"ChatbotIssue {len(issues_data)}개 조회 성공"
        }
        
    except Exception as e:
        logger.error(f"ChatbotIssue 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@kafka_router.get("/issues/{issue_id}")
async def get_chatbot_issue(
    issue_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """특정 ChatbotIssue 조회"""
    try:
        result = await db.execute(
            select(ChatbotIssue).where(ChatbotIssue.issue == issue_id)
        )
        issue = result.scalar_one_or_none()
        
        if not issue:
            raise HTTPException(status_code=404, detail="ChatbotIssue를 찾을 수 없습니다")
        
        return {
            "status": "success",
            "data": {
                "issue": issue.issue,
                "processType": issue.processType,
                "modeType": issue.modeType,
                "modeLogId": issue.modeLogId
            },
            "message": "ChatbotIssue 조회 성공"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ChatbotIssue 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@kafka_router.delete("/issues/{issue_id}")
async def delete_chatbot_issue(
    issue_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """ChatbotIssue 삭제"""
    try:
        result = await db.execute(
            select(ChatbotIssue).where(ChatbotIssue.issue == issue_id)
        )
        issue = result.scalar_one_or_none()
        
        if not issue:
            raise HTTPException(status_code=404, detail="ChatbotIssue를 찾을 수 없습니다")
        
        await db.delete(issue)
        await db.commit()
        
        return {
            "status": "success",
            "message": f"ChatbotIssue '{issue_id}' 삭제 완료"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ChatbotIssue 삭제 실패: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")


# 관계형 데이터 조회 API
@kafka_router.get("/issues/{issue_id}/details")
async def get_issue_details(
    issue_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Issue와 연결된 모든 Session, Message 상세 조회"""
    try:
        manager = DatabaseRelationManager()
        issue_details = await manager.get_issue_with_sessions_and_messages(db, issue_id)
        
        if not issue_details:
            raise HTTPException(status_code=404, detail="ChatbotIssue를 찾을 수 없습니다")
        
        return {
            "status": "success",
            "data": issue_details,
            "message": "Issue 상세 정보 조회 성공"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Issue 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@kafka_router.get("/sessions/{session_id}/details")
async def get_session_details(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Session과 연결된 모든 Message, Issue 정보 상세 조회"""
    try:
        manager = DatabaseRelationManager()
        session_details = await manager.get_session_with_messages(db, session_id)
        
        if not session_details:
            raise HTTPException(status_code=404, detail="ChatbotSession을 찾을 수 없습니다")
        
        return {
            "status": "success",
            "data": session_details,
            "message": "Session 상세 정보 조회 성공"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@kafka_router.get("/issues/{issue_id}/messages")
async def get_issue_messages(
    issue_id: str,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Issue와 연결된 모든 메시지 조회 (학습 데이터용)"""
    try:
        manager = DatabaseRelationManager()
        messages = await manager.get_messages_by_issue(db, issue_id, limit, offset)
        
        return {
            "status": "success",
            "data": {
                "issue_id": issue_id,
                "messages": messages,
                "count": len(messages),
                "limit": limit,
                "offset": offset
            },
            "message": f"Issue '{issue_id}' 메시지 {len(messages)}개 조회 성공"
        }
        
    except Exception as e:
        logger.error(f"Issue 메시지 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")


@kafka_router.post("/test/create-issue-session")
async def create_test_issue_session(
    issue_id: str,
    process_type: str,
    mode_type: str,
    mode_log_id: str,
    user_id: str,
    description: str = None,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """테스트용: Issue와 Session 생성"""
    try:
        manager = DatabaseRelationManager()
        result = await manager.create_chatbot_issue_with_session(
            db, issue_id, process_type, mode_type, mode_log_id, user_id, description
        )
        
        return {
            "status": "success",
            "data": result,
            "message": "Issue와 Session 생성 성공"
        }
        
    except Exception as e:
        logger.error(f"Issue-Session 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"생성 실패: {str(e)}")


@kafka_router.post("/test/add-message")
async def add_test_message(
    session_id: str,
    message_content: str,
    sender: str,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """테스트용: Session에 메시지 추가"""
    try:
        if sender not in ['user', 'bot']:
            raise HTTPException(status_code=400, detail="sender는 'user' 또는 'bot'이어야 합니다")
        
        manager = DatabaseRelationManager()
        result = await manager.add_message_to_session(db, session_id, message_content, sender)
        
        return {
            "status": "success",
            "data": result,
            "message": "메시지 추가 성공"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메시지 추가 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"추가 실패: {str(e)}")


@kafka_router.get("/stats")
async def get_database_stats(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """데이터베이스 통계 조회"""
    try:
        # 각 테이블별 개수 조회
        issue_count = await db.execute(select(func.count(ChatbotIssue.issue)))
        session_count = await db.execute(select(func.count(ChatbotSession.chatbotSessionId)))
        message_count = await db.execute(select(func.count(ChatMessage.chatMessageId)))
        
        # 관계별 통계
        sessions_with_issues = await db.execute(
            select(func.count(ChatbotSession.chatbotSessionId))
            .where(ChatbotSession.issue.isnot(None))
        )
        
        messages_with_issues = await db.execute(
            select(func.count(ChatMessage.chatMessageId))
            .where(ChatMessage.issue.isnot(None))
        )
        
        stats = {
            "total_issues": issue_count.scalar(),
            "total_sessions": session_count.scalar(),
            "total_messages": message_count.scalar(),
            "sessions_with_issues": sessions_with_issues.scalar(),
            "messages_with_issues": messages_with_issues.scalar(),
            "orphaned_sessions": session_count.scalar() - sessions_with_issues.scalar(),
            "orphaned_messages": message_count.scalar() - messages_with_issues.scalar()
        }
        
        return {
            "status": "success",
            "data": stats,
            "message": "데이터베이스 통계 조회 성공"
        }
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")