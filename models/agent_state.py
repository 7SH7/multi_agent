"""Agent state model for LangGraph workflow."""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class ConversationHistory(BaseModel):
    """대화 기록 모델"""
    message: str
    sender: str  # 'user' or 'bot'
    timestamp: datetime
    session_id: str


class ProcessingStep(BaseModel):
    """처리 단계 모델"""
    step_name: str
    status: str  # 'started', 'completed', 'failed'
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class AgentState(TypedDict):
    """LangGraph 워크플로우 상태"""

    # 세션 정보 (연속 대화 지원)
    session_id: str
    conversation_count: int
    response_type: str  # "first_question" | "follow_up"

    # 사용자 입력
    user_message: str
    issue_code: Optional[str]
    user_id: Optional[str]

    # RAG 분류 결과
    issue_classification: Optional[Dict[str, Any]]  # RAG 분류 정보
    question_category: Optional[str]  # 질문 카테고리
    rag_context: Optional[Dict[str, Any]]  # 검색된 컨텍스트

    # Dynamic Branch 결과
    selected_agents: Optional[List[str]]  # 선택된 Agent들
    selection_reasoning: Optional[str]  # 선택 근거

    # Multi-Agent 응답
    agent_responses: Optional[Dict[str, Dict[str, Any]]]  # Agent별 개별 응답
    response_quality_scores: Optional[Dict[str, float]]  # Agent별 품질 점수

    # Debate 결과
    debate_rounds: Optional[List[Dict[str, Any]]]  # 토론 기록
    consensus_points: Optional[List[str]]  # 합의 사항
    final_recommendation: Optional[Dict[str, Any]]  # 최종 권장사항

    # 기존 필드들 (호환성 유지)
    equipment_type: Optional[str]
    equipment_kr: Optional[str]
    problem_type: Optional[str]
    root_causes: Optional[List[Dict[str, Any]]]
    severity_level: Optional[str]
    analysis_confidence: Optional[float]

    # 세션 관리
    conversation_history: List[Dict[str, Any]]
    processing_steps: List[str]
    total_processing_time: Optional[float]
    timestamp: datetime
    error: Optional[str]

    # 모니터링
    performance_metrics: Optional[Dict[str, Any]]
    resource_usage: Optional[Dict[str, Any]]