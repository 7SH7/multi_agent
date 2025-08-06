"""ChatbotIssue 워크플로우 API - Issue 기반 챗봇 세션 관리"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.database_models import ChatbotIssue, ChatbotSession, ChatMessage
from utils.database import get_async_db
from utils.database_relations import DatabaseRelationManager
from core.session_manager import SessionManager
from api.dependencies import get_session_manager, get_workflow_manager
from models.agent_state import AgentState
from models.response_models import ChatResponse
from utils.pdf_generator import generate_session_report
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

chatbot_workflow_router = APIRouter(prefix="/api/chatbot-workflow", tags=["Chatbot Workflow"])


class StartChatRequest(BaseModel):
    """챗봇 대화 시작 요청"""
    issue_id: str
    user_id: str
    user_message: str


class ChatRequest(BaseModel):
    """챗봇 대화 요청"""
    session_id: str
    user_message: str


class CompleteChatRequest(BaseModel):
    """챗봇 대화 완료 요청"""
    session_id: str
    final_summary: Optional[str] = None


@chatbot_workflow_router.post("/start-chat")
async def start_chat_from_issue(
    request: StartChatRequest,
    db: AsyncSession = Depends(get_async_db),
    session_manager: SessionManager = Depends(get_session_manager),
    workflow_manager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """ChatbotIssue 기반으로 챗봇 대화 시작"""
    try:
        # 1. ChatbotIssue 존재 확인
        result = await db.execute(
            select(ChatbotIssue).where(ChatbotIssue.issue == request.issue_id)
        )
        chatbot_issue = result.scalar_one_or_none()
        
        if not chatbot_issue:
            raise HTTPException(status_code=404, detail=f"Issue '{request.issue_id}'를 찾을 수 없습니다")
        
        # 2. DB에 ChatbotSession 생성
        db_manager = DatabaseRelationManager()
        session_result = await db_manager.create_chatbot_issue_with_session(
            db=db,
            issue_id=request.issue_id,
            process_type=chatbot_issue.processType,
            mode_type=chatbot_issue.modeType,
            mode_log_id=chatbot_issue.modeLogId,
            user_id=request.user_id,
            description=chatbot_issue.description
        )
        
        db_session_id = session_result["session_id"]
        
        # 3. Redis SessionManager에 세션 생성
        redis_session_data = await session_manager.create_session(
            user_id=request.user_id,
            issue_code=request.issue_id
        )
        redis_session_id = redis_session_data.session_id
        
        # 4. 첫 번째 메시지로 챗봇 대화 시작
        current_state = AgentState(
            session_id=redis_session_id,
            conversation_count=1,
            response_type='first_question',
            user_message=request.user_message,
            issue_code=request.issue_id,
            user_id=request.user_id,
            issue_classification=None,
            question_category=None,
            rag_context=None,
            selected_agents=None,
            selection_reasoning=None,
            agent_responses=None,
            response_quality_scores=None,
            debate_rounds=None,
            consensus_points=None,
            final_recommendation=None,
            equipment_type=chatbot_issue.modeType,
            equipment_kr=chatbot_issue.modeType,
            problem_type=chatbot_issue.processType,
            root_causes=None,
            severity_level=None,
            analysis_confidence=None,
            conversation_history=[],
            processing_steps=[],
            total_processing_time=0.0,
            timestamp=datetime.now(),
            error=None,
            performance_metrics={},
            resource_usage={},
            failed_agents=None
        )
        
        # 5. 워크플로우 실행
        workflow_result = await workflow_manager.execute(current_state)
        
        if not workflow_result.success:
            raise HTTPException(
                status_code=500, 
                detail=f"워크플로우 실행 오류: {workflow_result.error_message}"
            )
        
        result_state = workflow_result.final_state
        final_recommendation = result_state.get('final_recommendation', {})
        executive_summary = final_recommendation.get('executive_summary', '응답을 생성할 수 없습니다.')
        
        # 6. Redis 세션에 대화 저장
        await session_manager.add_conversation(
            redis_session_id,
            request.user_message,
            executive_summary
        )
        
        # 7. DB에 메시지들 저장
        await db_manager.add_message_to_session(
            db, db_session_id, request.user_message, "user"
        )
        await db_manager.add_message_to_session(
            db, db_session_id, executive_summary, "bot"
        )
        
        # 8. Redis 세션 메타데이터에 DB 세션 ID 저장 (연동용)
        redis_session_data = await session_manager.get_session(redis_session_id)
        redis_session_data.metadata['db_session_id'] = db_session_id
        redis_session_data.metadata['issue_id'] = request.issue_id
        await session_manager.update_session(redis_session_data)
        
        return {
            "status": "success",
            "data": {
                "redis_session_id": redis_session_id,
                "db_session_id": db_session_id,
                "issue_id": request.issue_id,
                "conversation_count": 1,
                "executive_summary": executive_summary,
                "issue_info": {
                    "process_type": chatbot_issue.processType,
                    "mode_type": chatbot_issue.modeType,
                    "description": chatbot_issue.description
                }
            },
            "message": "챗봇 대화가 시작되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"챗봇 대화 시작 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"대화 시작 실패: {str(e)}")


@chatbot_workflow_router.post("/continue-chat")
async def continue_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_async_db),
    session_manager: SessionManager = Depends(get_session_manager),
    workflow_manager = Depends(get_workflow_manager)
) -> Dict[str, Any]:
    """기존 세션으로 챗봇 대화 계속"""
    try:
        # 1. Redis 세션 확인
        redis_session_data = await session_manager.get_session(request.session_id)
        if not redis_session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        # 세션 접근 차단 확인
        if redis_session_data.metadata.get('isTerminated', False):
            raise HTTPException(
                status_code=400, 
                detail="Issue가 해결되어 더 이상 대화할 수 없습니다"
            )
        
        if redis_session_data.metadata.get('isReported') is not None:
            raise HTTPException(
                status_code=400, 
                detail="이미 처리 완료된 세션입니다"
            )
        
        db_session_id = redis_session_data.metadata.get('db_session_id')
        issue_id = redis_session_data.metadata.get('issue_id')
        
        # 2. 워크플로우 실행 (기존 챗봇 로직과 동일)
        current_state = AgentState(
            session_id=request.session_id,
            conversation_count=redis_session_data.conversation_count + 1,
            response_type='follow_up',
            user_message=request.user_message,
            issue_code=issue_id or "GENERAL",
            user_id=redis_session_data.user_id,
            issue_classification=None,
            question_category=None,
            rag_context=None,
            selected_agents=None,
            selection_reasoning=None,
            agent_responses=None,
            response_quality_scores=None,
            debate_rounds=None,
            consensus_points=None,
            final_recommendation=None,
            equipment_type=None,
            equipment_kr=None,
            problem_type=None,
            root_causes=None,
            severity_level=None,
            analysis_confidence=None,
            conversation_history=redis_session_data.metadata.get('conversation_history', []),
            processing_steps=[],
            total_processing_time=0.0,
            timestamp=datetime.now(),
            error=None,
            performance_metrics={},
            resource_usage={},
            failed_agents=None
        )
        
        # 3. 워크플로우 실행
        workflow_result = await workflow_manager.execute(current_state)
        
        if not workflow_result.success:
            raise HTTPException(
                status_code=500, 
                detail=f"워크플로우 실행 오류: {workflow_result.error_message}"
            )
        
        result_state = workflow_result.final_state
        final_recommendation = result_state.get('final_recommendation', {})
        executive_summary = final_recommendation.get('executive_summary', '응답을 생성할 수 없습니다.')
        
        # 4. Redis 세션에 대화 저장
        await session_manager.add_conversation(
            request.session_id,
            request.user_message,
            executive_summary
        )
        
        # 5. DB에 메시지들 저장 (DB 세션 ID가 있는 경우)
        if db_session_id:
            db_manager = DatabaseRelationManager()
            await db_manager.add_message_to_session(
                db, db_session_id, request.user_message, "user"
            )
            await db_manager.add_message_to_session(
                db, db_session_id, executive_summary, "bot"
            )
        
        # 6. 업데이트된 세션 정보 조회
        updated_session = await session_manager.get_session(request.session_id)
        
        return {
            "status": "success",
            "data": {
                "session_id": request.session_id,
                "conversation_count": updated_session.conversation_count,
                "executive_summary": executive_summary,
                "processing_time": workflow_result.execution_time if hasattr(workflow_result, 'execution_time') else 0.0
            },
            "message": "대화가 계속되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"대화 계속 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"대화 실패: {str(e)}")


@chatbot_workflow_router.post("/complete-chat")
async def complete_chat(
    request: CompleteChatRequest,
    db: AsyncSession = Depends(get_async_db),
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict[str, Any]:
    """챗봇 대화 완료 처리 (isTerminated는 설정하지 않음 - Kafka에서 isSolved=true로 처리)"""
    try:
        # 1. Redis 세션 확인
        redis_session_data = await session_manager.get_session(request.session_id)
        if not redis_session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        # 세션 접근 차단 확인 (isTerminated 또는 isReported가 값이 있으면)
        if redis_session_data.metadata.get('isTerminated', False):
            raise HTTPException(status_code=400, detail="Issue가 해결되어 더 이상 대화할 수 없습니다")
        
        if redis_session_data.metadata.get('isReported') is not None:
            raise HTTPException(status_code=400, detail="이미 처리 완료된 세션입니다")
        
        db_session_id = redis_session_data.metadata.get('db_session_id')
        
        # 2. Redis 세션에 완료 요약만 저장 (종료는 하지 않음)
        redis_session_data.metadata.update({
            'final_summary': request.final_summary,
            'completed_at': datetime.now().isoformat()
        })
        redis_session_data.updated_at = datetime.now()
        await session_manager.update_session(redis_session_data)
        
        return {
            "status": "success",
            "data": {
                "session_id": request.session_id,
                "db_session_id": db_session_id,
                "is_terminated": False,  # 아직 종료되지 않음
                "completed_at": redis_session_data.metadata['completed_at'],
                "message": "대화 완료됨. Issue 해결시 자동으로 세션이 종료됩니다."
            },
            "message": "챗봇 대화 완료 처리됨 (Issue 해결 대기중)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"대화 완료 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"완료 처리 실패: {str(e)}")


@chatbot_workflow_router.get("/download-report/{session_id}")
async def download_chat_report(
    session_id: str,
    db: AsyncSession = Depends(get_async_db),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """챗봇 대화 PDF 보고서 다운로드 및 DB 업데이트"""
    try:
        # 1. Redis 세션 확인
        redis_session_data = await session_manager.get_session(session_id)
        if not redis_session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        # 대화 완료된 세션인지 확인 (completed_at이 있어야 함)
        if not redis_session_data.metadata.get('completed_at'):
            raise HTTPException(status_code=400, detail="대화가 완료되지 않은 세션입니다")
        
        # 이미 보고서 처리 결정이 된 세션인지 확인
        if redis_session_data.metadata.get('isReported') is not None:
            raise HTTPException(status_code=400, detail="이미 보고서 처리가 완료된 세션입니다")
        
        db_session_id = redis_session_data.metadata.get('db_session_id')
        issue_id = redis_session_data.metadata.get('issue_id')
        
        # 2. 대화 내역 가져오기
        conversation_history = redis_session_data.metadata.get('conversation_history', [])
        
        # 3. 세션 정보 준비
        session_info = {
            'session_id': session_id,
            'user_id': redis_session_data.user_id,
            'issue_code': issue_id,
            'created_at': redis_session_data.created_at.strftime('%Y-%m-%d %H:%M:%S') if redis_session_data.created_at else 'N/A',
            'ended_at': redis_session_data.metadata.get('terminated_at', 'N/A'),
            'conversation_count': redis_session_data.conversation_count,
            'participating_agents': redis_session_data.metadata.get('all_agents_used', redis_session_data.selected_agents or [])
        }
        
        # 최종 요약
        final_summary = redis_session_data.metadata.get('final_summary')
        
        # 4. PDF 생성
        pdf_buffer = await generate_session_report(
            session_id=session_id,
            conversation_history=conversation_history,
            session_info=session_info,
            final_summary=final_summary
        )
        
        # 5. Redis 세션에 보고서 처리 완료 표시
        redis_session_data.metadata['isReported'] = True  # 처리 완료 (다운로드함)
        redis_session_data.metadata['report_action'] = 'downloaded'
        redis_session_data.metadata['report_generated_at'] = datetime.now().isoformat()
        redis_session_data.updated_at = datetime.now()
        await session_manager.update_session(redis_session_data)
        
        # 6. DB 세션에도 보고서 처리 완료 표시 (있는 경우)
        if db_session_id:
            result = await db.execute(
                select(ChatbotSession).where(ChatbotSession.chatbotSessionId == db_session_id)
            )
            db_session = result.scalar_one_or_none()
            
            if db_session:
                db_session.isReported = True  # 처리 완료
                await db.commit()
        
        # 7. PDF 파일명 생성
        filename = f"chatbot_report_{issue_id or session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # 8. StreamingResponse로 PDF 반환
        return StreamingResponse(
            pdf_buffer,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/pdf'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 보고서 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF 보고서 생성 중 오류: {str(e)}")


@chatbot_workflow_router.post("/skip-report/{session_id}")
async def skip_report_download(
    session_id: str,
    db: AsyncSession = Depends(get_async_db),
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict[str, Any]:
    """보고서 다운로드 건너뛰기 (isReported = False)"""
    try:
        # 1. Redis 세션 확인
        redis_session_data = await session_manager.get_session(session_id)
        if not redis_session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        # 대화 완료된 세션인지 확인
        if not redis_session_data.metadata.get('completed_at'):
            raise HTTPException(status_code=400, detail="대화가 완료되지 않은 세션입니다")
        
        # 이미 보고서 처리 결정이 된 세션인지 확인
        if redis_session_data.metadata.get('isReported') is not None:
            raise HTTPException(status_code=400, detail="이미 보고서 처리가 완료된 세션입니다")
        
        db_session_id = redis_session_data.metadata.get('db_session_id')
        
        # 2. Redis 세션에 보고서 처리 완료 표시 (건너뛰기도 처리 완료)
        redis_session_data.metadata['isReported'] = True  # 처리 완료 (건너뛰기함)
        redis_session_data.metadata['report_action'] = 'skipped'
        redis_session_data.metadata['report_skipped_at'] = datetime.now().isoformat()
        redis_session_data.updated_at = datetime.now()
        await session_manager.update_session(redis_session_data)
        
        # 3. DB 세션에도 보고서 처리 완료 표시 (있는 경우)
        if db_session_id:
            result = await db.execute(
                select(ChatbotSession).where(ChatbotSession.chatbotSessionId == db_session_id)
            )
            db_session = result.scalar_one_or_none()
            
            if db_session:
                db_session.isReported = True  # 처리 완료
                await db.commit()
        
        return {
            "status": "success",
            "data": {
                "session_id": session_id,
                "db_session_id": db_session_id,
                "is_reported": True,  # 처리 완료
                "report_action": "skipped",
                "report_skipped_at": redis_session_data.metadata['report_skipped_at']
            },
            "message": "보고서 다운로드를 건너뛰었습니다. 세션이 비활성화됩니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보고서 건너뛰기 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"처리 실패: {str(e)}")


@chatbot_workflow_router.get("/session-status/{session_id}")
async def get_session_status(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict[str, Any]:
    """세션 상태 조회"""
    try:
        redis_session_data = await session_manager.get_session(session_id)
        if not redis_session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        return {
            "status": "success",
            "data": {
                "session_id": session_id,
                "db_session_id": redis_session_data.metadata.get('db_session_id'),
                "issue_id": redis_session_data.metadata.get('issue_id'),
                "user_id": redis_session_data.user_id,
                "conversation_count": redis_session_data.conversation_count,
                "is_terminated": redis_session_data.metadata.get('isTerminated', False),
                "is_reported": redis_session_data.metadata.get('isReported', False),
                "created_at": redis_session_data.created_at.isoformat() if redis_session_data.created_at else None,
                "terminated_at": redis_session_data.metadata.get('terminated_at'),
                "report_generated_at": redis_session_data.metadata.get('report_generated_at')
            },
            "message": "세션 상태 조회 성공"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")


@chatbot_workflow_router.get("/issues/{issue_id}/sessions")
async def get_issue_sessions(
    issue_id: str,
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """특정 Issue의 모든 세션 조회"""
    try:
        db_manager = DatabaseRelationManager()
        issue_details = await db_manager.get_issue_with_sessions_and_messages(db, issue_id)
        
        if not issue_details:
            raise HTTPException(status_code=404, detail=f"Issue '{issue_id}'를 찾을 수 없습니다")
        
        return {
            "status": "success",
            "data": issue_details,
            "message": f"Issue '{issue_id}' 세션 조회 성공"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Issue 세션 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"조회 실패: {str(e)}")