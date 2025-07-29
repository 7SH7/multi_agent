from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
from langgraph.graph import StateGraph, END
from models.agent_state import AgentState
from agents.rag_classifier import RAGClassifier
from agents.gpt_agent import GPTAgent
from agents.gemini_agent import GeminiAgent
from agents.clova_agent import ClovaAgent
from agents.debate_moderator import DebateModerator
from .dynamic_branch import DynamicAgentSelector
from .session_manager import SessionManager

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

    def _create_workflow(self) -> StateGraph:
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
                "gpt_only": "gpt_agent",
                "gemini_only": "gemini_agent",
                "clova_only": "clova_agent",
                "multiple_agents": "gpt_agent"
            }
        )

        # Agent execution routing
        workflow.add_conditional_edges("gpt_agent", self._route_after_gpt, {"continue": "gemini_agent", "debate": "debate_moderator"})
        workflow.add_conditional_edges("gemini_agent", self._route_after_gemini, {"continue": "clova_agent", "debate": "debate_moderator"})
        workflow.add_conditional_edges("clova_agent", self._route_after_clova, {"debate": "debate_moderator"})

        # End workflow
        workflow.add_edge("debate_moderator", END)

        return workflow.compile()

    async def _execute_rag_classifier(self, state: AgentState) -> AgentState:
        return await self.rag_classifier.classify_and_search(state)

    async def _execute_agent_selector(self, state: AgentState) -> AgentState:
        return self.agent_selector.select_agents(state)

    async def _execute_gpt_agent(self, state: AgentState) -> AgentState:
        selected_agents = state.get('selected_agents', [])
        if 'gpt' in selected_agents:
            response = await self.gpt_agent.analyze_and_respond(state)
            agent_responses = state.get('agent_responses', {})
            agent_responses['gpt'] = response
            state['agent_responses'] = agent_responses
        return state

    async def _execute_gemini_agent(self, state: AgentState) -> AgentState:
        selected_agents = state.get('selected_agents', [])
        if 'gemini' in selected_agents:
            response = await self.gemini_agent.analyze_and_respond(state)
            agent_responses = state.get('agent_responses', {})
            agent_responses['gemini'] = response
            state['agent_responses'] = agent_responses
        return state

    async def _execute_clova_agent(self, state: AgentState) -> AgentState:
        selected_agents = state.get('selected_agents', [])
        if 'clova' in selected_agents:
            response = await self.clova_agent.analyze_and_respond(state)
            agent_responses = state.get('agent_responses', {})
            agent_responses['clova'] = response
            state['agent_responses'] = agent_responses
        return state

    async def _execute_debate_moderator(self, state: AgentState) -> AgentState:
        return await self.debate_moderator.moderate_debate(state)

    def _route_to_agents(self, state: AgentState) -> str:
        selected_agents = state.get('selected_agents', [])
        if len(selected_agents) == 1:
            return f"{selected_agents[0]}_only"
        return "multiple_agents"

    def _route_after_gpt(self, state: AgentState) -> str:
        selected_agents = state.get('selected_agents', [])
        return "continue" if 'gemini' in selected_agents else "debate"

    def _route_after_gemini(self, state: AgentState) -> str:
        selected_agents = state.get('selected_agents', [])
        return "continue" if 'clova' in selected_agents else "debate"

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

# Global instances
_workflow_manager = None

def create_enhanced_workflow() -> EnhancedWorkflowManager:
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = EnhancedWorkflowManager()
    return _workflow_manager

# For backward compatibility - lazy initialization
enhanced_workflow = None

def get_enhanced_workflow() -> EnhancedWorkflowManager:
    """지연 초기화로 workflow 반환"""
    global enhanced_workflow
    if enhanced_workflow is None:
        enhanced_workflow = create_enhanced_workflow()
    return enhanced_workflow