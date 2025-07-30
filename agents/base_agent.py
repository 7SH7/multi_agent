"""Base agent class for all specialized agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
import time
import logging

logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """Agent 설정"""
    name: str
    specialty: str
    model: str
    max_tokens: int = 2000
    temperature: float = 0.2
    timeout: int = 30
    max_retries: int = 3

class AgentResponse(BaseModel):
    """Agent 응답"""
    agent_name: str
    specialty: str
    response: str
    confidence: float
    processing_time: float
    model_used: str
    token_usage: Optional[Dict[str, int]] = None
    strengths: List[str]
    focus_areas: List[str]
    timestamp: str
    error: Optional[str] = None
    
    model_config = {"protected_namespaces": ()}

class AgentError(Exception):
    """Agent 관련 예외"""
    def __init__(self, message: str, agent_name: str, error_code: str = None):
        self.message = message
        self.agent_name = agent_name
        self.error_code = error_code
        super().__init__(self.message)

class BaseAgent(ABC):
    """모든 Agent의 기본 클래스"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.specialty = config.specialty
        self.model = config.model
        self.max_retries = config.max_retries
        self.timeout = config.timeout

    @abstractmethod
    async def analyze_and_respond(self, state: Dict[str, Any]) -> AgentResponse:
        """문제 분석 및 응답 생성 (하위 클래스에서 구현)"""
        pass

    def create_response(self,
                       response_text: str,
                       confidence: float,
                       processing_time: float,
                       token_usage: Dict[str, int] = None,
                       error: str = None) -> AgentResponse:
        """표준 응답 생성"""
        return AgentResponse(
            agent_name=self.name,
            specialty=self.specialty,
            response=response_text,
            confidence=confidence,
            processing_time=processing_time,
            model_used=self.model,
            token_usage=token_usage,
            strengths=self.get_strengths(),
            focus_areas=self.get_focus_areas(),
            timestamp=datetime.now().isoformat(),
            error=error
        )

    @abstractmethod
    def get_strengths(self) -> List[str]:
        """Agent의 강점 반환"""
        pass

    @abstractmethod
    def get_focus_areas(self) -> List[str]:
        """Agent의 중점 영역 반환"""
        pass

    async def safe_analyze(self, state: Dict[str, Any]) -> AgentResponse:
        """안전한 분석 실행 (에러 처리 포함)"""
        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                logger.info(f"{self.name} Agent 분석 시작 (시도 {attempt + 1}/{self.max_retries})")

                response = await self.analyze_and_respond(state)
                processing_time = time.time() - start_time

                logger.info(f"{self.name} Agent 분석 완료 (소요시간: {processing_time:.2f}초)")
                return response

            except Exception as e:
                logger.error(f"{self.name} Agent 오류 (시도 {attempt + 1}): {str(e)}")

                if attempt == self.max_retries - 1:
                    # 마지막 시도에서도 실패
                    processing_time = time.time() - start_time
                    return self.create_response(
                        response_text=f"분석 중 오류가 발생했습니다: {str(e)}",
                        confidence=0.0,
                        processing_time=processing_time,
                        error=str(e)
                    )

                # 재시도 전 대기
                await self._wait_before_retry(attempt)

    async def _wait_before_retry(self, attempt: int):
        """재시도 전 대기 (지수 백오프)"""
        wait_time = 2 ** attempt  # 2, 4, 8초
        logger.info(f"{self.name} Agent {wait_time}초 후 재시도")
        import asyncio
        await asyncio.sleep(wait_time)

    def validate_input(self, state: Dict[str, Any]) -> bool:
        """입력 유효성 검사"""
        required_fields = ['user_message']

        for field in required_fields:
            if field not in state or not state[field]:
                raise AgentError(
                    f"필수 필드 '{field}'가 없습니다",
                    self.name,
                    "MISSING_REQUIRED_FIELD"
                )

        return True

    def calculate_confidence(self, response_length: int, token_usage: Dict[str, int] = None) -> float:
        """응답 신뢰도 계산"""
        base_confidence = 0.7

        # 응답 길이 기반 조정
        if response_length > 500:
            base_confidence += 0.1
        elif response_length < 100:
            base_confidence -= 0.2

        # 토큰 사용량 기반 조정
        if token_usage:
            completion_tokens = token_usage.get('completion_tokens', 0)
            if completion_tokens > 800:
                base_confidence += 0.1
            elif completion_tokens < 200:
                base_confidence -= 0.1

        return min(0.95, max(0.1, base_confidence))