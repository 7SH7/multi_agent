"""토큰 관리 및 동적 조정 유틸리티"""

from typing import Dict, Any, List
from config.settings import TOKEN_LIMITS, AGENT_TOKEN_LIMITS
import logging

logger = logging.getLogger(__name__)

class TokenManager:
    """토큰 한계 동적 관리"""
    
    def __init__(self):
        self.base_limits = AGENT_TOKEN_LIMITS.copy()
        
    def get_optimal_token_limit(self, 
                               agent_name: str,
                               question_type: str = "general",
                               question_length: int = 0,
                               is_technical: bool = False,
                               is_emergency: bool = False) -> int:
        """최적 토큰 한계 계산"""
        
        # 기본 Agent 한계
        base_limit = self.base_limits.get(agent_name, TOKEN_LIMITS["base"])
        
        # 긴급 상황 - 최소 토큰
        if is_emergency:
            return TOKEN_LIMITS["emergency"]
        
        # 기술적 질문 - 더 많은 토큰 필요
        if is_technical or "기술" in question_type or "분석" in question_type:
            if agent_name == "gemini":
                return TOKEN_LIMITS["technical"]
            else:
                return min(base_limit + 100, TOKEN_LIMITS["technical"])
        
        # 질문 길이에 따른 조정
        if question_length > 100:  # 긴 질문
            adjustment = min(50, question_length // 20)  # 최대 50토큰 추가
            return min(base_limit + adjustment, TOKEN_LIMITS["debate"])
        
        # 토론/종합이 필요한 경우
        if question_type in ["복합문제", "다단계분석", "종합판단"]:
            return TOKEN_LIMITS["debate"]
        
        return base_limit
    
    def get_debate_token_limit(self, 
                              agent_count: int,
                              complexity_level: str = "medium") -> int:
        """토론용 토큰 한계 계산"""
        
        base_debate_limit = TOKEN_LIMITS["debate"]
        
        # Agent 수에 따른 조정
        if agent_count >= 3:
            # 3개 이상 Agent면 더 많은 통합 필요
            adjustment = 100
        elif agent_count == 2:
            # 2개 Agent면 적당한 통합
            adjustment = 50
        else:
            # 1개 Agent면 토론 없음
            return self.base_limits.get("claude", TOKEN_LIMITS["base"])
        
        # 복잡도에 따른 조정
        complexity_multiplier = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.3
        }
        
        final_limit = int((base_debate_limit + adjustment) * complexity_multiplier.get(complexity_level, 1.0))
        
        # 최대 한계 적용
        return min(final_limit, 800)  # 최대 800토큰
    
    def adjust_for_context(self,
                          base_limit: int,
                          rag_results_count: int = 0,
                          conversation_history_length: int = 0) -> int:
        """컨텍스트에 따른 토큰 조정"""
        
        adjusted_limit = base_limit
        
        # RAG 결과가 많으면 더 긴 응답 필요
        if rag_results_count > 3:
            adjusted_limit += 50
        elif rag_results_count > 1:
            adjusted_limit += 25
        
        # 대화 기록이 길면 연속성 고려해서 더 긴 응답
        if conversation_history_length > 5:
            adjusted_limit += 30
        elif conversation_history_length > 2:
            adjusted_limit += 15
        
        return adjusted_limit
    
    def get_agent_specific_limit(self, agent_name: str, context) -> int:
        """Agent 특성과 상황을 고려한 최종 토큰 한계"""
        
        # AgentState 객체인지 dict인지 확인
        if hasattr(context, 'get'):
            # AgentState 객체
            question = context.get('user_message', '')
            question_type = context.get('question_category', 'general')
            rag_results = context.get('rag_context', {})
            conversation_history = context.get('conversation_history', [])
        else:
            # dict 형태
            question = context.get('user_message', '')
            question_type = context.get('question_category', 'general')
            rag_results = context.get('rag_context', {})
            conversation_history = context.get('conversation_history', [])
        
        # 기본 한계 계산
        base_limit = self.get_optimal_token_limit(
            agent_name=agent_name,
            question_type=question_type,
            question_length=len(question),
            is_technical=any(keyword in question.lower() for keyword in ['기술', '분석', '수치', '계산', '측정']),
            is_emergency=any(keyword in question.lower() for keyword in ['긴급', '즉시', '빨리', '응급'])
        )
        
        # 컨텍스트 조정
        rag_count = len(rag_results.get('chroma_results', [])) + len(rag_results.get('elasticsearch_results', []))
        adjusted_limit = self.adjust_for_context(
            base_limit=base_limit,
            rag_results_count=rag_count,
            conversation_history_length=len(conversation_history)
        )
        
        logger.info(f"{agent_name} 토큰 한계: {base_limit} → {adjusted_limit} (질문길이: {len(question)}, RAG결과: {rag_count})")
        
        return adjusted_limit

# 전역 토큰 매니저 인스턴스
token_manager = TokenManager()

def get_token_manager() -> TokenManager:
    """토큰 매니저 인스턴스 반환"""
    return token_manager