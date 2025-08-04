"""Claude 기반 전문가 토론 진행자"""

import anthropic
import json
from datetime import datetime
from typing import Dict, Any, List
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

        agent_responses = state.get('agent_responses', {})
        user_question = state.get('user_message', '')
        issue_info = state.get('issue_classification', {})
        conversation_history = state.get('conversation_history', [])

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
                'processing_steps': state.get('processing_steps', []) + ['debate_completed']
            })

            logger.info("토론 진행 완료")
            return state

        except Exception as e:
            logger.error(f"토론 진행 오류: {str(e)}")
            return self.handle_debate_failure(state, agent_responses)

    async def analyze_response_differences(self, agent_responses: Dict[str, Dict]) -> Dict[str, Any]:
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

        analysis_prompt = f'''
제조업 전문가 응답 비교 분석:
{responses_text}

다음 JSON 형식으로 응답해주세요:
{{
    "common_points": [
        "공통점 1",
        "공통점 2"
    ],
    "differences": [
        "차이점 1",
        "차이점 2"
    ],
    "conflicts": [
        {{
            "topic": "충돌 주제",
            "details": "구체적인 충돌 내용"
        }}
    ],
    "complementary_aspects": [
        {{
            "topic": "상호 보완적인 부분",
            "details": "어떻게 상호 보완적인지에 대한 설명"
        }}
    ]
}}
'''

        try:
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=self.temperature
            )

            try:
                response_text = response.content[0].text.strip()
                # JSON 문자열 정리
                if response_text.startswith('```json'):
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif response_text.startswith('```'):
                    response_text = response_text.split('```')[1].split('```')[0].strip()
                
                analysis_result = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"차이 분석 처리 오류: {str(e)}")
                analysis_result = {
                    "differences": ["분석 처리 중 오류가 발생했습니다."],
                    "common_points": ["두 Agent 모두 문제 해결에 도움이 되는 조언을 제공했습니다."],
                    "synthesis_needed": True
                }
            logger.info("응답 차이 분석 완료")
            return analysis_result

        except json.JSONDecodeError as e:
            logger.warning(f"차이 분석 결과 파싱 실패: {str(e)}")
            return {
                "error": "분석 결과 파싱 실패",
                "raw_response": response.content[0].text,
                "common_points": ["분석 실패"],
                "differences": [],
                "conflicts": [],
                "complementary_aspects": []
            }
        except Exception as e:
            logger.error(f"응답 차이 분석 오류: {str(e)}")
            return {"error": f"분석 실패: {str(e)}"}

    async def simulate_expert_debate(self, agent_responses: Dict, differences: Dict,
                                   user_question: str, issue_info: Dict) -> Dict[str, Any]:
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

        debate_prompt += f"""
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
                response_text = response.content[0].text.strip()
                # 안전한 JSON 파싱 with fallback
                fallback_data = {
                    "debate_rounds": [
                        {
                            "round": 1,
                            "topic": "전문가 의견 종합",
                            "discussions": [
                                {"speaker": "시스템", "statement": "텍스트 파싱으로 토론을 진행했습니다."}
                            ]
                        }
                    ],
                    "consensus_points": [
                        "전문가들의 의견을 종합하여 최적의 해결책을 제시합니다.",
                        "각 전문가의 강점을 활용한 통합 접근법을 적용합니다."
                    ],
                    "final_agreement": "전문가들의 개별 분석을 바탕으로 통합 해결책을 제시합니다.",
                    "synthesis_notes": "텍스트 기반 토론 분석 완료"
                }
                
                # 1차: JSON 파싱 시도
                debate_result = self._safe_json_parse(response_text, fallback_data)
                
                # 2차: JSON 파싱 실패시 텍스트 파싱 시도
                if debate_result == fallback_data:
                    logger.info("JSON 파싱 실패, 텍스트 파싱 시도")
                    debate_result = self._parse_debate_text(response_text, participants)
                    
            except Exception as e:
                logger.warning(f"토론 결과 처리 실패: {str(e)}")
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

        except json.JSONDecodeError as e:
            logger.warning(f"토론 결과 파싱 실패: {str(e)}")
            return {
                "error": "토론 결과 파싱 실패",
                "raw_response": response.content[0].text,
                "moderated_at": datetime.now().isoformat(),
                "participants": participants
            }
        except Exception as e:
            logger.error(f"토론 시뮬레이션 오류: {str(e)}")
            return {
                "error": f"토론 실패: {str(e)}",
                "moderated_at": datetime.now().isoformat()
            }

    async def synthesize_final_solution(self, agent_responses: Dict, debate_results: Dict,
                                      user_question: str, conversation_history: List = None) -> Dict[str, Any]:
        """최종 통합 해결책 생성"""

        # 대화 기록 컨텍스트 추가
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n이전 대화 맥락:\n"
            for i, conv in enumerate(conversation_history[-2:], 1):  # 최근 2개만
                if isinstance(conv, dict):
                    user_msg = conv.get('user_message', '')
                    timestamp = conv.get('timestamp', '')
                    if user_msg:
                        conversation_context += f"{i}. [{timestamp[:16]}] 이전 문의: {user_msg}\n"

        synthesis_prompt = f"""
질문: {user_question}

전문가 합의:
- {', '.join(debate_results.get('consensus_points', []))}
- {debate_results.get('final_agreement', '')}

간결한 최종 솔루션을 JSON으로:
{{
    "executive_summary": "핵심 해결책 요약",
    "immediate_actions": [
        {{"step": 1, "action": "조치1", "priority": "high"}}
    ],
    "cost_estimation": {{"total": "예상 비용"}},
    "safety_precautions": ["안전수칙1"],
    "expert_consensus": "전문가 합의점",
    "confidence_level": 0.85
}}
"""

        try:
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": synthesis_prompt}],
                temperature=self.temperature
            )

            try:
                response_text = response.content[0].text.strip()
                
                # 안전한 솔루션 파싱 with multiple fallbacks
                fallback_solution = {
                    "executive_summary": "전문가 분석을 바탕으로 한 종합 해결책을 제시합니다.",
                    "immediate_actions": [{"step": 1, "action": "전문가 권장사항 검토", "time": "즉시", "priority": "high", "responsible": "담당자"}],
                    "cost_estimation": {"parts": "분석 필요", "labor": "분석 필요", "total": "추후 산정"},
                    "safety_precautions": ["전문가 권장 안전수칙 준수"],
                    "expert_consensus": f"참여 전문가: {', '.join(agent_responses.keys())}",
                    "confidence_level": 0.75
                }
                
                # 1차: JSON 파싱 시도
                final_solution = self._safe_json_parse(response_text, fallback_solution)
                
                # 2차: JSON 파싱 실패시 텍스트 파싱 시도
                if final_solution == fallback_solution:
                    logger.info("JSON 파싱 실패, 텍스트 파싱 시도")
                    final_solution = self._parse_solution_text(response_text, agent_responses, debate_results)
                
                # 3차: 둘 다 실패하면 Agent 응답 기반 기본 솔루션 생성
                if not final_solution.get("executive_summary"):
                    logger.info("텍스트 파싱도 실패, 기본 솔루션 생성")
                    final_solution = self._generate_fallback_solution(agent_responses, debate_results)
                    
            except Exception as e:
                logger.error(f"최종 솔루션 처리 오류: {str(e)}")
                final_solution = self._generate_fallback_solution(agent_responses, debate_results)
            
            final_solution.update({
                "synthesized_at": datetime.now().isoformat(),
                "participating_agents": list(agent_responses.keys()),
                "debate_rounds_count": len(debate_results.get('debate_rounds', [])),
                "synthesis_method": "Claude-moderated expert debate"
            })

            logger.info("최종 솔루션 통합 완료")
            return final_solution

        except json.JSONDecodeError as e:
            logger.warning(f"최종 솔루션 파싱 실패: {str(e)}")
            return {
                "error": "최종 솔루션 파싱 실패",
                "raw_response": response.content[0].text,
                "synthesized_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"최종 솔루션 생성 오류: {str(e)}")
            return {
                "error": f"솔루션 생성 실패: {str(e)}",
                "synthesized_at": datetime.now().isoformat()
            }

    async def handle_single_agent_response(self, state: AgentState) -> AgentState:
        """단일 Agent 응답 처리 - 더욱 체계적인 구조화"""
        agent_responses = state.get('agent_responses', {})
        user_question = state.get('user_message', '')
        conversation_history = state.get('conversation_history', [])

        if len(agent_responses) == 1:
            agent_name, response_data = list(agent_responses.items())[0]
            
            # AgentResponse 객체인 경우 속성으로 접근
            if hasattr(response_data, 'response'):
                agent_response = response_data.response
                agent_confidence = response_data.confidence
            else:
                # dict인 경우 get으로 접근
                agent_response = response_data.get('response', '')
                agent_confidence = response_data.get('confidence', 0.7)
            
            # Claude를 사용해 단일 응답을 구조화
            try:
                # 대화 기록 컨텍스트 추가
                conversation_context = ""
                if conversation_history:
                    conversation_context = "\n이전 대화 맥락:\n"
                    for i, conv in enumerate(conversation_history[-2:], 1):  # 최근 2개만
                        if isinstance(conv, dict):
                            user_msg = conv.get('user_message', '')
                            timestamp = conv.get('timestamp', '')
                            if user_msg:
                                conversation_context += f"{i}. [{timestamp[:16]}] 이전 문의: {user_msg}\n"

                structure_prompt = f"""
다음 {agent_name} 전문가의 응답을 체계적으로 구조화해주세요:

사용자 질문: {user_question}
{conversation_context}
전문가 응답: {agent_response}

이전 대화 맥락이 있다면 연속성을 고려하여 구조화해주세요.
다음 JSON 형식으로 구조화해주세요:
{{
    "executive_summary": "핵심 해결책 요약 (2-3문장)",
    "immediate_actions": [
        {{"step": 1, "action": "즉시 조치사항", "time": "소요시간", "priority": "high/medium/low"}}
    ],
    "detailed_solution": [
        {{"phase": "단계명", "actions": ["세부행동1", "세부행동2"], "estimated_time": "예상시간"}}
    ],
    "cost_estimation": {{
        "parts": "부품비용", 
        "labor": "인건비", 
        "total": "총비용"
    }},
    "safety_precautions": ["안전수칙1", "안전수칙2"],
    "prevention_measures": ["예방법1", "예방법2"],
    "success_indicators": ["성공지표1", "성공지표2"],
    "alternative_approaches": ["대안1", "대안2"],
    "expert_consensus": "{agent_name} 전문가의 단독 분석 결과",
    "confidence_level": {agent_confidence},
    "recommended_followup": "후속조치 권장사항"
}}
"""
                
                response = self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[{"role": "user", "content": structure_prompt}],
                    temperature=0.3
                )
                
                # 안전한 파싱 with fallback
                fallback_recommendation = {
                    "executive_summary": f"{agent_name} 전문가의 분석 결과를 제시합니다.",
                    "immediate_actions": [{"step": 1, "action": "전문가 의견 검토", "time": "즉시", "priority": "medium"}],
                    "detailed_solution": [{"phase": "분석 결과", "actions": [agent_response[:200] + "..."], "estimated_time": "N/A"}],
                    "cost_estimation": {"parts": "분석 필요", "labor": "분석 필요", "total": "분석 필요"},
                    "safety_precautions": ["전문가 권장사항 준수"],
                    "prevention_measures": ["정기 점검 실시"],
                    "success_indicators": ["문제 해결 확인"],
                    "alternative_approaches": ["다른 전문가 의견 추가 검토"],
                    "expert_consensus": f"{agent_name} 단독 분석",
                    "confidence_level": agent_confidence,
                    "recommended_followup": "다른 전문가 의견도 함께 검토해보시기 바랍니다."
                }
                
                response_text = response.content[0].text.strip()
                final_recommendation = self._safe_json_parse(response_text, fallback_recommendation)
                logger.info(f"단일 Agent 응답 구조화 완료: {agent_name}")
                
            except Exception as e:
                logger.error(f"단일 Agent 응답 구조화 실패: {str(e)}")
                # 폴백: 기본 구조
                final_recommendation = {
                    "executive_summary": f"{agent_name} 전문가의 분석 결과를 제시합니다.",
                    "immediate_actions": [{"step": 1, "action": "전문가 의견 검토", "time": "즉시", "priority": "medium"}],
                    "detailed_solution": [{"phase": "분석 결과", "actions": [agent_response[:200] + "..."], "estimated_time": "N/A"}],
                    "cost_estimation": {"parts": "분석 필요", "labor": "분석 필요", "total": "분석 필요"},
                    "safety_precautions": ["전문가 권장사항 준수"],
                    "prevention_measures": ["정기 점검 실시"],
                    "success_indicators": ["문제 해결 확인"],
                    "alternative_approaches": ["다른 전문가 의견 추가 검토"],
                    "expert_consensus": f"{agent_name} 단독 분석",
                    "confidence_level": agent_confidence,
                    "recommended_followup": "다른 전문가 의견도 함께 검토해보시기 바랍니다."
                }
        else:
            final_recommendation = {
                "executive_summary": "분석할 전문가 응답이 없습니다.",
                "immediate_actions": [],
                "detailed_solution": [],
                "cost_estimation": {"parts": "N/A", "labor": "N/A", "total": "N/A"},
                "safety_precautions": [],
                "prevention_measures": [],
                "success_indicators": [],
                "alternative_approaches": [],
                "expert_consensus": "분석 실패",
                "confidence_level": 0.0,
                "recommended_followup": "시스템 관리자에게 문의하세요."
            }

        state.update({
            'final_recommendation': final_recommendation,
            'processing_steps': state.get('processing_steps', []) + ['single_agent_processed']
        })

        return state
    
    def _parse_analysis_text(self, text: str) -> dict:
        """분석 텍스트를 파싱해서 구조화"""
        result = {
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
    
    def _parse_debate_text(self, text: str, participants: list) -> dict:
        """토론 텍스트를 파싱해서 구조화"""
        result = {
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
    
    def _parse_solution_text(self, text: str, agent_responses: dict, debate_results: dict) -> dict:
        """솔루션 텍스트를 파싱해서 구조화"""
        result = {
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

    def _safe_json_parse(self, response_text: str, fallback_data: dict) -> dict:
        """안전한 JSON 파싱 with 강력한 정리"""
        try:
            # 마크다운 코드 블록 제거
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                # 일반 코드 블록도 제거
                parts = response_text.split('```')
                if len(parts) >= 3:
                    response_text = parts[1].strip()
            
            # 앞뒤 공백 및 불필요한 문자 제거
            response_text = response_text.strip()
            
            # JSON 문자열 시작/끝 확인 및 정리
            if not response_text.startswith('{'):
                # JSON 시작 부분 찾기
                start_idx = response_text.find('{')
                if start_idx != -1:
                    response_text = response_text[start_idx:]
            
            if not response_text.endswith('}'):
                # JSON 끝 부분 찾기 (뒤에서부터)
                end_idx = response_text.rfind('}')
                if end_idx != -1:
                    response_text = response_text[:end_idx + 1]
            
            # 잘못된 이스케이프 시퀀스 수정
            response_text = response_text.replace('\\\"', '"')
            response_text = response_text.replace('\\"', '"')
            
            # 제어 문자 제거
            import re
            response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)
            
            # JSON 파싱 시도
            result = json.loads(response_text)
            logger.info("JSON 파싱 성공")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 실패 (safe_parse): {str(e)}")
            logger.debug(f"파싱 실패한 텍스트 샘플: {response_text[:200]}...")
            return fallback_data
        except Exception as e:
            logger.error(f"JSON 처리 중 예외 발생: {str(e)}")
            return fallback_data

    def handle_debate_failure(self, state: AgentState, agent_responses: Dict) -> AgentState:
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
            'processing_steps': state.get('processing_steps', []) + ['debate_fallback']
        })

        return state
    
    def _generate_fallback_solution(self, agent_responses: dict, debate_results: dict) -> dict:
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