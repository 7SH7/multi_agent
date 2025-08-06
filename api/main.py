import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

from models.agent_state import AgentState
from models.response_models import ChatResponse, SessionInfoResponse, HealthResponse, FailedAgent
from core.session_manager import SessionManager
from core.monitoring import get_system_monitor
from api.dependencies import (
    get_session_manager,
    get_workflow_manager,
    check_api_keys
)
from config.settings import settings
from utils.validators import ConfigValidator
from api.agent_endpoints import agent_router
from api.knowledge_api import router as knowledge_router
from api.kafka_endpoints import kafka_router
from api.chatbot_workflow import chatbot_workflow_router
from services.kafka_manager import kafka_manager

logger = logging.getLogger(__name__)

# Request/Response Models
class ChatRequest(BaseModel):
    user_message: str
    issue_code: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class SessionEndRequest(BaseModel):
    reason: Optional[str] = None

class SessionCompleteRequest(BaseModel):
    final_summary: Optional[str] = None

def create_application() -> FastAPI:
    # 시작시 설정 검증
    
    logger.info("애플리케이션 설정 검증 시작...")
    
    # 기본 설정 검증
    config_result = ConfigValidator.validate_startup_config(settings)
    for error in config_result.errors:
        logger.error(f"설정 오류: {error}")
    for warning in config_result.warnings:
        logger.warning(f"설정 경고: {warning}")
    
    # 런타임 의존성 검증
    deps_result = ConfigValidator.validate_runtime_dependencies()
    for error in deps_result.errors:
        logger.error(f"의존성 오류: {error}")
    for warning in deps_result.warnings:
        logger.warning(f"의존성 경고: {warning}")
    
    logger.info("애플리케이션 설정 검증 완료 ✅")
    
    app = FastAPI(
        title="Multi-Agent 제조업 챗봇 API",
        description="Multi-Agent 협력형 제조업 장비 문제 해결 챗봇 시스템",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS 설정 - 보안 강화
    
    # 환경별 허용 오리진 설정
    if settings.DEBUG:
        # 개발 환경 - 로컬 개발 서버 허용
        allowed_origins = [
            "http://localhost:3000",  # React 개발 서버
            "http://localhost:3001",  # 추가 프론트엔드 서버
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://localhost:8080",  # Vue.js 개발 서버
            "http://127.0.0.1:8080",
        ]
        allowed_hosts = ["localhost", "127.0.0.1", "testserver"]
    else:
        # 운영 환경 - 실제 도메인만 허용
        allowed_origins = [
            "https://smartfactory.company.com",  # 실제 운영 도메인으로 교체
            "https://app.smartfactory.company.com",  # 앱 서브도메인
            "https://dashboard.smartfactory.company.com",  # 대시보드 서브도메인
        ]
        allowed_hosts = [
            "smartfactory.company.com",
            "app.smartfactory.company.com", 
            "dashboard.smartfactory.company.com",
            "localhost"  # Docker 내부 통신용
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 필요한 메서드만 허용
        allow_headers=[
            "Accept",
            "Accept-Language", 
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Requested-With",
        ],  # 필요한 헤더만 허용
        expose_headers=["X-Process-Time"],  # 응답에서 노출할 헤더
        max_age=600,  # 프리플라이트 요청 캐시 시간 (초)
    )
    
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=allowed_hosts
    )
    
    # Add routes
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = datetime.now()
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()
        response.headers["X-Process-Time"] = str(process_time)
        
        # Record metrics
        monitor = get_system_monitor()
        monitor.record_histogram("request_duration", process_time)
        monitor.increment_counter("total_requests")
        
        return response
    
    @app.post("/chat", response_model=ChatResponse)
    async def chat_endpoint(
        request: ChatRequest,
        session_manager: SessionManager = Depends(get_session_manager),
        workflow_manager = Depends(get_workflow_manager),
        monitor = Depends(get_system_monitor),
        _: None = Depends(check_api_keys)
    ):
        """Multi-Agent 챗봇 대화 API"""
        
        try:
            # Get or create session
            if request.session_id:
                session_data = await session_manager.get_session(request.session_id)
                if not session_data:
                    raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
                
                # 종료된 세션인지 확인
                if session_data.metadata.get('isTerminated', False):
                    raise HTTPException(
                        status_code=400, 
                        detail="이미 해결완료된 세션입니다. 더 이상 대화할 수 없습니다."
                    )
                
                session_id = request.session_id
            else:
                session_data = await session_manager.create_session(
                    user_id=request.user_id or f"user_{datetime.now().timestamp()}",
                    issue_code=request.issue_code or "GENERAL"
                )
                session_id = session_data.session_id
            
            # Determine response_type based on current conversation count (before incrementing for this turn)
            response_type = 'first_question' if session_data.conversation_count == 0 else 'follow_up' # Use 0 for first question
            
            # Create AgentState
            current_state = AgentState(
                session_id=session_id,
                conversation_count=session_data.conversation_count + 1,
                response_type=response_type,
                user_message=request.user_message,
                issue_code=request.issue_code or "GENERAL",
                user_id=request.user_id or f"user_{session_id}",
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
                conversation_history=session_data.metadata.get('conversation_history', []),
                processing_steps=[],
                total_processing_time=0.0,
                timestamp=datetime.now(),
                error=None,
                performance_metrics={},
                resource_usage={},
                failed_agents=None
            )
            
            # Execute workflow
            monitor.increment_counter("chat_requests")
            start_time = datetime.now()
            
            try:
                workflow_result = await workflow_manager.execute(current_state)
                processing_time = (datetime.now() - start_time).total_seconds()
                
                if not workflow_result.success:
                    monitor.increment_counter("workflow_errors")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"워크플로우 실행 오류: {workflow_result.error_message}"
                    )
                
                result_state = workflow_result.final_state
                monitor.increment_counter("workflow_success")
                monitor.record_histogram("workflow_duration", processing_time)
                
            except Exception as e:
                monitor.increment_counter("workflow_errors")
                raise HTTPException(status_code=500, detail=f"처리 오류: {str(e)}")
            
            # Build executive_summary for saving and response
            final_recommendation = result_state.get('final_recommendation', {})
            executive_summary = final_recommendation.get('executive_summary', '응답을 생성할 수 없습니다.')
            
            # 실패한 Agent 정보 처리 (executive_summary에 추가)
            failed_agents_data = result_state.get('failed_agents', [])
            if failed_agents_data:
                failed_names = [f['agent_name'] for f in failed_agents_data]
                executive_summary += f"\n\n⚠️ 주의: {', '.join(failed_names)} 전문가 분석에 오류가 발생했습니다. 다른 전문가의 의견을 바탕으로 답변을 제공합니다."

            # Update session with conversation history and other details - FORCE SAVE
            # This will also increment conversation_count and save to Redis
            try:
                print(f"🔍 [MAIN.PY] 저장 시도 - 세션 ID: {session_id}")
                print(f"🔍 [MAIN.PY] 사용자 메시지: {request.user_message[:50]}...")
                print(f"🔍 [MAIN.PY] 봇 응답: {executive_summary[:50]}...")
                
                # 세션이 존재하는지 먼저 확인
                current_session = await session_manager.get_session(session_id)
                if current_session:
                    print(f"🔍 [MAIN.PY] 저장 전 대화수: {current_session.conversation_count}")
                    print(f"🔍 [MAIN.PY] 저장 전 히스토리: {len(current_session.metadata.get('conversation_history', []))}")
                else:
                    print(f"❌ [MAIN.PY] 세션을 찾을 수 없음: {session_id}")
                
                # 대화 저장 - add_conversation이 conversation_count도 증가시킴
                simple_save_success = await session_manager.add_conversation(
                    session_id, 
                    request.user_message, 
                    executive_summary
                )
                print(f"✅ [MAIN.PY] 대화 저장 결과: {simple_save_success}")
                
                if simple_save_success:
                    # 저장 후 즉시 확인
                    check_session = await session_manager.get_session(session_id)
                    if check_session:
                        print(f"✅ [MAIN.PY] 저장 후 대화수: {check_session.conversation_count}")
                        print(f"✅ [MAIN.PY] 저장 후 히스토리 수: {len(check_session.metadata.get('conversation_history', []))}")
                        
                        # 히스토리 내용도 확인
                        history = check_session.metadata.get('conversation_history', [])
                        if history:
                            last_conv = history[-1]
                            print(f"✅ [MAIN.PY] 마지막 대화 - 사용자: {last_conv.get('user_message', '')[:30]}...")
                            print(f"✅ [MAIN.PY] 마지막 대화 - 봇: {last_conv.get('bot_response', '')[:30]}...")
                    else:
                        print(f"❌ [MAIN.PY] 저장 후 세션 조회 실패")
                else:
                    print(f"❌ [MAIN.PY] 대화 저장 실패")
                
            except Exception as save_error:
                print(f"❌ [MAIN.PY] 대화 저장 오류: {str(save_error)}")
                import traceback
                traceback.print_exc()
                # 저장 실패해도 계속 진행
            
            # Re-fetch session_data to get the updated conversation_count and other fields
            # This is crucial to ensure the ChatResponse has the correct, updated values
            session_data = await session_manager.get_session(session_id)
            if not session_data: # Should not happen if add_conversation_detailed worked
                raise HTTPException(status_code=500, detail="세션 데이터 업데이트 후 재조회 실패")

            # Build response using the updated session_data
            failed_agents = [
                FailedAgent(
                    agent_name=failed['agent_name'],
                    error_message=failed['error_message'],
                    timestamp=failed['timestamp'],
                    specialty=failed['specialty']
                ) for failed in failed_agents_data
            ] if failed_agents_data else None
            
            return ChatResponse(
                session_id=session_id,
                conversation_count=session_data.conversation_count, # Use the updated count from re-fetched session_data
                response_type='first_question' if session_data.conversation_count == 1 else 'follow_up', # Re-evaluate response_type based on updated count
                executive_summary=executive_summary,
                detailed_solution=final_recommendation.get('detailed_solution', []),
                immediate_actions=final_recommendation.get('immediate_actions', []),
                safety_precautions=final_recommendation.get('safety_precautions', []),
                cost_estimation=final_recommendation.get('cost_estimation', {
                    'parts': '분석 필요',
                    'labor': '분석 필요', 
                    'total': '분석 필요'
                }),
                confidence_level=final_recommendation.get('confidence_level', 0.5),
                participating_agents=list(result_state.get('agent_responses', {}).keys()),
                debate_rounds=len(result_state.get('debate_rounds', [])),
                processing_time=processing_time,
                processing_steps=result_state.get('processing_steps', []),
                timestamp=datetime.now().isoformat(),
                failed_agents=failed_agents)
            
        except HTTPException:
            raise
        except Exception as e:
            monitor.increment_counter("api_errors")
            raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
    
    @app.get("/session/{session_id}", response_model=SessionInfoResponse)
    async def get_session_info(
        session_id: str,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """세션 정보 조회"""
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        return SessionInfoResponse(
            session_id=session_id,
            status=session_data.status.value,
            conversation_count=session_data.conversation_count,
            issue_code=session_data.issue_code,
            created_at=session_data.created_at.isoformat(),
            total_processing_time=session_data.total_processing_time,
            agents_used=session_data.metadata.get('all_agents_used', session_data.selected_agents),
            total_debates=len(session_data.debate_history)
        )
    
    @app.post("/session/{session_id}/end")
    async def end_session(
        session_id: str,
        request: SessionEndRequest,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """세션 종료"""
        success = await session_manager.end_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        return {"message": "세션이 종료되었습니다", "session_id": session_id}
    
    @app.post("/session/{session_id}/complete")
    async def complete_session(
        session_id: str,
        request: SessionCompleteRequest,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """세션 해결완료 처리 (isTerminated = True)"""
        try:
            # 세션 존재 확인
            session_data = await session_manager.get_session(session_id)
            if not session_data:
                raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
            
            # 이미 완료된 세션인지 확인
            if session_data.metadata.get('isTerminated', False):
                raise HTTPException(status_code=400, detail="이미 완료된 세션입니다")
            
            # 세션을 완료 상태로 변경
            update_data = {
                'isTerminated': True,
                'terminated_at': datetime.now().isoformat(),
                'final_summary': request.final_summary
            }
            
            # 세션 메타데이터 업데이트
            session_data.metadata.update(update_data)
            session_data.updated_at = datetime.now()
            success = await session_manager.update_session(session_data)
            
            if not success:
                raise HTTPException(status_code=500, detail="세션 완료 처리 중 오류가 발생했습니다")
            
            return {
                "message": "세션이 해결완료 처리되었습니다",
                "session_id": session_id,
                "isTerminated": True,
                "terminated_at": update_data['terminated_at']
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"세션 완료 처리 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"세션 완료 처리 중 오류: {str(e)}")
    
    @app.get("/session/{session_id}/download-report")
    async def download_session_report(
        session_id: str,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """세션 대화 내역 PDF 보고서 다운로드 (isReported = True)"""
        try:
            from utils.pdf_generator import generate_session_report
            
            # 세션 존재 확인
            session_data = await session_manager.get_session(session_id)
            if not session_data:
                raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
            
            # 완료된 세션인지 확인
            if not session_data.metadata.get('isTerminated', False):
                raise HTTPException(status_code=400, detail="완료되지 않은 세션은 보고서를 생성할 수 없습니다")
            
            # 대화 내역 가져오기
            conversation_history = session_data.metadata.get('conversation_history', [])
            
            # 세션 정보 준비
            session_info = {
                'session_id': session_id,
                'user_id': session_data.user_id,
                'issue_code': session_data.issue_code,
                'created_at': session_data.created_at.strftime('%Y-%m-%d %H:%M:%S') if session_data.created_at else 'N/A',
                'ended_at': session_data.metadata.get('terminated_at', 'N/A'),
                'conversation_count': session_data.conversation_count,
                'participating_agents': session_data.metadata.get('all_agents_used', session_data.selected_agents or [])
            }
            
            # 최종 요약
            final_summary = session_data.metadata.get('final_summary')
            
            # PDF 생성
            pdf_buffer = await generate_session_report(
                session_id=session_id,
                conversation_history=conversation_history,
                session_info=session_info,
                final_summary=final_summary
            )
            
            # 보고서 생성 완료 표시 (isReported = True)
            session_data.metadata['isReported'] = True
            session_data.metadata['report_generated_at'] = datetime.now().isoformat()
            session_data.updated_at = datetime.now()
            await session_manager.update_session(session_data)
            
            # PDF 파일명 생성
            filename = f"chatbot_report_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # StreamingResponse로 PDF 반환
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
    
    @app.get("/ping")
    async def ping():
        """단순 ping - 의존성 없는 헬스체크"""
        return {"status": "ok", "timestamp": datetime.now().isoformat()}
    
    @app.post("/chat/test", response_model=ChatResponse)
    async def chat_test_endpoint(
        request: ChatRequest,
        session_manager: SessionManager = Depends(get_session_manager),
        workflow_manager = Depends(get_workflow_manager),
        monitor = Depends(get_system_monitor)
    ):
        """API 키 없이 테스트할 수 있는 챗봇 엔드포인트"""
        
        try:
            # Get or create session
            if request.session_id:
                session_data = await session_manager.get_session(request.session_id)
                if not session_data:
                    raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
                
                # 종료된 세션인지 확인
                if session_data.metadata.get('isTerminated', False):
                    raise HTTPException(
                        status_code=400, 
                        detail="이미 해결완료된 세션입니다. 더 이상 대화할 수 없습니다."
                    )
                
                session_id = request.session_id
            else:
                session_data = await session_manager.create_session(
                    user_id=request.user_id or f"user_{datetime.now().timestamp()}",
                    issue_code=request.issue_code or "GENERAL"
                )
                session_id = session_data.session_id
            
            # Update conversation count
            await session_manager.increment_conversation_count(session_id)
            
            # Prepare agent state
            agent_state = AgentState(
                session_id=session_id,
                conversation_count=session_data.conversation_count + 1,
                response_type='first_question' if session_data.conversation_count == 0 else 'follow_up',
                user_message=request.user_message,
                issue_code=request.issue_code or "GENERAL",
                user_id=request.user_id or 'test_user',
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
                conversation_history=session_data.metadata.get('conversation_history', []),
                processing_steps=[],
                total_processing_time=0.0,
                timestamp=datetime.now(),
                error=None,
                performance_metrics={},
                resource_usage={},
                failed_agents=None
            )
            
            # Execute workflow
            result = await workflow_manager.execute(agent_state)
            
            if not result.success:
                raise HTTPException(status_code=500, detail=f"워크플로우 실행 실패: {result.error_message}")
            
            # Build final recommendation from result FIRST (before saving)
            final_recommendation = result.final_state.get('final_recommendation', {})
            executive_summary = final_recommendation.get('executive_summary', result.final_state.get('final_response', '답변 생성 실패'))
            
            # Update session with conversation (save the actual response)
            await session_manager.add_conversation(
                session_id, 
                request.user_message, 
                executive_summary
            )
            
            # Record metrics
            monitor.record_histogram("workflow_execution_time", result.execution_time)
            monitor.increment_counter("successful_conversations")
            
            # final_recommendation already built above
            
            # 실패한 Agent 정보 처리 (테스트 엔드포인트용)
            failed_agents_data = result.final_state.get('failed_agents', [])
            failed_agents = [
                FailedAgent(
                    agent_name=failed['agent_name'],
                    error_message=failed['error_message'],
                    timestamp=failed['timestamp'],
                    specialty=failed['specialty']
                ) for failed in failed_agents_data
            ] if failed_agents_data else None
            
            # executive_summary에 실패한 Agent 정보 추가
            executive_summary = final_recommendation.get('executive_summary', result.final_state.get('final_response', '답변 생성 실패'))
            if failed_agents:
                failed_names = [f.agent_name for f in failed_agents]
                executive_summary += f"\n\n⚠️ 주의: {', '.join(failed_names)} 전문가 분석에 오류가 발생했습니다. 다른 전문가의 의견을 바탕으로 답변을 제공합니다."
            
            return ChatResponse(
                session_id=session_id,
                conversation_count=session_data.conversation_count + 1,
                response_type='test',
                executive_summary=executive_summary,
                detailed_solution=final_recommendation.get('detailed_solution', []),
                immediate_actions=final_recommendation.get('immediate_actions', []),
                safety_precautions=final_recommendation.get('safety_precautions', []),
                cost_estimation=final_recommendation.get('cost_estimation', {
                    'parts': '분석 필요',
                    'labor': '분석 필요', 
                    'total': '분석 필요'
                }),
                confidence_level=final_recommendation.get('confidence_level', result.final_state.get('confidence_score', 0.5)),
                participating_agents=result.final_state.get('selected_agents', []),
                debate_rounds=len(result.final_state.get('debate_rounds', [])),
                processing_time=result.execution_time,
                processing_steps=result.steps_completed,
                timestamp=datetime.now().isoformat(),
                failed_agents=failed_agents
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"챗봇 테스트 처리 중 오류 발생: {str(e)}")
            monitor.increment_counter("failed_conversations")
            raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check(monitor = Depends(get_system_monitor)):
        """시스템 헬스 체크"""
        health_data = monitor.get_system_health()
        
        # 설정 상태 체크 추가
        config_status = ConfigValidator.get_health_check_status(settings)
        
        # Determine overall status
        active_alerts = health_data.get('active_alerts_count', 0)
        config_alerts = len(config_status.get('missing_keys', []))
        
        if not config_status.get('config_valid', True):
            status = "error"
        elif active_alerts > 0 or config_alerts > 0:
            status = "warning" if (active_alerts + config_alerts) < 3 else "error"
        else:
            status = "healthy"
        
        # 설정 관련 알림 추가
        alerts = health_data.get('active_alerts', [])
        if config_alerts > 0:
            alerts.append(f"설정 문제: API 키 {config_alerts}개 누락")
        
        return HealthResponse(
            status=status,
            timestamp=datetime.now(),
            uptime_seconds=health_data['uptime_seconds'],
            active_sessions=health_data.get('active_sessions', 0),
            total_requests=health_data.get('total_requests', 0),
            agent_health=health_data.get('agent_health', {}),
            active_alerts=alerts,
            system_metrics={
                'memory_usage_mb': health_data.get('memory_usage_mb', 0),
                'cpu_usage_percent': health_data.get('cpu_usage_percent', 0),
                'config_status': config_status  # 설정 상태 추가
            }
        )
    
    @app.get("/metrics")
    async def get_metrics(monitor = Depends(get_system_monitor)):
        """시스템 메트릭 조회 (모니터링용)"""
        return monitor.get_all_metrics_summary()
    
    @app.get("/test/simple")
    async def simple_test():
        """간단한 기능 테스트"""
        try:
            from utils.rag_engines import HybridRAGEngine
            
            # RAG 엔진 테스트
            rag_engine = HybridRAGEngine()
            results = await rag_engine.search("모터 베어링", top_k=2)
            await rag_engine.close()
            
            return {
                "status": "success",
                "message": "모든 기본 기능이 정상 작동합니다",
                "rag_results_count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"오류 발생: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    @app.delete("/session/{session_id}")
    async def delete_session(
        session_id: str,
        session_manager: SessionManager = Depends(get_session_manager)
    ):
        """세션 삭제"""
        success = await session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        return {"message": "세션이 삭제되었습니다", "session_id": session_id}
    
    

    # Individual Agent 라우터 추가
    app.include_router(agent_router)
    
    # Knowledge Base API 라우터 추가
    app.include_router(knowledge_router)
    
    # Kafka Management API 라우터 추가
    app.include_router(kafka_router)
    
    # Chatbot Workflow API 라우터 추가
    app.include_router(chatbot_workflow_router)
    
    # Startup/Shutdown 이벤트 추가
    @app.on_event("startup")
    async def startup_event():
        """애플리케이션 시작시 실행"""
        try:
            logger.info("애플리케이션 시작 - Kafka Consumer 초기화 중...")
            # Kafka Consumer는 선택적으로 시작 (환경변수로 제어 가능)
            kafka_enabled = getattr(settings, 'KAFKA_ENABLED', True)
            if kafka_enabled:
                await kafka_manager.start()
                logger.info("Kafka Consumer 시작 완료")
            else:
                logger.info("Kafka Consumer 비활성화됨 (KAFKA_ENABLED=False)")
        except Exception as e:
            logger.error(f"Kafka Consumer 시작 실패: {str(e)}")
            # Kafka 실패해도 애플리케이션은 계속 실행
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """애플리케이션 종료시 실행"""
        try:
            logger.info("애플리케이션 종료 - Kafka Consumer 정리 중...")
            await kafka_manager.stop()
            logger.info("Kafka Consumer 정리 완료")
        except Exception as e:
            logger.error(f"Kafka Consumer 정리 실패: {str(e)}")
    
    return app

# Create application instance
app = create_application()

def get_application() -> FastAPI:
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
