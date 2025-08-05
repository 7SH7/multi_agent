"""API response models."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    user_message: str = Field(..., description="사용자 메시지")
    issue_code: Optional[str] = Field(None, description="이슈 코드")
    session_id: Optional[str] = Field(None, description="세션 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID")

class AgentAnalysis(BaseModel):
    """Agent 분석 결과"""
    agent_name: str
    specialty: str
    response: str
    confidence: float
    processing_time: str
    strengths: List[str]
    focus_areas: List[str]

class DebateRound(BaseModel):
    """토론 라운드"""
    round: int
    topic: str
    discussions: List[str]
    consensus_reached: Optional[str] = None

class ImmediateAction(BaseModel):
    """즉시 조치사항"""
    step: int
    action: str
    time: str
    priority: str  # 'high', 'medium', 'low'

class DetailedSolution(BaseModel):
    """상세 해결책"""
    phase: str
    actions: List[str]
    estimated_time: str

class CostEstimation(BaseModel):
    """비용 추정"""
    parts: str
    labor: str
    total: str

class FinalRecommendation(BaseModel):
    """최종 권장사항"""
    executive_summary: str
    immediate_actions: List[ImmediateAction]
    detailed_solution: List[DetailedSolution]
    cost_estimation: CostEstimation
    safety_precautions: List[str]
    prevention_measures: List[str]
    success_indicators: List[str]
    alternative_approaches: List[str]
    expert_consensus: str
    confidence_level: float
    recommended_followup: str

class FailedAgent(BaseModel):
    """실패한 Agent 정보"""
    agent_name: str
    error_message: str
    timestamp: str
    specialty: str

class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    session_id: str
    conversation_count: int
    response_type: str
    executive_summary: str
    detailed_solution: List[DetailedSolution]
    immediate_actions: List[ImmediateAction]
    safety_precautions: List[str]
    cost_estimation: CostEstimation
    confidence_level: float
    participating_agents: List[str]
    debate_rounds: int
    processing_time: float
    processing_steps: List[str]
    timestamp: str
    failed_agents: Optional[List[FailedAgent]] = Field(default=None, description="실패한 Agent 목록")

class SessionInfo(BaseModel):
    """세션 정보"""
    session_id: str
    status: str
    conversation_count: int
    issue_code: Optional[str]
    created_at: str
    total_processing_time: float

class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: str
    timestamp: str

class SessionInfoResponse(BaseModel):
    """세션 정보 응답 모델"""
    session_id: str
    status: str
    conversation_count: int
    issue_code: Optional[str]
    created_at: str
    total_processing_time: float
    agents_used: List[str] = Field(default_factory=list)
    total_debates: int = 0

class AgentHealthInfo(BaseModel):
    """Agent 건강 상태 정보"""
    success_count: int
    error_count: int
    success_rate: float

class AlertInfo(BaseModel):
    """알림 정보"""
    rule: str
    level: str
    message: str
    timestamp: str

class SystemMetrics(BaseModel):
    """시스템 메트릭"""
    memory_usage_mb: float
    cpu_usage_percent: float

class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str  # 'healthy', 'warning', 'error'
    timestamp: str
    uptime_seconds: float
    active_sessions: int
    total_requests: int
    agent_health: Dict[str, AgentHealthInfo]
    active_alerts: List[AlertInfo]
    system_metrics: SystemMetrics