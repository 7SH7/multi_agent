"""Clova 기반 실무 경험 전문가 Agent"""

import httpx
from typing import Dict, Any, List, Optional
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
        self.api_key_id = LLM_CONFIGS["naver"].get("api_key_id", "")  # 설정에서 가져오기
        self.api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"
        self.request_id = "smartfactory-request"

    async def analyze_and_respond(self, state: Dict[str, Any]) -> AgentResponse:
        """Clova 기반 실무 분석"""

        self.validate_input(state)

        user_question = state.get('user_message', '')
        rag_context = state.get('rag_context', {})
        issue_classification = state.get('issue_classification', {})
        conversation_history = state.get('conversation_history', [])
        
        # 동적 토큰 한계 계산
        from utils.token_manager import get_token_manager
        token_manager = get_token_manager()
        dynamic_max_tokens = token_manager.get_agent_specific_limit('clova', state)

        # 프롬프트 구성
        prompt = self.build_practical_prompt(user_question, rag_context, issue_classification, conversation_history)

        try:
            logger.info(f"Clova Agent 분석 시작 - 모델: {self.model}")

            # Clova API 호출
            response_data = await self._call_clova_api(prompt, dynamic_max_tokens)

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

    async def _call_clova_api(self, prompt: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Clova API 호출"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
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
            "maxTokens": max_tokens or self.config.max_tokens,
            "temperature": self.config.temperature,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True
        }

        try:
            logger.info(f"Clova API 호출 - URL: {self.api_url}")
            logger.info(f"Clova API 키 길이: {len(self.api_key)}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )

                logger.info(f"Clova API 응답 코드: {response.status_code}")
                
                if response.status_code == 401:
                    logger.warning(f"Clova API 인증 실패 - 응답: {response.text}")
                    return self._create_fallback_response(prompt)
                elif response.status_code != 200:
                    error_msg = f"Clova API 오류: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return self._create_fallback_response(prompt)

                # 스트리밍 응답 파싱
                return self._parse_streaming_response(response.text)
                
        except Exception as e:
            logger.error(f"Clova API 호출 중 예외 발생: {str(e)}")
            return self._create_fallback_response(prompt)

    def _parse_streaming_response(self, response_text: str) -> Dict[str, Any]:
        """Clova 스트리밍 응답 파싱"""
        try:
            lines = response_text.strip().split('\n')
            content_parts = []
            input_tokens = 0
            output_tokens = 0
            
            for line in lines:
                if line.startswith('data:'):
                    try:
                        import json
                        data_str = line[5:].strip()  # 'data:' 제거
                        if data_str and data_str != '[DONE]':
                            data = json.loads(data_str)
                            if 'message' in data and 'content' in data['message']:
                                content_parts.append(data['message']['content'])
                            if 'inputLength' in data:
                                input_tokens = data['inputLength']
                            if 'outputLength' in data:
                                output_tokens += data['outputLength']
                    except json.JSONDecodeError:
                        continue
            
            full_content = ''.join(content_parts)
            
            return {
                "result": {
                    "message": {
                        "content": full_content if full_content else "응답을 생성할 수 없습니다."
                    }
                },
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"스트리밍 응답 파싱 오류: {str(e)}")
            return {
                "result": {
                    "message": {
                        "content": "응답 파싱 중 오류가 발생했습니다."
                    }
                },
                "usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0
                }
            }
    
    def _create_fallback_response(self, prompt: str) -> Dict[str, Any]:
        """Clova API 실패 시 fallback 응답 생성"""
        fallback_content = f"""
실무 전문가 관점에서의 분석 (오프라인 모드):

{prompt[:200]}...에 대한 실무적 해결 방안:

1. 현장 상황 점검
   - 문제 발생 빈도와 패턴 확인
   - 기존 해결 시도 내역 검토
   - 현재 사용 중인 도구 및 자원 파악

2. 비용 효율적 해결책
   - 기존 장비 활용 방안 검토
   - 단계적 개선 계획 수립
   - 예산 범위 내 실현 가능한 대안 제시

3. 실행 계획
   - 우선순위에 따른 단계별 접근
   - 작업자 교육 및 안전 고려사항
   - 효과 측정 및 지속적 개선 방안

※ 현재 Clova API 연결 이슈로 인해 제한된 분석 결과입니다.
보다 정확한 분석을 위해서는 API 연결 상태를 확인해주세요.
"""
        
        return {
            "result": {
                "message": {
                    "content": fallback_content.strip()
                }
            },
            "usage": {
                "input_tokens": len(prompt) // 4,
                "output_tokens": len(fallback_content) // 4,
                "total_tokens": (len(prompt) + len(fallback_content)) // 4
            }
        }

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

    def build_practical_prompt(self, question: str, rag_context: Dict, issue_info: Dict, conversation_history: Optional[List] = None) -> str:
        """실무 중심 프롬프트 구성"""

        # 실무 사례 추출
        practical_cases = ""
        if rag_context and rag_context.get('elasticsearch_results'):
            practical_cases += "유사 사례 및 해결 방법:\n"
            for i, result in enumerate(rag_context['elasticsearch_results'][:3], 1):
                # RAGResult 객체와 dictionary 둘 다 처리
                if hasattr(result, 'content'):
                    content = result.content[:200]
                else:
                    content = result.get('content', '')[:200]
                practical_cases += f"{i}. {content}...\n"

        # 대화 기록 정리 (실무 관점) - 사용자 정보 추출 강화
        conversation_context = ""
        user_name = None
        user_problem = None
        
        if conversation_history:
            conversation_context = "\n이전 현장 상담 기록:\n"
            
            # 먼저 사용자 정보 추출
            for conv in conversation_history:
                if isinstance(conv, dict) and conv.get('role') == 'user':
                    content = conv.get('content', '')
                    # 이름 추출 패턴
                    name_patterns = [
                        r"제?\s*(?:이름은|성함은)\s*([가-힣]{2,4})",
                        r"저는\s*([가-힣]{2,4})(?:입니다|이에요|예요)",
                        r"([가-힣]{2,4})(?:입니다|이에요|예요)"
                    ]
                    for pattern in name_patterns:
                        import re
                        match = re.search(pattern, content)
                        if match and not user_name:
                            user_name = match.group(1)
                            break
                    
                    # 문제 상황 키워드
                    problem_keywords = ["금", "균열", "크랙", "설비", "장비", "문제", "고장", "불량", "이상"]
                    if any(keyword in content for keyword in problem_keywords):
                        user_problem = "설비/장비 관련 문제"
            
            # 사용자 정보가 있으면 컨텍스트에 추가
            if user_name or user_problem:
                conversation_context += f"[고객 정보] 이름: {user_name or '미확인'}, 문제: {user_problem or '미확인'}\n\n"
            
            # 대화 기록 추가
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
                        timestamp = conv.get('timestamp', '')
                        agents_used = conv.get('agents_used', [])
                        if user_msg:
                            conversation_context += f"{i}. [{timestamp[:16]}] 현장 문의: {user_msg}\n"
                            if agents_used:
                                conversation_context += f"   → 상담 전문가: {', '.join(agents_used)}\n"

        # 비용 및 실무 정보
        practical_context = ""
        if issue_info and issue_info.get('issue_info') and not issue_info['issue_info'].get('error'):
            issue_data = issue_info['issue_info']
            practical_context = f"""
현장 정보:
- 문제 상황: {issue_data.get('description', '')}
- 일반적 원인: {', '.join(issue_data.get('common_causes', [])[:3])}
- 검증된 해결책: {', '.join(issue_data.get('standard_solutions', [])[:3])}
"""

        return f"""
현장 문제: {question}

{conversation_context}

{practical_context}

참고 사례:
{practical_cases}

현장 전문가 관점에서 다음을 중점적으로 분석해주세요.
이전 현장 상담이 있다면 고객의 이름과 문제를 기억하며 그 연속성을 고려하여 답변하세요.
특히 고객 정보가 있다면 반드시 언급하여 개인화된 서비스를 제공하세요:

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

    def calculate_confidence(self, response_length: int, token_usage: Optional[Dict[str, int]] = None) -> float:
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