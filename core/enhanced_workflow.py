from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# 워크플로우 라우팅 수정: 2025-08-04
from langgraph.graph import StateGraph, END
from models.agent_state import AgentState
from agents.rag_classifier import RAGClassifier
from agents.gpt_agent import GPTAgent
from agents.gemini_agent import GeminiAgent
from agents.clova_agent import ClovaAgent
from agents.debate_moderator import DebateModerator
from .dynamic_branch import DynamicAgentSelector
from .session_manager import SessionManager

logger = logging.getLogger(__name__)

@dataclass
class WorkflowState:
    session_id: str
    current_step: str
    completed_steps: List[str]
    error_count: int
    start_time: datetime
    processing_time: float
    metadata: Dict[str, Any]

@dataclass
class WorkflowResult:
    success: bool
    final_state: AgentState
    workflow_state: WorkflowState
    error_message: Optional[str]
    execution_time: float
    steps_completed: List[str]

class EnhancedWorkflowManager:
    def __init__(self):
        self.rag_classifier = RAGClassifier()
        self.agent_selector = DynamicAgentSelector()
        self.gpt_agent = GPTAgent()
        self.gemini_agent = GeminiAgent()
        self.clova_agent = ClovaAgent()
        self.debate_moderator = DebateModerator()
        self.session_manager = SessionManager()
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("rag_classifier", self._execute_rag_classifier)
        workflow.add_node("agent_selector", self._execute_agent_selector)
        workflow.add_node("gpt_agent", self._execute_gpt_agent)
        workflow.add_node("gemini_agent", self._execute_gemini_agent)
        workflow.add_node("clova_agent", self._execute_clova_agent)
        workflow.add_node("debate_moderator", self._execute_debate_moderator)

        # Set entry point
        workflow.set_entry_point("rag_classifier")

        # Add edges
        workflow.add_edge("rag_classifier", "agent_selector")

        # Conditional routing after agent selection
        workflow.add_conditional_edges(
            "agent_selector",
            self._route_to_agents,
            {
                "multiple_agents": "gpt_agent",  # 모든 경우를 multiple_agents로 처리
                END: END  # 선택된 Agent가 없을 경우 워크플로우 종료
            }
        )

        # Agent execution routing
        workflow.add_conditional_edges("gpt_agent", self._route_after_gpt, {"continue_gemini": "gemini_agent", "continue_clova": "clova_agent", "debate": "debate_moderator"})
        workflow.add_conditional_edges("gemini_agent", self._route_after_gemini, {"continue": "clova_agent", "debate": "debate_moderator"})
        workflow.add_conditional_edges("clova_agent", self._route_after_clova, {"debate": "debate_moderator"})

        # End workflow
        workflow.add_edge("debate_moderator", END)

        compiled_workflow = workflow.compile()
        return compiled_workflow

    async def _execute_rag_classifier(self, state: AgentState) -> AgentState:
        return await self.rag_classifier.classify_and_search(state)

    async def _execute_agent_selector(self, state: AgentState) -> AgentState:
        return self.agent_selector.select_agents(state)

    async def _execute_gpt_agent(self, state: AgentState) -> AgentState:
        selected_agents = state.get('selected_agents') or []
        # 대소문자 구분 없이 체크
        if any(agent.lower() == 'gpt' for agent in selected_agents):
            try:
                logger.info("GPT Agent 실행 시작")
                response = await self.gpt_agent.analyze_and_respond(state)
                agent_responses = state.get('agent_responses') or {}
                agent_responses['GPT'] = response  # 대문자로 저장
                state['agent_responses'] = agent_responses
                logger.info("GPT Agent 실행 성공")
                processing_steps = state.get('processing_steps') or []
                processing_steps.append('gpt_agent_completed')
                state['processing_steps'] = processing_steps
            except Exception as e:
                logger.error(f"GPT Agent 실행 실패: {str(e)}")
                # 실패한 Agent 정보를 상태에 기록
                failed_agents = state.get('failed_agents') or []
                failed_agents.append({
                    'agent_name': 'GPT',
                    'error_message': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'specialty': '종합분석 및 안전성'
                })
                state['failed_agents'] = failed_agents
                
                # 실패한 Agent의 응답도 agent_responses에 추가하여 DebateModerator가 처리할 수 있도록 함
                agent_responses = state.get('agent_responses') or {}
                agent_responses['GPT'] = {'error': str(e), 'agent_name': 'GPT', 'response': 'GPT Agent failed to generate a response.'}
                state['agent_responses'] = agent_responses

                # 처리 단계에 실패 기록 추가
                processing_steps = state.get('processing_steps') or []
                processing_steps.append('gpt_agent_failed')
                state['processing_steps'] = processing_steps
        return state

    async def _execute_gemini_agent(self, state: AgentState) -> AgentState:
        selected_agents = state.get('selected_agents') or []
        # 대소문자 구분 없이 체크
        if any(agent.lower() == 'gemini' for agent in selected_agents):
            try:
                logger.info("Gemini Agent 실행 시작")
                response = await self.gemini_agent.analyze_and_respond(state)
                agent_responses = state.get('agent_responses') or {}
                agent_responses['Gemini'] = response  # 대문자로 저장
                state['agent_responses'] = agent_responses
                logger.info("Gemini Agent 실행 성공")
                processing_steps = state.get('processing_steps') or []
                processing_steps.append('gemini_agent_completed')
                state['processing_steps'] = processing_steps
            except Exception as e:
                logger.error(f"Gemini Agent 실행 실패: {str(e)}")
                # 실패한 Agent 정보를 상태에 기록
                failed_agents = state.get('failed_agents') or []
                failed_agents.append({
                    'agent_name': 'Gemini',
                    'error_message': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'specialty': '기술적 정확성 및 수치 분석'
                })
                state['failed_agents'] = failed_agents
                
                # 처리 단계에 실패 기록 추가
                processing_steps = state.get('processing_steps') or []
                processing_steps.append('gemini_agent_failed')
                state['processing_steps'] = processing_steps
        return state

    async def _execute_clova_agent(self, state: AgentState) -> AgentState:
        selected_agents = state.get('selected_agents') or []
        # 대소문자 구분 없이 체크
        if any(agent.lower() == 'clova' for agent in selected_agents):
            try:
                logger.info("Clova Agent 실행 시작")
                response = await self.clova_agent.analyze_and_respond(state)
                agent_responses = state.get('agent_responses') or {}
                agent_responses['Clova'] = response  # 대문자로 저장
                state['agent_responses'] = agent_responses
                logger.info("Clova Agent 실행 성공")
                processing_steps = state.get('processing_steps') or []
                processing_steps.append('clova_agent_completed')
                state['processing_steps'] = processing_steps
            except Exception as e:
                logger.error(f"Clova Agent 실행 실패: {str(e)}")
                # 에러가 발생해도 workflow는 계속 진행하되, 에러 정보를 상태에 기록
                agent_responses = state.get('agent_responses') or {}
                agent_responses['Clova'] = {'error': str(e), 'agent_name': 'Clova'}
                state['agent_responses'] = agent_responses
                failed_agents = state.get('failed_agents') or []
                failed_agents.append({
                    'agent_name': 'Clova',
                    'error_message': str(e),
                    'timestamp': datetime.now().isoformat(),
                    'specialty': '실무 경험 및 비용 효율성'
                })
                state['failed_agents'] = failed_agents
                
                # 처리 단계에 실패 기록 추가
                processing_steps = state.get('processing_steps') or []
                processing_steps.append('clova_agent_failed')
                state['processing_steps'] = processing_steps
        return state

    async def _execute_debate_moderator(self, state: AgentState) -> AgentState:
        return await self.debate_moderator.moderate_debate(state)

    def _route_to_agents(self, state: AgentState) -> str:
        selected_agents = state.get('selected_agents') or []
        if not selected_agents:
            logger.warning("선택된 Agent가 없습니다. 워크플로우를 종료합니다.")
            return END  # 선택된 Agent가 없으면 워크플로우 종료
        else:
            # 단일 Agent든 다중 Agent든 모두 multiple_agents로 처리
            logger.info(f"선택된 Agent들: {selected_agents}, multiple_agents 라우트로 처리")
            return "multiple_agents"

    def _route_after_gpt(self, state: AgentState) -> str:
        selected_agents = state.get('selected_agents') or []
        # 대소문자 구분 없이 체크
        has_gemini = any(agent.lower() == 'gemini' for agent in selected_agents)
        has_clova = any(agent.lower() == 'clova' for agent in selected_agents)
        
        # Gemini가 선택되었고, 아직 실행되지 않았다면 Gemini로
        if has_gemini and 'gemini_agent_completed' not in state.get('processing_steps', []):
            return "continue_gemini"  # gemini_agent로
        # Clova가 선택되었고, 아직 실행되지 않았다면 Clova로
        elif has_clova and 'clova_agent_completed' not in state.get('processing_steps', []):
            return "continue_clova"   # clova_agent로 직접
        else:
            return "debate"

    def _route_after_gemini(self, state: AgentState) -> str:
        selected_agents = state.get('selected_agents') or []
        # 대소문자 구분 없이 체크
        has_clova = any(agent.lower() == 'clova' for agent in selected_agents)
        
        # Clova가 선택되었고, 아직 실행되지 않았다면 Clova로
        if has_clova and 'clova_agent_completed' not in state.get('processing_steps', []):
            return "continue"  # clova_agent로
        else:
            return "debate"

    def _route_after_clova(self, state: AgentState) -> str:
        return "debate"

    async def execute(self, state: AgentState) -> WorkflowResult:
        start_time = datetime.now()
        workflow_state = WorkflowState(
            session_id=state.get('session_id', ''),
            current_step='starting',
            completed_steps=[],
            error_count=0,
            start_time=start_time,
            processing_time=0.0,
            metadata={}
        )

        try:
            result_state = await self.workflow.ainvoke(state)
            execution_time = (datetime.now() - start_time).total_seconds()

            return WorkflowResult(
                success=True,
                final_state=result_state,
                workflow_state=workflow_state,
                error_message=None,
                execution_time=execution_time,
                steps_completed=result_state.get('processing_steps', [])
            )
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return WorkflowResult(
                success=False,
                final_state=state,
                workflow_state=workflow_state,
                error_message=str(e),
                execution_time=execution_time,
                steps_completed=workflow_state.completed_steps
            )

# Global instances - force recreation for fixes
_workflow_manager = None

def create_enhanced_workflow() -> EnhancedWorkflowManager:
    global _workflow_manager
    # Always create new instance to ensure latest code is used
    _workflow_manager = EnhancedWorkflowManager()
    return _workflow_manager

# For backward compatibility - lazy initialization
enhanced_workflow = None

def get_enhanced_workflow() -> EnhancedWorkflowManager:
    """지연 초기화로 workflow 반환"""
    global enhanced_workflow
    # Always create new instance to ensure latest code is used
    enhanced_workflow = create_enhanced_workflow()
    return enhanced_workflow