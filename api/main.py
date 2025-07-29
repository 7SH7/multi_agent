import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, ValidationError

from models.agent_state import AgentState
from models.response_models import ChatResponse, SessionInfoResponse, HealthResponse
from core.enhanced_workflow import get_enhanced_workflow
from core.session_manager import SessionManager
from core.monitoring import get_system_monitor
from api.dependencies import (
    get_session_manager,
    get_workflow_manager,
    get_system_monitor as get_monitor_dep,
    validate_request,
    check_api_keys
)

# Request/Response Models
class ChatRequest(BaseModel):
    user_message: str
    issue_code: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class SessionEndRequest(BaseModel):
    reason: Optional[str] = None

def create_application() -> FastAPI:
    app = FastAPI(
        title="Multi-Agent 제조업 챗봇 API",
        description="Multi-Agent 협력형 제조업 장비 문제 해결 챗봇 시스템",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS 설정 - 보안 강화
    from config.settings import settings
    
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
        monitor = Depends(get_monitor_dep),
        _: None = Depends(check_api_keys)
    ):
        """Multi-Agent 챗봇 대화 API"""
        
        try:
            # Get or create session
            if request.session_id:
                session_data = await session_manager.get_session(request.session_id)
                if not session_data:
                    raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
                session_id = request.session_id
            else:
                session_data = await session_manager.create_session(
                    user_id=request.user_id,
                    issue_code=request.issue_code
                )
                session_id = session_data.session_id
            
            # Update conversation count
            session_data.conversation_count += 1
            response_type = 'first_question' if session_data.conversation_count == 1 else 'follow_up'
            
            # Create AgentState
            current_state = AgentState(
                session_id=session_id,
                conversation_count=session_data.conversation_count,
                response_type=response_type,
                user_message=request.user_message,
                issue_code=request.issue_code,
                conversation_history=session_data.metadata.get('conversation_history', []),
                processing_steps=[],
                timestamp=datetime.now(),
                error=None
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
            
            # Update session
            session_data.agent_responses = result_state.get('agent_responses', {})
            session_data.debate_history = result_state.get('debate_rounds', [])
            session_data.selected_agents = result_state.get('selected_agents', [])
            session_data.processing_steps = result_state.get('processing_steps', [])
            session_data.total_processing_time += processing_time
            
            # Add to conversation history
            if 'conversation_history' not in session_data.metadata:
                session_data.metadata['conversation_history'] = []
            
            session_data.metadata['conversation_history'].append({
                'user_message': request.user_message,
                'timestamp': datetime.now().isoformat(),
                'agents_used': result_state.get('selected_agents', []),
                'processing_time': processing_time
            })
            
            await session_manager.update_session(session_data)
            
            # Build response
            final_recommendation = result_state.get('final_recommendation', {})
            
            return ChatResponse(
                session_id=session_id,
                conversation_count=session_data.conversation_count,
                response_type=response_type,
                executive_summary=final_recommendation.get('executive_summary', '응답을 생성할 수 없습니다.'),
                detailed_solution=final_recommendation.get('detailed_solution', []),
                immediate_actions=final_recommendation.get('immediate_actions', []),
                safety_precautions=final_recommendation.get('safety_precautions', []),
                cost_estimation=final_recommendation.get('cost_estimation', {}),
                confidence_level=final_recommendation.get('confidence_level', 0.5),
                participating_agents=list(result_state.get('agent_responses', {}).keys()),
                debate_rounds=len(result_state.get('debate_rounds', [])),
                processing_time=processing_time,
                processing_steps=result_state.get('processing_steps', []),
                timestamp=datetime.now().isoformat()
            )
            
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
            agents_used=list(set(session_data.selected_agents)),
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
    
    @app.get("/ping")
    async def ping():
        """단순 ping - 의존성 없는 헬스체크"""
        return {"status": "ok", "timestamp": datetime.now().isoformat()}
    
    @app.post("/chat/test", response_model=ChatResponse)
    async def chat_test_endpoint(
        request: ChatRequest,
        session_manager: SessionManager = Depends(get_session_manager),
        workflow_manager = Depends(get_workflow_manager),
        monitor = Depends(get_monitor_dep)
    ):
        """API 키 없이 테스트할 수 있는 챗봇 엔드포인트"""
        
        try:
            # Get or create session
            if request.session_id:
                session_data = await session_manager.get_session(request.session_id)
                if not session_data:
                    raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
                session_id = request.session_id
            else:
                session_data = await session_manager.create_session(
                    user_id=request.user_id,
                    issue_code=request.issue_code
                )
                session_id = session_data.session_id
            
            # Update conversation count
            await session_manager.increment_conversation_count(session_id)
            
            # Prepare agent state
            agent_state = AgentState()
            agent_state.update({
                'session_id': session_id,
                'user_message': request.user_message,
                'issue_code': request.issue_code,
                'user_id': request.user_id or 'test_user',
                'conversation_context': session_data.conversation_history,
                'metadata': {
                    'request_time': datetime.now().isoformat(),
                    'is_test': True
                }
            })
            
            # Execute workflow
            result = await workflow_manager.execute(agent_state)
            
            if not result.success:
                raise HTTPException(status_code=500, detail=f"워크플로우 실행 실패: {result.error_message}")
            
            # Update session with conversation
            await session_manager.add_conversation(
                session_id, 
                request.user_message, 
                result.final_state.get('final_response', '답변 생성 실패')
            )
            
            # Record metrics
            monitor.record_histogram("workflow_execution_time", result.execution_time)
            monitor.increment_counter("successful_conversations")
            
            return ChatResponse(
                response=result.final_state.get('final_response', '답변 생성 실패'),
                session_id=session_id,
                confidence_score=result.final_state.get('confidence_score', 0.5),
                processing_time=result.execution_time,
                agents_used=result.final_state.get('selected_agents', []),
                workflow_steps=result.steps_completed,
                knowledge_sources=result.final_state.get('knowledge_sources', []),
                metadata={
                    'workflow_success': result.success,
                    'session_conversations': session_data.conversation_count + 1,
                    'test_mode': True
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"챗봇 테스트 처리 중 오류 발생: {str(e)}")
            monitor.increment_counter("failed_conversations")
            raise HTTPException(status_code=500, detail=f"서버 내부 오류: {str(e)}")
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check(monitor = Depends(get_monitor_dep)):
        """시스템 헬스 체크"""
        health_data = monitor.get_system_health()
        
        # Determine overall status
        active_alerts = health_data.get('active_alerts_count', 0)
        if active_alerts > 0:
            status = "warning" if active_alerts < 3 else "error"
        else:
            status = "healthy"
        
        return HealthResponse(
            status=status,
            timestamp=datetime.now().isoformat(),
            uptime_seconds=health_data['uptime_seconds'],
            active_sessions=health_data.get('active_sessions', 0),
            total_requests=health_data.get('total_requests', 0),
            agent_health=health_data.get('agent_health', {}),
            active_alerts=health_data.get('active_alerts', []),
            system_metrics={
                'memory_usage_mb': health_data.get('memory_usage_mb', 0),
                'cpu_usage_percent': health_data.get('cpu_usage_percent', 0)
            }
        )
    
    @app.get("/metrics")
    async def get_metrics(monitor = Depends(get_monitor_dep)):
        """시스템 메트릭 조회 (모니터링용)"""
        return monitor.get_all_metrics_summary()
    
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
