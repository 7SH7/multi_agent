"""Claude 기반 전문가 토론 진행자"""

import anthropic
from datetime import datetime
from typing import Dict, Any, List, Optional
from models.agent_state import AgentState
from config.settings import LLM_CONFIGS
import logging

logger = logging.getLogger(__name__)

class DebateModerator:
    """Claude 기반 Multi-Agent 토론 진행자"""

    def __init__(self):
        self.claude_client = anthropic.Anthropic(
            api_key=LLM_CONFIGS["anthropic"]["api_key"]
        )
        self.model = LLM_CONFIGS["anthropic"]["model"]
        from config.settings import AGENT_TOKEN_LIMITS
        self.max_tokens = AGENT_TOKEN_LIMITS["debate"]
        self.temperature = LLM_CONFIGS["anthropic"]["temperature"]

        # 참여자 설명
        self.participant_descriptions = {
            "GPT": "종합분석 및 안전성 중시 전문가 - 체계적이고 논리적인 접근을 선호",
            "Gemini": "기술적 정확성 및 공학적 접근 전문가 - 데이터와 수치를 중시",
            "Clova": "실무경험 및 비용효율성 중시 전문가 - 현장 적용성과 경제성을 우선시"
        }

    async def moderate_debate(self, state: AgentState) -> AgentState:
        """Agent들의 응답을 토론시키고 최종 결론 도출"""

        agent_responses = state.get('agent_responses') or {}
        user_question = state.get('user_message', '')
        issue_info = state.get('issue_classification') or {}
        conversation_history = state.get('conversation_history') or []

        logger.info(f"토론 진행 시작 - 참여 Agent 수: {len(agent_responses)}")

        if len(agent_responses) < 2:
            logger.info("Agent가 1개 이하이므로 토론 생략")
            return await self.handle_single_agent_response(state)

        try:
            # 1단계: 응답 간 차이점 분석
            differences_analysis = await self.analyze_response_differences(agent_responses)

            # 2단계: 토론 시뮬레이션
            debate_results = await self.simulate_expert_debate(
                agent_responses, differences_analysis, user_question, issue_info
            )

            # 3단계: 최종 통합 응답 생성
            final_recommendation = await self.synthesize_final_solution(
                agent_responses, debate_results, user_question, conversation_history
            )

            # 상태 업데이트
            state.update({
                'debate_rounds': [debate_results],
                'consensus_points': debate_results.get('consensus_points', []),
                'final_recommendation': final_recommendation,
                'processing_steps': (state.get('processing_steps') or []) + ['debate_completed']
            })

            logger.info("토론 진행 완료")
            return state

        except Exception as e:
            logger.error(f"토론 진행 오류: {str(e)}")
            return self.handle_debate_failure(state, agent_responses)

    async def analyze_response_differences(self, agent_responses: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 응답 간 차이점 분석"""

        responses_text = ""
        for agent_name, response_data in agent_responses.items():
            # AgentResponse 객체인 경우 속성으로 접근
            if hasattr(response_data, 'specialty'):
                specialty = response_data.specialty
                response = response_data.response
                confidence = response_data.confidence
            else:
                # dict인 경우 get으로 접근
                specialty = response_data.get('specialty', '')
                response = response_data.get('response', '')
                confidence = response_data.get('confidence', 0)

            responses_text += f"\n=== {agent_name} 전문가 ({specialty}) ===\n"
            responses_text += f"신뢰도: {confidence:.2f}\n"
            responses_text += f"의견: {response}\n"

        analysis_prompt = f"""
제조업 전문가 응답 비교 분석:
{responses_text}

다음 형식으로 간단히 답변해주세요 (JSON 없이):

공통점:
- 공통점1
- 공통점2

차이점:
- 차이점1  
- 차이점2
"""

        try:
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=self.temperature
            )

            try:
                # Claude API 응답 구조 안전하게 처리
                if hasattr(response, 'content') and response.content:
                    if isinstance(response.content, list) and len(response.content) > 0:
                        if hasattr(response.content[0], 'text'):
                            response_text = response.content[0].text.strip()
                        else:
                            response_text = str(response.content[0]).strip()
                    else:
                        response_text = str(response.content).strip()
                else:
                    response_text = str(response).strip()
                
                logger.info(f"Claude 응답 받음: {response_text[:100]}...")
                
                # 텍스트 응답을 파싱해서 구조화
                analysis_result = self._parse_analysis_text(response_text)
                
            except Exception as e:
                logger.error(f"차이 분석 처리 오류: {str(e)}")
                logger.error(f"응답 타입: {type(response)}")
                logger.error(f"응답 내용: {str(response)[:200]}")
                analysis_result = {
                    "differences": ["분석 처리 중 오류가 발생했습니다."],
                    "common_points": ["두 Agent 모두 문제 해결에 도움이 되는 조언을 제공했습니다."],
                    "synthesis_needed": True
                }
            logger.info("응답 차이 분석 완료")
            return analysis_result

        except Exception as e:
            logger.error(f"응답 차이 분석 오류: {str(e)}")
            return {"error": f"분석 실패: {str(e)}"}

    async def simulate_expert_debate(self, agent_responses: Dict[str, Any], differences: Dict[str, Any],
                                   user_question: str, issue_info: Dict[str, Any]) -> Dict[str, Any]:
        """전문가 간 토론 시뮬레이션"""

        participants = list(agent_responses.keys())

        # 토론 프롬프트 구성
        debate_prompt = f"""
제조업 문제: {user_question}

전문가 의견:
"""

        for agent in participants:
            agent_data = agent_responses[agent]
            # AgentResponse 객체인 경우 속성으로 접근
            if hasattr(agent_data, 'response'):
                response = agent_data.response[:200]  # 더 짧게 요약
            else:
                response = agent_data.get('response', '')[:200]  # 더 짧게 요약

            debate_prompt += f"{agent}: {response}...\n"

        debate_prompt += """
다음 형식으로 토론 결과를 정리해주세요 (JSON 없이):

합의점:
- 합의점1
- 합의점2

최종 해결책:
최종 합의된 해결책을 한 문장으로
"""

        try:
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": debate_prompt}],
                temperature=self.temperature
            )

            try:
                # Claude API 응답 구조 안전하게 처리
                if hasattr(response, 'content') and response.content:
                    if isinstance(response.content, list) and len(response.content) > 0:
                        if hasattr(response.content[0], 'text'):
                            response_text = response.content[0].text.strip()
                        else:
                            response_text = str(response.content[0]).strip()
                    else:
                        response_text = str(response.content).strip()
                else:
                    response_text = str(response).strip()
                
                logger.info(f"토론 Claude 응답: {response_text[:100]}...")
                
                # 텍스트 파싱으로 구조화
                debate_result = self._parse_debate_text(response_text, participants)
                    
            except Exception as e:
                logger.warning(f"토론 결과 처리 실패: {str(e)}")
                logger.warning(f"토론 응답 타입: {type(response)}")
                debate_result = {
                    "debate_rounds": [{"round": 1, "topic": "오류 복구", "discussions": [{"speaker": "시스템", "statement": "처리 오류가 발생했지만 전문가 의견은 정상 수집되었습니다."}]}],
                    "consensus_points": ["각 전문가의 전문성을 바탕으로 한 종합 분석"],
                    "final_agreement": "전문가 의견을 통합하여 최적의 해결방안을 제시합니다.",
                    "synthesis_notes": "오류 복구 완료"
                }
            
            debate_result['moderated_at'] = datetime.now().isoformat()
            debate_result['participants'] = participants

            logger.info(f"토론 시뮬레이션 완료 - {len(debate_result.get('debate_rounds', []))}라운드")
            return debate_result

        except Exception as e:
            logger.error(f"토론 시뮬레이션 오류: {str(e)}")
            return {
                "error": f"토론 실패: {str(e)}",
                "moderated_at": datetime.now().isoformat()
            }

    async def synthesize_final_solution(self, agent_responses: Dict[str, Any], debate_results: Dict[str, Any],
                                      user_question: str, conversation_history: Optional[List] = None) -> Dict[str, Any]:
        """최종 통합 해결책 생성"""

        # 대화 기록 컨텍스트 추가 - 사용자 정보 추출 강화
        conversation_context = ""
        user_name = None
        user_problem = None
        
        if conversation_history:
            conversation_context = "\n이전 대화 맥락:\n"
            
            # 사용자 정보 추출
            for conv in conversation_history:
                if isinstance(conv, dict):
                    # 메시지 형식 처리
                    if conv.get('role') == 'user':
                        content = conv.get('content', '')
                        # 이름 추출 - 패턴 강화
                        import re
                        name_patterns = [
                            r"제?\s*(?:이름은|성함은)\s*([가-힣]{2,4})",
                            r"저는\s*([가-힣]{2,4})(?:입니다|이에요|예요)",
                            r"([가-힣]{2,4})(?:입니다|이에요|예요)",
                            r"안녕하세요[.\s]*저는\s*([가-힣]{2,4})",
                            r"([가-힣]{2,4})라고?\s*합니다",
                            r"제\s*이름은?\s*([가-힣]{2,4})"
                        ]
                        for pattern in name_patterns:
                            match = re.search(pattern, content)
                            if match and not user_name:
                                user_name = match.group(1)
                                break
                        
                        # 문제 상황 키워드
                        problem_keywords = ["금", "균열", "크랙", "설비", "장비", "문제", "고장", "불량", "이상"]
                        if any(keyword in content for keyword in problem_keywords):
                            user_problem = "설비/장비 관련 문제"
                    
                    # 기존 형식 처리
                    user_msg = conv.get('user_message', '')
                    timestamp = conv.get('timestamp', '')
                    if user_msg:
                        conversation_context += f"[{timestamp[:16]}] 이전 문의: {user_msg}\n"
                        
                        # 이름과 문제 추출 (기존 형식에서도) - 강화된 패턴
                        import re
                        name_patterns = [
                            r"제?\s*(?:이름은|성함은)\s*([가-힣]{2,4})",
                            r"저는\s*([가-힣]{2,4})(?:입니다|이에요|예요)",
                            r"([가-힣]{2,4})(?:입니다|이에요|예요)",
                            r"안녕하세요[.\s]*저는\s*([가-힣]{2,4})",
                            r"([가-힣]{2,4})라고?\s*합니다",
                            r"제\s*이름은?\s*([가-힣]{2,4})"
                        ]
                        for pattern in name_patterns:
                            match = re.search(pattern, user_msg)
                            if match and not user_name:
                                user_name = match.group(1)
                                break
                        
                        problem_keywords = ["금", "균열", "크랙", "설비", "장비", "문제", "고장", "불량", "이상"]
                        if any(keyword in user_msg for keyword in problem_keywords):
                            user_problem = "설비/장비 관련 문제"
            
            # 사용자 정보가 있으면 컨텍스트에 추가
            if user_name or user_problem:
                conversation_context = f"\n**중요 고객 정보**: 이름={user_name or '미확인'}, 문제={user_problem or '미확인'}\n" + conversation_context

        synthesis_prompt = f"""
질문: {user_question}
{conversation_context}

전문가 합의:
- {', '.join(debate_results.get('consensus_points', []))}
- {debate_results.get('final_agreement', '')}

**절대 규칙**: 고객 정보에서 이름이 확인되었다면, 응답을 반드시 "○○○님,"으로 시작해야 합니다. 이름이 없으면 일반적으로 답변하세요.

간결한 최종 솔루션을 다음 형식으로 작성하세요 (JSON 없이):

핵심 해결책:
[고객 이름이 있다면 "○○○님,"] 핵심 해결책 요약

즉시 조치:
- 조치1
- 조치2

예상 비용:
총 예상 비용

안전 수칙:
- 안전수칙1
- 안전수칙2

전문가 합의:  
합의 내용 요약 (고객 상황 고려)
"""

        try:
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": synthesis_prompt}],
                temperature=self.temperature
            )

            try:
                # Claude API 응답 구조 안전하게 처리
                if hasattr(response, 'content') and response.content:
                    if isinstance(response.content, list) and len(response.content) > 0:
                        if hasattr(response.content[0], 'text'):
                            response_text = response.content[0].text.strip()
                        else:
                            response_text = str(response.content[0]).strip()
                    else:
                        response_text = str(response.content).strip()
                else:
                    response_text = str(response).strip()
                
                logger.info(f"솔루션 Claude 응답: {response_text[:100]}...")
                
                # 텍스트 파싱으로 구조화
                final_solution = self._parse_solution_text(response_text, agent_responses, debate_results)
                
            except Exception as e:
                logger.error(f"최종 솔루션 처리 오류: {str(e)}")
                logger.error(f"솔루션 응답 타입: {type(response)}")
                final_solution = self._generate_fallback_solution(agent_responses, debate_results)
            
            final_solution.update({
                "synthesized_at": datetime.now().isoformat(),
                "participating_agents": list(agent_responses.keys()),
                "debate_rounds_count": len(debate_results.get('debate_rounds', [])),
                "synthesis_method": "Claude-moderated expert debate"
            })

            logger.info("최종 솔루션 통합 완료")
            return final_solution

        except Exception as e:
            logger.error(f"최종 솔루션 생성 오류: {str(e)}")
            return self._generate_fallback_solution(agent_responses, debate_results)

    async def handle_single_agent_response(self, state: AgentState) -> AgentState:
        """단일 Agent 응답 처리"""
        agent_responses = state.get('agent_responses') or {}

        if len(agent_responses) == 1:
            agent_name, response_data = list(agent_responses.items())[0]
            
            # AgentResponse 객체인 경우 속성으로 접근
            if hasattr(response_data, 'response'):
                agent_response = getattr(response_data, 'response', '')
                agent_confidence = getattr(response_data, 'confidence', 0.7)
            else:
                # dict인 경우 get으로 접근
                agent_response = response_data.get('response', '') if isinstance(response_data, dict) else ''
                agent_confidence = response_data.get('confidence', 0.7) if isinstance(response_data, dict) else 0.7
            
            # 기본 구조화
            final_recommendation = {
                "executive_summary": f"{agent_name} 전문가의 분석 결과를 제시합니다.",
                "immediate_actions": [{"step": 1, "action": "전문가 의견 검토", "time": "즉시", "priority": "medium", "responsible": "담당자"}],
                "detailed_solution": [{"phase": "분석 결과", "actions": [agent_response[:200] + "..."], "estimated_time": "N/A"}],
                "cost_estimation": {"parts": "분석 필요", "labor": "분석 필요", "total": "분석 필요"},
                "safety_precautions": ["전문가 권장사항 준수"],
                "expert_consensus": f"{agent_name} 단독 분석",
                "confidence_level": agent_confidence
            }
        else:
            final_recommendation = {
                "executive_summary": "분석할 전문가 응답이 없습니다.",
                "immediate_actions": [],
                "detailed_solution": [],
                "cost_estimation": {"parts": "N/A", "labor": "N/A", "total": "N/A"},
                "safety_precautions": [],
                "expert_consensus": "분석 실패",
                "confidence_level": 0.0
            }

        state.update({
            'final_recommendation': final_recommendation,
            'processing_steps': (state.get('processing_steps') or []) + ['single_agent_processed']
        })

        return state
    
    def _parse_analysis_text(self, text: str) -> Dict[str, Any]:
        """분석 텍스트를 파싱해서 구조화"""
        result: Dict[str, Any] = {
            "common_points": [],
            "differences": [],
            "synthesis_needed": True
        }
        
        try:
            lines = text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if '공통점:' in line:
                    current_section = 'common'
                elif '차이점:' in line:
                    current_section = 'differences'
                elif line.startswith('- ') and current_section:
                    content = line[2:].strip()
                    if current_section == 'common':
                        result["common_points"].append(content)
                    elif current_section == 'differences':
                        result["differences"].append(content)
            
            # 기본값 설정
            if not result["common_points"]:
                result["common_points"] = ["두 전문가 모두 문제 해결을 위한 조언을 제공했습니다."]
            if not result["differences"]:
                result["differences"] = ["접근 방식에서 각자의 전문성이 반영되었습니다."]
                
        except Exception as e:
            logger.error(f"분석 텍스트 파싱 오류: {str(e)}")
            result = {
                "common_points": ["전문가들이 공통적으로 문제 해결을 위한 조언을 제공했습니다."],
                "differences": ["각 전문가의 관점과 접근법에 차이가 있습니다."],
                "synthesis_needed": True
            }
        
        return result
    
    def _parse_debate_text(self, text: str, participants: List[str]) -> Dict[str, Any]:
        """토론 텍스트를 파싱해서 구조화"""
        result: Dict[str, Any] = {
            "debate_rounds": [],
            "consensus_points": [],
            "final_agreement": "",
            "synthesis_notes": ""
        }
        
        try:
            lines = text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if '합의점:' in line:
                    current_section = 'consensus'
                elif '최종 해결책:' in line:
                    current_section = 'final'
                elif line.startswith('- ') and current_section == 'consensus':
                    result["consensus_points"].append(line[2:].strip())
                elif current_section == 'final' and not line.startswith('-'):
                    result["final_agreement"] = line.strip()
            
            # 기본값 설정
            if not result["consensus_points"]:
                result["consensus_points"] = ["전문가들이 협력하여 최적의 해결책을 도출했습니다."]
            if not result["final_agreement"]:
                result["final_agreement"] = "각 전문가의 강점을 통합한 종합 해결방안을 적용하시기 바랍니다."
            
            result["synthesis_notes"] = f"{len(participants)}명의 전문가가 참여한 종합 분석 결과"
                
        except Exception as e:
            logger.error(f"토론 텍스트 파싱 오류: {str(e)}")
            result = {
                "debate_rounds": [],
                "consensus_points": ["전문가 협력을 통한 최적 해결책 도출"],
                "final_agreement": "종합적인 접근을 통해 문제를 해결하시기 바랍니다.",
                "synthesis_notes": "전문가 토론 완료"
            }
        
        return result
    
    def _parse_solution_text(self, text: str, agent_responses: Dict[str, Any], debate_results: Dict[str, Any]) -> Dict[str, Any]:
        """솔루션 텍스트를 파싱해서 구조화"""
        result: Dict[str, Any] = {
            "executive_summary": "",
            "immediate_actions": [],
            "cost_estimation": {"parts": "", "labor": "", "total": ""},
            "safety_precautions": [],
            "expert_consensus": "",
            "confidence_level": 0.85
        }
        
        try:
            lines = text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if '핵심 해결책:' in line:
                    current_section = 'summary'
                elif '즉시 조치:' in line:
                    current_section = 'actions'
                elif '예상 비용:' in line:
                    current_section = 'cost'
                elif '안전 수칙:' in line:
                    current_section = 'safety'
                elif '전문가 합의:' in line:
                    current_section = 'consensus'
                elif line.startswith('- ') and current_section:
                    content = line[2:].strip()
                    if current_section == 'actions':
                        result["immediate_actions"].append({"step": len(result["immediate_actions"]) + 1, "action": content, "time": "즉시", "priority": "high", "responsible": "담당자"})
                    elif current_section == 'safety':
                        result["safety_precautions"].append(content)
                elif current_section and not line.startswith('-'):
                    if current_section == 'summary':
                        result["executive_summary"] = line.strip()
                    elif current_section == 'cost':
                        result["cost_estimation"]["total"] = line.strip()
                    elif current_section == 'consensus':
                        result["expert_consensus"] = line.strip()
            
            # 기본값 설정
            if not result["executive_summary"]:
                consensus_summary = ', '.join(debate_results.get('consensus_points', ['전문가 의견 통합']))[:100]
                result["executive_summary"] = f"전문가 분석 결과: {consensus_summary}"
            
            if not result["immediate_actions"]:
                result["immediate_actions"] = [{"step": 1, "action": "전문가 권장사항 검토 및 적용", "time": "즉시", "priority": "high", "responsible": "담당자"}]
            
            if not result["cost_estimation"]["total"]:
                result["cost_estimation"]["total"] = "상세 분석 후 산정"
            if not result["cost_estimation"]["parts"]:
                result["cost_estimation"]["parts"] = "부품 비용 분석 필요"
            if not result["cost_estimation"]["labor"]:
                result["cost_estimation"]["labor"] = "인건비 분석 필요"
            
            if not result["safety_precautions"]:
                result["safety_precautions"] = ["전문가 권장 안전수칙 준수"]
            
            if not result["expert_consensus"]:
                result["expert_consensus"] = f"참여 전문가: {', '.join(agent_responses.keys())}"
                
        except Exception as e:
            logger.error(f"솔루션 텍스트 파싱 오류: {str(e)}")
            result = {
                "executive_summary": "전문가 분석을 바탕으로 한 종합 해결책을 제시합니다.",
                "immediate_actions": [{"step": 1, "action": "전문가 권장사항 검토", "time": "즉시", "priority": "high", "responsible": "담당자"}],
                "cost_estimation": {"parts": "부품 비용 분석 필요", "labor": "인건비 분석 필요", "total": "추후 산정"},
                "safety_precautions": ["안전 수칙 준수"],
                "expert_consensus": f"참여 전문가: {', '.join(agent_responses.keys())}",
                "confidence_level": 0.75
            }
        
        return result
    
    def _generate_fallback_solution(self, agent_responses: Dict[str, Any], debate_results: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 응답 기반 기본 솔루션 생성 (최후의 fallback)"""
        try:
            if not agent_responses:
                return {
                    "executive_summary": "분석할 전문가 응답이 없습니다.",
                    "immediate_actions": [{"step": 1, "action": "시스템 관리자 문의", "time": "즉시", "priority": "high", "responsible": "사용자"}],
                    "cost_estimation": {"parts": "N/A", "labor": "N/A", "total": "N/A"},
                    "safety_precautions": ["시스템 점검 필요"],
                    "expert_consensus": "분석 실패",
                    "confidence_level": 0.0
                }
            
            # 가장 높은 신뢰도의 Agent 선택
            def get_confidence(item):
                agent_data = item[1]
                if hasattr(agent_data, 'confidence'):
                    return agent_data.confidence
                else:
                    return agent_data.get('confidence', 0)
            
            best_agent = max(agent_responses.items(), key=get_confidence)
            best_agent_data = best_agent[1]
            
            # AgentResponse 객체인 경우 속성으로 접근
            if hasattr(best_agent_data, 'response'):
                primary_response = best_agent_data.response
                confidence_level = best_agent_data.confidence
            else:
                primary_response = best_agent_data.get('response', '')
                confidence_level = best_agent_data.get('confidence', 0.5)
            
            # 기본 솔루션 생성
            solution = {
                "executive_summary": f"{best_agent[0]} 전문가의 분석을 기반으로 한 해결책을 제시합니다.",
                "immediate_actions": [
                    {"step": 1, "action": "전문가 권장사항 검토", "time": "즉시", "priority": "high", "responsible": "담당자"},
                    {"step": 2, "action": "세부 조치 계획 수립", "time": "1일 이내", "priority": "medium", "responsible": "관리자"}
                ],
                "cost_estimation": {
                    "parts": "세부 분석 후 산정",
                    "labor": "전문가 분석 필요", 
                    "total": "추후 견적 제공"
                },
                "safety_precautions": [
                    "전문가 권장 안전수칙 준수",
                    "작업 전 안전점검 실시"
                ],
                "expert_consensus": f"최고 신뢰도 전문가 {best_agent[0]}의 분석 결과",
                "confidence_level": max(confidence_level * 0.8, 0.3),  # 약간 낮춤
                "fallback_reason": "파싱 오류로 인한 기본 솔루션 제공",
                "primary_expert_response": primary_response[:300] + "..." if len(primary_response) > 300 else primary_response
            }
            
            return solution
            
        except Exception as e:
            logger.error(f"Fallback 솔루션 생성 실패: {str(e)}")
            return {
                "executive_summary": "시스템 오류가 발생했습니다. 관리자에게 문의하세요.",
                "immediate_actions": [{"step": 1, "action": "시스템 관리자 문의", "time": "즉시", "priority": "high", "responsible": "사용자"}],
                "cost_estimation": {"parts": "N/A", "labor": "N/A", "total": "N/A"},
                "safety_precautions": ["시스템 복구까지 대기"],
                "expert_consensus": "시스템 오류",
                "confidence_level": 0.0,
                "error": True
            }

    def handle_debate_failure(self, state: AgentState, agent_responses: Dict[str, Any]) -> AgentState:
        """토론 실패 시 폴백 처리"""

        # 가장 높은 신뢰도의 Agent 응답 선택
        if agent_responses:
            # 신뢰도 기준으로 최고 Agent 선택
            def get_confidence(item):
                agent_data = item[1]
                if hasattr(agent_data, 'confidence'):
                    return agent_data.confidence
                else:
                    return agent_data.get('confidence', 0)
            
            best_agent = max(agent_responses.items(), key=get_confidence)
            best_agent_data = best_agent[1]
            
            # AgentResponse 객체인 경우 속성으로 접근
            if hasattr(best_agent_data, 'response'):
                primary_response = best_agent_data.response
                confidence_level = best_agent_data.confidence
            else:
                primary_response = best_agent_data.get('response', '')
                confidence_level = best_agent_data.get('confidence', 0.5)

            fallback_recommendation = {
                "executive_summary": "토론 진행 중 오류가 발생하여 최고 신뢰도 전문가 의견을 제시합니다.",
                "primary_response": primary_response,
                "primary_agent": best_agent[0],
                "confidence_level": confidence_level,
                "fallback": True,
                "note": "토론 시뮬레이션에 실패했으나, 개별 전문가 분석은 정상적으로 완료되었습니다.",
                "synthesized_at": datetime.now().isoformat()
            }
        else:
            fallback_recommendation = {
                "error": "토론 실패 및 분석할 응답 없음",
                "synthesized_at": datetime.now().isoformat()
            }

        state.update({
            'final_recommendation': fallback_recommendation,
            'processing_steps': (state.get('processing_steps') or []) + ['debate_fallback']
        })

        return state