"""동적 Agent 선택 시스템"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from models.agent_state import AgentState
import logging

logger = logging.getLogger(__name__)

class SelectionRule(BaseModel):
    """Agent 선택 규칙"""
    category: str
    agents: List[str]
    confidence_threshold: float = 0.7
    max_agents: int = 3

class AgentSelectionResult(BaseModel):
    """Agent 선택 결과"""
    selected_agents: List[str]
    selection_reasoning: str
    confidence_adjustment: float
    selection_time: str
    rules_applied: List[str]

class DynamicAgentSelector:
    """최적 Agent 동적 선택기"""

    def __init__(self):
        # Agent별 전문성 정의
        self.agent_specialties = {
            "GPT": {
                "strengths": ["종합분석", "논리적사고", "단계적해결", "안전분석"],
                "best_for": ["전기문제", "복잡한진단", "안전분석", "종합판단"],
                "cost": "medium",
                "speed": "medium",
                "reliability": 0.85
            },
            "Gemini": {
                "strengths": ["기술적정확성", "수치분석", "공학계산", "성능최적화"],
                "best_for": ["기계문제", "치수불량", "성능최적화", "기술분석"],
                "cost": "low",
                "speed": "fast",
                "reliability": 0.80
            },
            "Clova": {
                "strengths": ["실무경험", "비용효율", "현장적용", "경험활용"],
                "best_for": ["품질문제", "작업개선", "비용최적화", "실무적용"],
                "cost": "low",
                "speed": "fast",
                "reliability": 0.75
            }
        }

        # 카테고리별 선택 규칙
        self.selection_rules = {
            "전기문제": SelectionRule(
                category="전기문제",
                agents=["GPT", "Gemini"],
                confidence_threshold=0.75
            ),
            "기계문제": SelectionRule(
                category="기계문제",
                agents=["Gemini", "Clova"],
                confidence_threshold=0.70
            ),
            "품질문제": SelectionRule(
                category="품질문제",
                agents=["Clova", "GPT"],
                confidence_threshold=0.70
            ),
            "안전문제": SelectionRule(
                category="안전문제",
                agents=["GPT", "Gemini", "Clova"],  # 안전은 모든 관점 필요
                confidence_threshold=0.80,
                max_agents=3
            ),
            "비용문제": SelectionRule(
                category="비용문제",
                agents=["Clova"],
                confidence_threshold=0.65
            ),
            "긴급문제": SelectionRule(
                category="긴급문제",
                agents=["GPT", "Gemini"],  # 빠른 응답
                confidence_threshold=0.75
            ),
            "일반문제": SelectionRule(
                category="일반문제",
                agents=["GPT"],
                confidence_threshold=0.70
            )
        }

    def select_agents(self, state: AgentState) -> AgentState:
        """최적 Agent 선택"""

        start_time = datetime.now()

        try:
            question_category = state.get('question_category', '일반문제')
            classification_info = state.get('issue_classification', {})
            confidence = classification_info.get('classification_confidence', 0.5)
            session_id = state.get('session_id', '')

            logger.info(f"Agent 선택 시작 - 카테고리: {question_category}, 신뢰도: {confidence}")

            # 기본 Agent 선택
            selection_result = self._apply_selection_rules(question_category, confidence, state)

            # 컨텍스트 기반 조정
            selection_result = self._adjust_based_on_context(selection_result, state)

            # 세션 히스토리 기반 조정
            selection_result = self._adjust_based_on_history(selection_result, state)

            # 결과 로깅
            logger.info(f"Agent 선택 완료 - 선택된 Agent: {selection_result.selected_agents}")

            # 상태 업데이트
            state.update({
                'selected_agents': selection_result.selected_agents,
                'selection_reasoning': selection_result.selection_reasoning,
                'agent_selection_result': selection_result.dict(),
                'processing_steps': state.get('processing_steps', []) + ['agent_selection_completed']
            })

            return state

        except Exception as e:
            logger.error(f"Agent 선택 오류: {str(e)}")
            # 폴백: 기본 GPT Agent 선택
            fallback_result = AgentSelectionResult(
                selected_agents=["GPT"],
                selection_reasoning=f"선택 오류로 인한 기본 Agent 사용: {str(e)}",
                confidence_adjustment=0.0,
                selection_time=datetime.now().isoformat(),
                rules_applied=["fallback"]
            )

            state.update({
                'selected_agents': ["GPT"],
                'selection_reasoning': fallback_result.selection_reasoning,
                'processing_steps': state.get('processing_steps', []) + ['agent_selection_fallback']
            })

            return state

    def _apply_selection_rules(self, category: str, confidence: float, state: AgentState) -> AgentSelectionResult:
        """선택 규칙 적용"""

        rule = self.selection_rules.get(category, self.selection_rules["일반문제"])
        selected_agents = rule.agents.copy()
        rules_applied = [f"category_rule_{category}"]

        # 신뢰도에 따른 Agent 추가/제거
        confidence_adjustment = 0.0

        if confidence < rule.confidence_threshold:
            # 신뢰도가 낮으면 더 많은 관점 필요
            available_agents = list(self.agent_specialties.keys())
            for agent in available_agents:
                if agent not in selected_agents and len(selected_agents) < rule.max_agents:
                    selected_agents.append(agent)
                    confidence_adjustment -= 0.05
                    rules_applied.append("low_confidence_expansion")
                    break

        # 특수 상황 처리
        issue_info = state.get('issue_classification', {}).get('issue_info', {})
        if not issue_info.get('error'):
            severity = issue_info.get('severity', '')
            if severity in ['높음', '매우높음']:
                # 심각한 문제는 다중 Agent 필요
                if len(selected_agents) < 2:
                    for agent in ["GPT", "Gemini"]:
                        if agent not in selected_agents:
                            selected_agents.append(agent)
                            rules_applied.append("high_severity_expansion")
                            break

        # 선택 근거 생성
        reasoning = self._generate_selection_reasoning(category, selected_agents, confidence, rules_applied)

        return AgentSelectionResult(
            selected_agents=selected_agents,
            selection_reasoning=reasoning,
            confidence_adjustment=confidence_adjustment,
            selection_time=datetime.now().isoformat(),
            rules_applied=rules_applied
        )

    def _adjust_based_on_context(self, result: AgentSelectionResult, state: AgentState) -> AgentSelectionResult:
        """컨텍스트 기반 조정"""

        rag_context = state.get('rag_context', {})

        # 검색 결과의 품질에 따른 조정
        chroma_results = rag_context.get('chroma_results', [])
        es_results = rag_context.get('elasticsearch_results', [])

        if len(chroma_results) + len(es_results) < 3:
            # 검색 결과가 부족하면 더 강력한 Agent 필요
            if "GPT" not in result.selected_agents:
                result.selected_agents.append("GPT")
                result.rules_applied.append("insufficient_context_gpt_added")
                result.selection_reasoning += " (검색 결과 부족으로 GPT 추가)"

        return result

    def _adjust_based_on_history(self, result: AgentSelectionResult, state: AgentState) -> AgentSelectionResult:
        """세션 히스토리 기반 조정"""

        conversation_count = state.get('conversation_count', 1)

        # 연속 대화에서는 일관성 유지
        if conversation_count > 1:
            # 이전 대화에서 사용된 Agent 정보가 있다면 고려
            # (실제 구현에서는 Redis에서 조회)
            result.rules_applied.append("conversation_continuity")

        return result

    def _generate_selection_reasoning(self, category: str, agents: List[str],
                                    confidence: float, rules_applied: List[str]) -> str:
        """Agent 선택 근거 생성"""

        agent_names = {
            "GPT": "GPT(종합분석)",
            "Gemini": "Gemini(기술특화)",
            "Clova": "Clova(실무경험)"
        }

        selected_names = [agent_names.get(agent, agent) for agent in agents]

        reasoning = f"문제 유형 '{category}'에 최적화된 {', '.join(selected_names)} Agent 선택"

        if confidence < 0.7:
            reasoning += f" (분류 신뢰도 {confidence:.2f}로 낮아 다중 Agent 투입)"

        if len(rules_applied) > 1:
            reasoning += f" (적용 규칙: {', '.join(rules_applied)})"

        return reasoning

    def get_agent_load_balancing(self) -> Dict[str, float]:
        """Agent별 부하 분산 정보 조회"""
        # 실제 구현에서는 Redis나 DB에서 Agent별 사용량 조회
        return {
            "GPT": 0.7,   # 70% 사용률
            "Gemini": 0.4, # 40% 사용률
            "Clova": 0.3   # 30% 사용률
        }

    def optimize_selection_for_performance(self, agents: List[str]) -> List[str]:
        """성능 최적화를 위한 Agent 선택 조정"""

        load_info = self.get_agent_load_balancing()

        # 부하가 높은 Agent는 대체 고려
        optimized_agents = []
        for agent in agents:
            if load_info.get(agent, 0) > 0.8:  # 80% 이상 부하
                # 대체 Agent 찾기
                alternatives = self._find_alternative_agents(agent)
                if alternatives:
                    optimized_agents.append(alternatives[0])
                    logger.info(f"부하 분산: {agent} → {alternatives[0]}")
                else:
                    optimized_agents.append(agent)
            else:
                optimized_agents.append(agent)

        return optimized_agents

    def _find_alternative_agents(self, agent: str) -> List[str]:
        """대체 가능한 Agent 찾기"""

        agent_capabilities = self.agent_specialties.get(agent, {}).get('best_for', [])
        alternatives = []

        for other_agent, info in self.agent_specialties.items():
            if other_agent != agent:
                # 공통 역량이 있는 Agent 찾기
                common_capabilities = set(agent_capabilities) & set(info['best_for'])
                if common_capabilities:
                    alternatives.append(other_agent)

        return alternatives