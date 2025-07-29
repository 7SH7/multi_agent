"""Clova 기반 실무 경험 전문가 Agent"""

import httpx
import json
from datetime import datetime
from typing import Dict, Any, List
from models.agent_state import AgentState
from agents.base_agent import BaseAgent, AgentConfig, AgentResponse, AgentError
from config.settings import LLM_CONFIGS
import logging

logger = logging.getLogger(__name__)

class ClovaAgent(BaseAgent):
    """Clova 기반 실무 경험 및 비용 효율성 전문가"""

    def __init__(self):
        config = AgentConfig(
            name="Clova",
            specialty="실무 경험 및 비용 효율성",
            model=LLM_CONFIGS["naver"]["model"],
            max_tokens=LLM_CONFIGS["naver"]["max_tokens"],
            temperature=LLM_CONFIGS["naver"]["temperature"]
        )
        super().__init__(config)

        # Clova API 설정
        self.api_key = LLM_CONFIGS["naver"]["api_key"]
        self.api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"

    async def analyze_and_respond(self, state: AgentState) -> AgentResponse:
        """Clova 기반 실무 분석"""

        self.validate_input(state)

        user_question = state.get('user_message', '')
        rag_context = state.get('rag_context', {})
        issue_classification = state.get('issue_classification', {})

        # 프롬프트 구성
        prompt = self.build_practical_prompt(user_question, rag_context, issue_classification)

        try:
            logger.info(f"Clova Agent 분석 시작 - 모델: {self.model}")

            # Clova API 호출
            response_data = await self._call_clova_api(prompt)

            response_text = response_data.get('result', {}).get('message', {}).get('content', '')

            if not response_text:
                raise AgentError("Clova API에서 유효한 응답을 받지 못했습니다", self.name, "EMPTY_RESPONSE")

            confidence = self.calculate_confidence(len(response_text))

            # 토큰 사용량 (Clova API 응답에서 추출)
            token_usage = {
                "input_tokens": response_data.get('usage', {}).get('input_tokens', 0),
                "output_tokens": response_data.get('usage', {}).get('output_tokens', 0),
                "total_tokens": response_data.get('usage', {}).get('total_tokens', 0)
            }

            logger.info(f"Clova Agent 분석 완료 - 토큰 사용: {token_usage.get('total_tokens', 0)}")

            return self.create_response(
                response_text=response_text,
                confidence=confidence,
                processing_time=0.0,
                token_usage=token_usage
            )

        except Exception as e:
            logger.error(f"Clova Agent 분석 오류: {str(e)}")
            raise AgentError(f"실무 분석 중 오류가 발생했습니다: {str(e)}", self.name, "ANALYSIS_ERROR")

    async def _call_clova_api(self, prompt: str) -> Dict[str, Any]:
        """Clova API 호출"""

        headers = {
            "X-NCP-APIGW-TEST-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": self.get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "topP": 0.8,
            "topK": 0,
            "maxTokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                error_msg = f"Clova API 오류: {response.status_code} - {response.text}"
                raise AgentError(error_msg, self.name, "API_ERROR")

            return response.json()

    def get_system_prompt(self) -> str:
        """Clova Agent 시스템 프롬프트"""
        return """당신은 제조업 현장에서 20년 이상 경험을 쌓은 실무 전문가입니다.

전문성:
- 풍부한 현장 경험과 실무 노하우
- 비용 효율적인 해결 방안 제시
- 현실적이고 실용적인 접근
- 작업자 관점에서의 실행 가능성 고려
- 제한된 자원으로 최대 효과를 내는 방법

응답 시 다음을 중점적으로 다뤄주세요:
1. 현장에서 실제로 적용 가능한 솔루션
2. 비용 대비 효과가 높은 방법
3. 작업자가 쉽게 이해하고 실행할 수 있는 절차
4. 기존 자원을 최대한 활용하는 방안
5. 비슷한 문제의 과거 해결 사례
6. 단계적 개선을 통한 점진적 해결

실무진이 바로 적용할 수 있는 구체적이고 현실적인 조언을 제공해주세요."""

    def build_practical_prompt(self, question: str, rag_context: Dict, issue_info: Dict) -> str:
        """실무 중심 프롬프트 구성"""

        # 실무 사례 추출
        practical_cases = ""
        if rag_context.get('elasticsearch_results'):
            practical_cases += "유사 사례 및 해결 방법:\n"
            for i, result in enumerate(rag_context['elasticsearch_results'][:3], 1):
                content = result.get('content', '')[:200]
                practical_cases += f"{i}. {content}...\n"

        # 비용 및 실무 정보
        practical_context = ""
        if issue_info.get('issue_info') and not issue_info['issue_info'].get('error'):
            issue_data = issue_info['issue_info']
            practical_context = f"""
현장 정보:
- 문제 상황: {issue_data.get('description', '')}
- 일반적 원인: {', '.join(issue_data.get('common_causes', [])[:3])}
- 검증된 해결책: {', '.join(issue_data.get('standard_solutions', [])[:3])}
"""

        return f"""
현장 문제: {question}

{practical_context}

참고 사례:
{practical_cases}

현장 전문가 관점에서 다음을 중점적으로 분석해주세요:

1. 현장에서 바로 적용 가능한 해결책
2. 최소 비용으로 최대 효과를 내는 방법
3. 기존 장비와 인력을 활용한 개선 방안
4. 단계별 실행 계획 (우선순위 포함)
5. 예상 비용 및 소요 시간
6. 작업자 안전 및 편의성 고려사항

특히 비용 효율성과 현실적 실행 가능성을 중시하여 답변해주세요.
이론보다는 실제 경험과 현장 노하우를 바탕으로 한 조언을 원합니다.
"""

    def get_strengths(self) -> List[str]:
        """Clova Agent의 강점"""
        return ["실무경험", "비용효율", "현장적용", "실용적접근", "자원활용"]

    def get_focus_areas(self) -> List[str]:
        """Clova Agent의 중점 영역"""
        return ["현장개선", "비용절감", "작업효율", "실행가능성", "경험활용"]

    def calculate_confidence(self, response_length: int) -> float:
        """Clova 응답 신뢰도 계산"""
        base_confidence = 0.7  # Clova 기본 신뢰도

        # 응답 길이 기반 조정
        if response_length > 500:
            base_confidence += 0.1
        elif response_length < 100:
            base_confidence -= 0.2

        # 실무 키워드 가중치 (비용, 현장, 실제 등)
        base_confidence += 0.05

        return min(0.90, max(0.3, base_confidence))