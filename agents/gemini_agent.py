"""Gemini 기반 기술 정확성 전문가 Agent"""

import google.generativeai as genai
from typing import Dict, List, Optional, Any
from agents.base_agent import BaseAgent, AgentConfig, AgentResponse, AgentError
from config.settings import LLM_CONFIGS
import logging

logger = logging.getLogger(__name__)

class GeminiAgent(BaseAgent):
    """Gemini 기반 기술적 정확성 및 수치 분석 전문가"""

    def __init__(self):
        config = AgentConfig(
            name="Gemini",
            specialty="기술적 정확성 및 수치 분석",
            model=LLM_CONFIGS["google"]["model"],
            max_tokens=LLM_CONFIGS["google"]["max_tokens"],
            temperature=LLM_CONFIGS["google"]["temperature"]
        )
        super().__init__(config)

        # Gemini 클라이언트 초기화
        genai.configure(api_key=LLM_CONFIGS["google"]["api_key"])
        self.model_instance = genai.GenerativeModel(self.model)

    async def analyze_and_respond(self, state: Dict[str, Any]) -> AgentResponse:
        """Gemini 기반 기술 분석"""

        self.validate_input(state)

        user_question = state.get('user_message', '')
        rag_context = state.get('rag_context', {})
        issue_classification = state.get('issue_classification', {})
        conversation_history = state.get('conversation_history', [])
        
        print(f"🔍 Gemini Agent - conversation_history 수: {len(conversation_history)}")
        if conversation_history:
            print(f"🔍 Gemini Agent - 첫 번째 대화: {conversation_history[0]}")
        else:
            print(f"🔍 Gemini Agent - conversation_history가 비어있음")
        
        # 동적 토큰 한계 계산  
        from utils.token_manager import get_token_manager
        token_manager = get_token_manager()
        dynamic_max_tokens = token_manager.get_agent_specific_limit('gemini', state)

        # 프롬프트 구성
        prompt = self.build_technical_prompt(user_question, rag_context or {}, issue_classification or {}, conversation_history)

        try:
            logger.info(f"Gemini Agent 분석 시작 - 모델: {self.model}, 토큰 한계: {dynamic_max_tokens}")

            # Gemini API 호출 (재시도 포함)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await self._generate_content_async(prompt)
                    break
                except Exception as e:
                    if "overloaded" in str(e) and attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 지수 백오프: 1s, 2s, 4s
                        logger.warning(f"Gemini 과부하, {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})")
                        import asyncio
                        await asyncio.sleep(wait_time)
                        continue
                    raise e

            response_text = response.text
            
            # 토큰 사용량 추정 (Gemini는 정확한 토큰 수를 제공하지 않음)
            estimated_tokens = len(response_text) // 4  # 대략적인 추정
            token_usage = {
                "estimated_total_tokens": estimated_tokens,
                "estimated_completion_tokens": estimated_tokens // 2
            }
            
            confidence = self.calculate_confidence(len(response_text), token_usage)

            logger.info(f"Gemini Agent 분석 완료 - 예상 토큰: {estimated_tokens}")

            return self.create_response(
                response_text=response_text,
                confidence=confidence,
                processing_time=0.0,
                token_usage=token_usage
            )

        except Exception as e:
            logger.error(f"Gemini Agent 분석 오류: {str(e)}")
            raise AgentError(f"기술 분석 중 오류가 발생했습니다: {str(e)}", self.name, "ANALYSIS_ERROR")

    async def _generate_content_async(self, prompt: str):
        """비동기 컨텐츠 생성"""
        import asyncio

        # Gemini는 비동기를 직접 지원하지 않으므로 executor 사용
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.model_instance.generate_content, prompt)

    def build_technical_prompt(self, question: str, rag_context: Dict, issue_info: Dict, conversation_history: Optional[List] = None) -> str:
        """기술적 분석 프롬프트 구성"""

        # 기술 데이터 추출
        technical_data = ""
        if rag_context.get('chroma_results'):
            technical_data += "기술 사양 및 데이터:\n"
            for i, result in enumerate(rag_context['chroma_results'][:3], 1):
                # RAGResult 객체와 dictionary 둘 다 처리
                if hasattr(result, 'content'):
                    content = result.content[:250]
                else:
                    content = result.get('content', '')[:250]
                if any(keyword in content.lower() for keyword in ['압력', '온도', '전류', '전압', '진동', '두께']):
                    technical_data += f"{i}. {content}...\n"

        # 대화 기록 정리
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n이전 기술 상담 기록:\n"
            for i, conv in enumerate(conversation_history[-3:], 1):  # 최근 3개만
                if isinstance(conv, dict):
                    # 메시지 형식과 기존 형식 모두 지원
                    if conv.get('role') == 'user':
                        user_msg = conv.get('content', '')
                        conversation_context += f"{i}. 사용자: {user_msg}\n"
                    elif conv.get('role') == 'assistant':
                        bot_msg = conv.get('content', '')
                        conversation_context += f"   → 이전 답변: {bot_msg[:100]}...\n"
                    else:
                        # 기존 형식 지원
                        user_msg = conv.get('user_message', '')
                        bot_response = conv.get('bot_response', '')
                        timestamp = conv.get('timestamp', '')
                        agents_used = conv.get('agents_used', [])
                        if user_msg:
                            conversation_context += f"{i}. [{timestamp[:16]}] 기술 문의: {user_msg}\n"
                            if bot_response:
                                conversation_context += f"   → 이전 답변: {bot_response[:200]}...\n"
                            if agents_used:
                                conversation_context += f"   → 분석 전문가: {', '.join(agents_used)}\n"

        # 이슈 기술 정보
        technical_context = ""
        if issue_info.get('issue_info') and not issue_info['issue_info'].get('error'):
            issue_data = issue_info['issue_info']
            technical_context = f"""
기술적 배경:
- 문제 유형: {issue_data.get('description', '')}
- 기술 카테고리: {issue_data.get('category', '')}
- 관련 부품: {', '.join(issue_data.get('affected_components', []))}
"""

        return f"""
사용자 기술 문의: {question}

{conversation_context}

{technical_context}

기술 자료:
{technical_data}

위 정보를 바탕으로 기술 전문가 관점에서 다음을 중점적으로 분석해주세요.
이전 기술 상담이 있다면 그 연속성을 고려하여 답변하세요:

1. 정확한 기술적 원인 분석
2. 수치 및 데이터 기반 접근
3. 공학적 계산 및 검증
4. 기술 표준 및 규격 준수
5. 성능 최적화 방안
6. 정밀한 측정 및 검사 방법

모든 제안은 기술적 근거와 함께 제시하고, 가능한 경우 구체적인 수치나 사양을 포함해주세요.
"""

    def get_strengths(self) -> List[str]:
        """Gemini Agent의 강점"""
        return ["기술정확성", "수치분석", "공학계산", "성능최적화", "정밀측정"]

    def get_focus_areas(self) -> List[str]:
        """Gemini Agent의 중점 영역"""
        return ["기술분석", "데이터검증", "성능측정", "규격준수", "최적화"]

    def calculate_confidence(self, response_length: int, token_usage: Optional[Dict[str, int]] = None) -> float:
        """Gemini 응답 신뢰도 계산"""
        base_confidence = 0.75  # Gemini 기본 신뢰도

        # 응답 길이 기반 조정
        if response_length > 600:
            base_confidence += 0.15
        elif response_length < 150:
            base_confidence -= 0.15

        # 기술적 키워드 존재 여부로 추가 가중치
        # (실제 구현에서는 response_text를 분석)
        base_confidence += 0.05  # 기본 기술 가중치

        return min(0.95, max(0.3, base_confidence))