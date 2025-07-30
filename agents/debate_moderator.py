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
        self.max_tokens = LLM_CONFIGS["anthropic"]["max_tokens"]
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

        logger.info(f"토론 진행 시작 - 참여 Agent 수: {len(agent_responses)}")

        if len(agent_responses) < 2:
            logger.info("Agent가 1개 이하이므로 토론 생략")
            return self.handle_single_agent_response(state)

        try:
            # 1단계: 응답 간 차이점 분석
            differences_analysis = await self.analyze_response_differences(agent_responses)

            # 2단계: 토론 시뮬레이션
            debate_results = await self.simulate_expert_debate(
                agent_responses, differences_analysis, user_question, issue_info
            )

            # 3단계: 최종 통합 응답 생성
            final_recommendation = await self.synthesize_final_solution(
                agent_responses, debate_results, user_question
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

        analysis_prompt = f"""
다음 제조업 전문가들의 응답을 비교 분석해주세요:
{responses_text}

다음 관점에서 체계적으로 분석하세요:
1. 주요 공통점 - 모든 전문가가 동의하는 부분
2. 핵심 차이점 - 접근 방식이나 해결책의 차이
3. 상충되는 의견 - 서로 다른 관점이나 우선순위
4. 보완 가능한 부분 - 한 전문가의 의견이 다른 의견을 보완하는 부분

JSON 형식으로 응답해주세요:
{{
    "common_points": ["공통점1", "공통점2", "공통점3"],
    "differences": [
        {{"area": "차이영역", "details": ["차이점1", "차이점2"]}},
        {{"area": "접근방식", "details": ["차이점3", "차이점4"]}}
    ],
    "conflicts": [
        {{"issue": "상충이슈", "positions": ["입장1", "입장2"]}}
    ],
    "complementary_aspects": [
        {{"combination": "보완조합", "benefit": "시너지효과"}}
    ]
}}
"""

        try:
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=1200,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=self.temperature
            )

            analysis_result = json.loads(response.content[0].text)
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
제조업 장비 문제에 대한 전문가 패널 토론을 시뮬레이션해주세요.

사용자 문제: {user_question}

참여 전문가들과 그들의 초기 의견:
"""

        for agent in participants:
            agent_data = agent_responses[agent]
            description = self.participant_descriptions.get(agent, f"{agent} 전문가")
            # AgentResponse 객체인 경우 속성으로 접근
            if hasattr(agent_data, 'response'):
                response = agent_data.response[:500]  # 응답 요약
            else:
                response = agent_data.get('response', '')[:500]  # 응답 요약

            debate_prompt += f"""
{description}:
"{response}..."
"""

        debate_prompt += f"""

분석된 차이점:
- 공통점: {', '.join(differences.get('common_points', [])[:3])}
- 주요 차이점: {differences.get('differences', [])}
- 상충점: {differences.get('conflicts', [])}

이제 이 전문가들이 건설적인 토론을 진행합니다:

1. 각 전문가는 자신의 전문성을 바탕으로 다른 전문가의 의견에 대해 질문하고 의견을 제시
2. 서로의 접근법의 장단점을 분석하고 토론
3. 상충되는 부분에 대해서는 근거를 바탕으로 설득하거나 절충안 모색
4. 최종적으로 모든 관점을 종합한 최적의 해결책에 합의

토론 과정을 상세히 시뮬레이션하고, 최종 합의점을 도출해주세요.

JSON 형식으로 응답:
{{
    "debate_rounds": [
        {{
            "round": 1,
            "topic": "주요 쟁점1",
            "discussions": [
                {{"speaker": "GPT", "statement": "GPT 전문가의 발언"}},
                {{"speaker": "Gemini", "statement": "Gemini 전문가의 응답"}},
                {{"speaker": "Clova", "statement": "Clova 전문가의 의견"}}
            ]
        }},
        {{
            "round": 2,
            "topic": "주요 쟁점2",
            "discussions": [...]
        }}
    ],
    "consensus_points": [
        "합의사항1: 모든 전문가가 동의한 핵심 해결책",
        "합의사항2: 통합된 접근 방법",
        "합의사항3: 우선순위 및 실행 계획"
    ],
    "final_agreement": "최종 합의된 종합 해결책",
    "synthesis_notes": "각 전문가의 강점을 어떻게 통합했는지에 대한 설명"
}}
"""

        try:
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=2800,
                messages=[{"role": "user", "content": debate_prompt}],
                temperature=self.temperature
            )

            debate_result = json.loads(response.content[0].text)
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
                                      user_question: str) -> Dict[str, Any]:
        """최종 통합 해결책 생성"""

        synthesis_prompt = f"""
사용자 질문: {user_question}

전문가 토론 결과를 바탕으로 최종 권장사항을 작성해주세요.

합의 사항: {', '.join(debate_results.get('consensus_points', []))}
최종 합의: {debate_results.get('final_agreement', '')}
통합 노트: {debate_results.get('synthesis_notes', '')}

다음을 포함한 완성도 높은 최종 응답을 작성하세요:

JSON 형식:
{{
    "executive_summary": "핵심 해결책 요약 (2-3문장으로 전문가들이 합의한 최적 솔루션)",
    "immediate_actions": [
        {{"step": 1, "action": "즉시 조치사항1", "time": "소요시간", "priority": "high/medium/low", "responsible": "담당자"}},
        {{"step": 2, "action": "즉시 조치사항2", "time": "소요시간", "priority": "high/medium/low", "responsible": "담당자"}}
    ],
    "detailed_solution": [
        {{"phase": "1단계: 진단", "actions": ["세부행동1", "세부행동2"], "estimated_time": "예상시간", "resources": "필요자원"}},
        {{"phase": "2단계: 해결", "actions": ["세부행동3", "세부행동4"], "estimated_time": "예상시간", "resources": "필요자원"}},
        {{"phase": "3단계: 검증", "actions": ["세부행동5", "세부행동6"], "estimated_time": "예상시간", "resources": "필요자원"}}
    ],
    "cost_estimation": {{
        "parts": "부품 교체 비용 추정", 
        "labor": "인건비 추정", 
        "total": "총 예상비용 범위",
        "cost_breakdown": ["비용항목1", "비용항목2"]
    }},
    "safety_precautions": [
        "안전수칙1: 작업 전 필수 확인사항",
        "안전수칙2: 작업 중 주의사항", 
        "안전수칙3: 작업 후 점검사항"
    ],
    "prevention_measures": [
        "예방법1: 정기 점검 방안",
        "예방법2: 운영 개선 방안"
    ],
    "success_indicators": [
        "성공지표1: 측정 가능한 개선 지표",
        "성공지표2: 성과 확인 방법"
    ],
    "alternative_approaches": [
        "대안1: 비용 최소화 접근법",
        "대안2: 시간 단축 접근법"
    ],
    "expert_consensus": "전문가들이 합의한 핵심 포인트와 각 전문가의 기여 요약",
    "confidence_level": 0.85,
    "recommended_followup": "후속 조치 및 모니터링 권장사항"
}}
"""

        try:
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": synthesis_prompt}],
                temperature=self.temperature
            )

            final_solution = json.loads(response.content[0].text)
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
                structure_prompt = f"""
다음 {agent_name} 전문가의 응답을 체계적으로 구조화해주세요:

사용자 질문: {user_question}
전문가 응답: {agent_response}

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
                    max_tokens=2000,
                    messages=[{"role": "user", "content": structure_prompt}],
                    temperature=0.3
                )
                
                final_recommendation = json.loads(response.content[0].text)
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