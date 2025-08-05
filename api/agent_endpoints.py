"""개별 Agent API 엔드포인트"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging
from datetime import datetime

# 기존 conversation_manager 제거 - SessionManager로 완전 대체
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
from typing import Union, Dict, Any, List
import re

_agents: Dict[str, Any] = {}

def extract_user_info_from_messages(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """대화에서 사용자 정보 추출"""
    user_info = {
        "name": None,
        "problem": None,
        "issues": []
    }
    
    for message in messages:
        if message.get("role") == "user":
            content = message.get("content", "")
            
            # 이름 추출 패턴
            name_patterns = [
                r"제?\s*(?:이름은|성함은)\s*([가-힣]{2,4})",
                r"저는\s*([가-힣]{2,4})(?:입니다|이에요|예요)",
                r"([가-힣]{2,4})(?:입니다|이에요|예요).*(?:문제|고민)"
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, content)
                if match and not user_info["name"]:
                    user_info["name"] = match.group(1)
                    break
            
            # 문제 상황 추출
            problem_keywords = ["금", "균열", "크랙", "설비", "장비", "문제", "고장", "불량", "이상"]
            if any(keyword in content for keyword in problem_keywords):
                user_info["problem"] = "설비/장비 관련 문제"
                user_info["issues"].append(content)
    
    return user_info

def get_agent(agent_name: str) -> Union[GPTAgent, GeminiAgent, ClovaAgent, AnthropicClient]:
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
    """Agent별 독립 세션으로 대화 연속성 보장"""
    try:
        from core.simple_memory_store import memory_store
        from datetime import datetime
        
        # Agent별 고유 세션 ID 생성
        if request.session_id:
            session_id = request.session_id
        else:
            # Agent별 기본 세션: gpt_user_session, gemini_user_session 등
            session_id = f"{agent_name}_user_session"
        
        # 세션 생성 또는 기존 세션 사용
        print(f"🔍 세션 조회 시도: {session_id}")
        session_data = await memory_store.get_session(session_id)
        print(f"🔍 세션 조회 결과: {session_data}")
        
        if not session_data:
            # 새 세션 생성
            session_data = {
                'session_id': session_id,
                'user_id': f"user_{agent_name}",
                'issue_code': "GENERAL",
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'conversation_count': 0,
                'conversation_history': []
            }
            save_result = await memory_store.set_session(session_id, session_data)
            print(f"✅ 새 세션 생성: {session_id}, 저장 결과: {save_result}")
        else:
            print(f"✅ 기존 세션 사용: {session_id}")
        
        # 이전 대화 기록 가져오기
        conversation_history = await memory_store.get_conversation_history(session_id)
        
        # Agent 실행 및 응답 생성
        agent = get_agent(agent_name)
        
        # 대화 기록을 메시지 형태로 변환
        messages = []
        for conv in conversation_history:
            if isinstance(conv, dict):
                user_msg = conv.get('user_message', '')
                bot_response = conv.get('bot_response', '')
                if user_msg:
                    messages.append({"role": "user", "content": user_msg})
                if bot_response:
                    # [agent_name] 접두사 제거
                    clean_response = bot_response
                    if bot_response.startswith(f"[{agent_name}]"):
                        clean_response = bot_response[len(f"[{agent_name}]"):].strip()
                    messages.append({"role": "assistant", "content": clean_response})
        
        # 현재 메시지 추가
        messages.append({"role": "user", "content": request.message})
        
        print(f"🔍 {agent_name} 에이전트 - 전체 메시지 수: {len(messages)}")
        print(f"🔍 대화 히스토리 수: {len(conversation_history)}")
        if len(messages) > 1:
            print(f"🔍 이전 대화 있음 - 첫 메시지: {messages[0]['content'][:50]}...")
        
        # 대화 기록이 없다면 강제로 대화 컨텍스트 생성
        if len(conversation_history) == 0 and len(messages) == 1:
            print(f"⚠️ {agent_name} 에이전트 - 대화 기록이 없습니다. 새 대화로 처리합니다.")
        elif len(conversation_history) > 0 and len(messages) == 1:
            print(f"⚠️ {agent_name} 에이전트 - 대화 기록은 있지만 메시지 변환에 실패했습니다.")
            # 직접 대화 기록을 텍스트로 변환하여 컨텍스트에 추가
            context_text = ""
            for conv in conversation_history:
                if isinstance(conv, dict):
                    user_msg = conv.get('user_message', '')
                    bot_response = conv.get('bot_response', '')
                    if user_msg:
                        context_text += f"사용자: {user_msg}\n"
                    if bot_response:
                        clean_response = bot_response
                        if bot_response.startswith(f"[{agent_name}]"):
                            clean_response = bot_response[len(f"[{agent_name}]"):].strip()
                        context_text += f"어시스턴트: {clean_response}\n"
            
            if context_text:
                # 현재 메시지에 이전 대화 컨텍스트를 포함
                messages[-1]["content"] = f"이전 대화:\n{context_text}\n현재 질문: {request.message}"
                print(f"✅ {agent_name} 에이전트 - 대화 컨텍스트를 현재 메시지에 포함했습니다.")
        
        # 사용자 정보 추출 (첫 대화에서 이름 등 추출)
        user_info = extract_user_info_from_messages(messages)
        
        # Agent별 응답 생성 방식
        if agent_name == "claude":
            # Anthropic client 사용
            from utils.llm_clients import AnthropicClient
            if isinstance(agent, AnthropicClient):
                response_text = await agent.generate_simple_response(messages)
                model_details = {"model": "claude-3-5-sonnet", "provider": "anthropic"}
            else:
                raise ValueError("Claude agent not properly initialized")
        else:
            # 기존 Agent 클래스 사용
            # AgentState 생성
            from models.agent_state import AgentState
            
            agent_state = AgentState(
                session_id=session_id,
                conversation_count=len(messages),
                response_type="first_question" if len(messages) == 1 else "follow_up",
                user_message=request.message,
                issue_code="GENERAL",
                user_id=user_info.get("name") or f"user_{agent_name}",
                issue_classification=None,
                question_category=None,
                rag_context={},
                selected_agents=[agent_name],
                selection_reasoning=f"Direct {agent_name} agent request",
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
                conversation_history=conversation_history,  # 원본 대화 히스토리 형태 유지
                processing_steps=[],
                total_processing_time=0.0,
                timestamp=datetime.now(),
                error=None,
                performance_metrics={},
                resource_usage={},
                failed_agents=None
            )
            
            
            
            if hasattr(agent, 'analyze_and_respond'):
                # analyze_and_respond 메서드 사용
                agent_response = await agent.analyze_and_respond(agent_state)
                response_text = agent_response.response
                model_details = {
                    "model": agent_response.model_used,
                    "provider": agent_name,
                    "confidence": str(agent_response.confidence),
                    "processing_time": str(agent_response.processing_time)
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
        
        # 응답을 공통 세션에 저장
        print(f"🔍 대화 저장 시도: {session_id}")
        save_result = await memory_store.add_conversation(
            session_id, 
            request.message, 
            f"[{agent_name}] {response_text}"
        )
        print(f"✅ 대화 저장 결과: {save_result}")
        
        # 응답 생성
        return AgentChatResponse(
            response=response_text,
            session_id=session_id,
            agent_name=agent_name,
            model_details=model_details,
            conversation_length=len(conversation_history) + 1,
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
    from core.simple_memory_store import memory_store
    import uuid
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    session_data = {
        'session_id': session_id,
        'user_id': "agent_user",
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'conversation_count': 0,
        'conversation_history': []
    }
    await memory_store.set_session(session_id, session_data)
    return {"session_id": session_id, "message": "새 세션이 생성되었습니다."}

@agent_router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """세션 정보 조회"""
    from core.simple_memory_store import memory_store
    session_data = await memory_store.get_session(session_id)
    if session_data:
        return {
            "session_id": session_data['session_id'],
            "user_id": session_data['user_id'],
            "created_at": session_data['created_at'],
            "updated_at": session_data['updated_at']
        }
    else:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

@agent_router.get("/session/{session_id}/history")
async def get_conversation_history_endpoint(session_id: str):
    """대화 히스토리 조회"""
    from core.simple_memory_store import memory_store
    history = await memory_store.get_conversation_history(session_id)
    return {
        "session_id": session_id,
        "messages": history
    }

@agent_router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """세션 초기화"""
    from core.simple_memory_store import memory_store
    success = await memory_store.delete_session(session_id)
    if success:
        return {"message": f"세션 {session_id}가 초기화되었습니다."}
    else:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")