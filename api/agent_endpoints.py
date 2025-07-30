"""개별 Agent API 엔드포인트"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from pydantic import BaseModel
import logging

from core.conversation_manager import conversation_manager
from agents.gpt_agent import GPTAgent
from agents.gemini_agent import GeminiAgent  
from agents.clova_agent import ClovaAgent
from utils.llm_clients import AnthropicClient

logger = logging.getLogger(__name__)

# Router 생성
agent_router = APIRouter(prefix="/api", tags=["Individual Agents"])

# Request 모델
class AgentChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class AgentChatResponse(BaseModel):
    response: str
    session_id: str
    agent_name: str
    model_details: dict
    conversation_length: int
    timestamp: str
    
    class Config:
        protected_namespaces = ()

# Agent 인스턴스 생성 (lazy loading)
_agents = {}

def get_agent(agent_name: str):
    """Agent 인스턴스 가져오기 (lazy loading)"""
    if agent_name not in _agents:
        if agent_name == "gpt":
            _agents[agent_name] = GPTAgent()
        elif agent_name == "gemini":
            _agents[agent_name] = GeminiAgent()
        elif agent_name == "clova":
            _agents[agent_name] = ClovaAgent()
        elif agent_name == "claude":
            _agents[agent_name] = AnthropicClient()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")
    
    return _agents[agent_name]

async def process_agent_request(agent_name: str, request: AgentChatRequest) -> AgentChatResponse:
    """공통 Agent 요청 처리"""
    try:
        # 세션 ID 처리
        session_id = request.session_id
        if not session_id:
            session_id = conversation_manager.create_session()
        
        # 기존 대화 히스토리 가져오기
        messages = conversation_manager.get_messages_for_model(session_id)
        
        # 사용자 메시지 추가
        conversation_manager.add_message(session_id, "user", request.message)
        messages.append({"role": "user", "content": request.message})
        
        # Agent 가져오기 및 응답 생성
        agent = get_agent(agent_name)
        
        # Agent별 응답 생성 방식
        if agent_name == "claude":
            # Anthropic client 사용
            response_text = await agent.generate_simple_response(messages)
            model_details = {"model": "claude-3-5-sonnet", "provider": "anthropic"}
        else:
            # 기존 Agent 클래스 사용
            # AgentState 생성
            from models.agent_state import AgentState
            
            agent_state = AgentState()
            agent_state.update({
                'user_message': request.message,
                'conversation_history': messages[:-1],  # 현재 메시지 제외한 히스토리
                'rag_context': {},
                'issue_classification': {'category': 'general', 'confidence': 0.8}
            })
            
            if hasattr(agent, 'analyze_and_respond'):
                # analyze_and_respond 메서드 사용
                agent_response = await agent.analyze_and_respond(agent_state)
                response_text = agent_response.response
                model_details = {
                    "model": agent_response.model_used,
                    "provider": agent_name,
                    "confidence": agent_response.confidence,
                    "processing_time": agent_response.processing_time
                }
            elif hasattr(agent, 'analyze_issue'):
                # analyze_issue 메서드가 있는 경우
                agent_response = await agent.analyze_issue(
                    issue_description=request.message,
                    context="\\n".join([f"{msg['role']}: {msg['content']}" for msg in messages[:-1]]),
                    issue_code="MANUAL_TEST"
                )
                response_text = agent_response.get('response', '응답 생성 실패')
                model_details = {
                    "model": agent_response.get('model_used', 'unknown'),
                    "provider": agent_name,
                    "confidence": agent_response.get('confidence', 0.0)
                }
            else:
                response_text = f"{agent_name} Agent의 응답 메서드를 찾을 수 없습니다."
                model_details = {"error": f"No suitable method found for {agent_name}"}
        
        # 응답을 히스토리에 추가
        conversation_manager.add_message(
            session_id, "assistant", response_text, 
            agent_name=agent_name, 
            metadata=model_details
        )
        
        # 응답 생성
        from datetime import datetime
        return AgentChatResponse(
            response=response_text,
            session_id=session_id,
            agent_name=agent_name,
            model_details=model_details,
            conversation_length=len(conversation_manager.get_history(session_id)),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"{agent_name} Agent 오류: {str(e)}")
        
        # 과부하 에러인 경우 더 친절한 메시지
        if "overloaded" in str(e).lower():
            error_msg = f"{agent_name} 서버가 현재 과부하 상태입니다. 잠시 후 다시 시도해주세요."
            status_code = 503
        else:
            error_msg = f"{agent_name} Agent 처리 중 오류: {str(e)}"
            status_code = 500
            
        raise HTTPException(status_code=status_code, detail=error_msg)

# GPT API 엔드포인트
@agent_router.post("/gpt", response_model=AgentChatResponse)
async def chat_with_gpt(request: AgentChatRequest):
    """GPT Agent와 대화"""
    return await process_agent_request("gpt", request)

# Claude API 엔드포인트  
@agent_router.post("/claude", response_model=AgentChatResponse)
async def chat_with_claude(request: AgentChatRequest):
    """Claude Agent와 대화"""
    return await process_agent_request("claude", request)

# Gemini API 엔드포인트
@agent_router.post("/gemini", response_model=AgentChatResponse)
async def chat_with_gemini(request: AgentChatRequest):
    """Gemini Agent와 대화"""
    return await process_agent_request("gemini", request)

# Clova API 엔드포인트
@agent_router.post("/clova", response_model=AgentChatResponse)
async def chat_with_clova(request: AgentChatRequest):
    """Clova Agent와 대화"""
    return await process_agent_request("clova", request)

# 세션 관리 엔드포인트들
@agent_router.post("/session/new")
async def create_new_session():
    """새 대화 세션 생성"""
    session_id = conversation_manager.create_session()
    return {"session_id": session_id, "message": "새 세션이 생성되었습니다."}

@agent_router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """세션 정보 조회"""
    return conversation_manager.get_session_info(session_id)

@agent_router.get("/session/{session_id}/history")
async def get_conversation_history(session_id: str):
    """대화 히스토리 조회"""
    history = conversation_manager.get_history(session_id)
    return {
        "session_id": session_id,
        "messages": [msg.dict() for msg in history]
    }

@agent_router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """세션 초기화"""
    success = conversation_manager.clear_session(session_id)
    if success:
        return {"message": f"세션 {session_id}가 초기화되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")