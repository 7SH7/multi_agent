"""GPT 기반 종합 분석 전문가 Agent"""

import openai
from typing import Dict, List, Optional, Any
from agents.base_agent import BaseAgent, AgentConfig, AgentResponse, AgentError
from config.settings import LLM_CONFIGS
from utils.knowledge_connector import get_knowledge_connector
import logging

logger = logging.getLogger(__name__)

class GPTAgent(BaseAgent):
    """GPT 기반 종합 분석 및 논리적 해결책 전문가"""

    def __init__(self):
        config = AgentConfig(
            name="GPT",
            specialty="종합 분석 및 논리적 해결책",
            model=LLM_CONFIGS["openai"]["model"],
            max_tokens=LLM_CONFIGS["openai"]["max_tokens"],
            temperature=LLM_CONFIGS["openai"]["temperature"]
        )
        super().__init__(config)

        # OpenAI 클라이언트 초기화
        self.client = openai.AsyncOpenAI(
            api_key=LLM_CONFIGS["openai"]["api_key"]
        )
        
        # Knowledge Connector 초기화
        self.knowledge_connector = get_knowledge_connector()

    async def analyze_and_respond(self, state: Dict[str, Any]) -> AgentResponse:
        """GPT 기반 종합 분석"""

        self.validate_input(state)

        user_question = state.get('user_message', '')
        rag_context = state.get('rag_context', {})
        issue_classification = state.get('issue_classification', {})
        conversation_history = state.get('conversation_history', [])
        
        print(f"🔍 GPT Agent - conversation_history 수: {len(conversation_history)}")
        if conversation_history:
            print(f"🔍 GPT Agent - 첫 번째 대화: {conversation_history[0]}")
        else:
            print(f"🔍 GPT Agent - conversation_history가 비어있음")
        
        # 동적 토큰 한계 계산
        from utils.token_manager import get_token_manager
        token_manager = get_token_manager()
        dynamic_max_tokens = token_manager.get_agent_specific_limit('gpt', state)

        # Knowledge Base 컨텍스트 추가
        knowledge_context = self._get_knowledge_context(user_question, issue_classification or {})
        
        # 프롬프트 구성
        prompt = self.build_analysis_prompt(user_question, rag_context or {}, issue_classification or {}, conversation_history, knowledge_context)

        try:
            logger.info(f"GPT Agent 분석 시작 - 모델: {self.model}")

            # 대화 히스토리를 포함한 메시지 구성
            messages = [{"role": "system", "content": self.get_system_prompt()}]
            
            # 이전 대화 히스토리 추가
            if conversation_history:
                for conv in conversation_history:
                    if isinstance(conv, dict):
                        if conv.get("role") and conv.get("content"):
                            messages.append(conv)
            
            # 현재 질문 추가
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=dynamic_max_tokens
            )

            response_text = response.choices[0].message.content
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

            confidence = self.calculate_confidence(len(response_text), token_usage)

            logger.info(f"GPT Agent 분석 완료 - 토큰 사용: {token_usage['total_tokens']}")

            return self.create_response(
                response_text=response_text,
                confidence=confidence,
                processing_time=0.0,  # 실제 시간은 base_agent에서 계산
                token_usage=token_usage
            )

        except openai.RateLimitError as e:
            logger.error(f"GPT API 요청 한도 초과: {str(e)}")
            raise AgentError("API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.", self.name, "RATE_LIMIT")

        except openai.AuthenticationError as e:
            logger.error(f"GPT API 인증 오류: {str(e)}")
            raise AgentError("API 인증에 실패했습니다. API 키를 확인해주세요.", self.name, "AUTH_ERROR")

        except Exception as e:
            logger.error(f"GPT Agent 분석 오류: {str(e)}")
            raise AgentError(f"분석 중 오류가 발생했습니다: {str(e)}", self.name, "ANALYSIS_ERROR")

    def get_system_prompt(self) -> str:
        """GPT Agent 시스템 프롬프트"""
        return """당신은 제조업 장비 문제 해결 전문가입니다.
        
전문성:
- 종합적이고 논리적인 문제 분석
- 단계별 해결 방법 제시
- 안전성을 최우선으로 고려
- 체계적이고 구조화된 접근
- 다양한 관점에서의 종합적 판단

응답 시 다음을 포함하세요:
1. 문제 상황 정확한 진단
2. 단계별 해결 방법 (우선순위 포함)
3. 예상 소요 시간 및 필요 자원
4. 안전 주의사항 (필수)
5. 장기적 예방 방안
6. 위험도 평가 및 대안 제시

응답은 명확하고 실행 가능한 형태로 작성하세요."""

    def build_analysis_prompt(self, question: str, rag_context: Dict, issue_info: Dict, conversation_history: Optional[List] = None, knowledge_context: str = "") -> str:
        """분석 프롬프트 구성"""

        # RAG 컨텍스트 정리
        context_text = ""
        if rag_context.get('chroma_results'):
            context_text += "관련 기술 문서:\n"
            for i, result in enumerate(rag_context['chroma_results'][:3], 1):
                # RAGResult 객체와 dictionary 둘 다 처리
                if hasattr(result, 'content'):
                    content = result.content[:300]
                else:
                    content = result.get('content', '')[:300]
                context_text += f"{i}. {content}...\n"

        if rag_context.get('elasticsearch_results'):
            context_text += "\n관련 해결 사례:\n"
            for i, result in enumerate(rag_context['elasticsearch_results'][:3], 1):
                # RAGResult 객체와 dictionary 둘 다 처리
                if hasattr(result, 'content'):
                    content = result.content[:300]
                else:
                    content = result.get('content', '')[:300]
                context_text += f"{i}. {content}...\n"

        # 대화 기록 정리
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n이전 대화 기록:\n"
            for i, conv in enumerate(conversation_history[-3:], 1):  # 최근 3개만
                if isinstance(conv, dict):
                    user_msg = conv.get('user_message', '')
                    bot_response = conv.get('bot_response', '')
                    timestamp = conv.get('timestamp', '')
                    agents_used = conv.get('agents_used', [])
                    if user_msg:
                        conversation_context += f"{i}. [{timestamp[:16]}] 사용자: {user_msg}\n"
                        if bot_response:
                            conversation_context += f"   어시스턴트: {bot_response[:200]}...\n"
                        if agents_used:
                            conversation_context += f"   → 참여 전문가: {', '.join(agents_used)}\n"

        # 이슈 컨텍스트 정리
        issue_context = ""
        if issue_info.get('issue_info') and not issue_info['issue_info'].get('error'):
            issue_data = issue_info['issue_info']
            issue_context = f"""
이슈 정보:
- 문제 유형: {issue_data.get('description', '')}
- 카테고리: {issue_data.get('category', '')}
- 심각도: {issue_data.get('severity', '')}
- 일반적 원인: {', '.join(issue_data.get('common_causes', []))}
- 표준 해결책: {', '.join(issue_data.get('standard_solutions', []))}
- 영향 부품: {', '.join(issue_data.get('affected_components', []))}
"""

        return f"""
사용자 질문: {question}

{conversation_context}

{issue_context}

배경 정보:
{context_text}

{knowledge_context}

위 정보를 종합하여 제조업 전문가 관점에서 분석하고 해결책을 제시해주세요.
이전 대화가 있다면 그 맥락을 고려하여 연속성 있는 답변을 제공하세요.
특히 다음 사항을 중점적으로 다뤄주세요:

1. 문제의 근본 원인 분석
2. 체계적이고 단계별 해결 방법
3. 안전성과 실용성을 모두 고려한 접근
4. 예방을 위한 장기적 관점
5. 비용과 효과를 고려한 우선순위

전문적이면서도 현장에서 실제로 적용 가능한 솔루션을 제공해주세요.
"""

    def get_strengths(self) -> List[str]:
        """GPT Agent의 강점"""
        return ["종합적분석", "단계적해결", "안전고려", "논리적사고", "체계적접근"]

    def get_focus_areas(self) -> List[str]:
        """GPT Agent의 중점 영역"""
        return ["문제진단", "해결절차", "위험평가", "예방방안", "종합판단"]

    def calculate_confidence(self, response_length: int, token_usage: Optional[Dict[str, int]] = None) -> float:
        """GPT 응답 신뢰도 계산"""
        base_confidence = 0.8  # GPT는 기본적으로 높은 신뢰도

        # 응답 길이 기반 조정
        if response_length > 800:  # 충분히 상세한 응답
            base_confidence += 0.1
        elif response_length < 200:  # 너무 간단한 응답
            base_confidence -= 0.2

        # 토큰 사용량 기반 조정
        if token_usage:
            completion_tokens = token_usage.get('completion_tokens', 0)
            if completion_tokens > 1000:  # 매우 상세한 분석
                base_confidence += 0.05
            elif completion_tokens < 300:  # 간단한 응답
                base_confidence -= 0.1

        return min(0.95, max(0.3, base_confidence))

    def _get_knowledge_context(self, question: str, issue_info: Dict) -> str:
        """Knowledge Base에서 관련 컨텍스트 정보 추출"""
        try:
            context_parts = []
            
            # 장비 타입 추출 시도
            equipment_type = None
            equipment_keywords = {
                'PRESS_HYDRAULIC': ['유압', '프레스', 'press', 'hydraulic'],
                'PRESS_PRODUCTIVITY': ['생산성', 'productivity', '프레스'],
                'WELDING_ROBOT_KAMP': ['용접', '로봇', 'welding', 'robot', 'kamp'],
                'PAINTING_COATING': ['도장', '코팅', 'painting', 'coating'],
                'PAINTING_EQUIPMENT': ['도장장비', 'painting equipment'],
                'ASSEMBLY_PARTS': ['조립', '부품', 'assembly', 'parts']
            }
            
            for eq_type, keywords in equipment_keywords.items():
                if any(keyword in question.lower() for keyword in keywords):
                    equipment_type = eq_type
                    break
            
            # 이슈 코드에서 장비 타입 추출
            issue_code = issue_info.get('issue_code') if issue_info else None
            if not equipment_type and issue_code:
                for eq_type in equipment_keywords.keys():
                    if eq_type.lower() in issue_code.lower():
                        equipment_type = eq_type
                        break
            
            # Knowledge Base 컨텍스트 생성
            if equipment_type:
                kb_context = self.knowledge_connector.get_context_for_agent(
                    equipment_type=equipment_type,
                    issue_code=issue_code
                )
                if kb_context:
                    context_parts.append(f"[지식베이스 정보]\n{kb_context}")
            
            # 이슈별 해결책 검색
            if issue_code:
                solution_info = self.knowledge_connector.search_solutions(issue_code)
                if solution_info.get('found'):
                    issue_data = solution_info['issue']
                    context_parts.append(f"[해결책 데이터베이스]\n문제: {issue_data.get('description', '')}")
                    if issue_data.get('standard_solutions'):
                        context_parts.append(f"표준 해결책: {', '.join(issue_data['standard_solutions'][:3])}")
            
            return "\n\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            logger.warning(f"Knowledge context 생성 중 오류: {str(e)}")
            return ""