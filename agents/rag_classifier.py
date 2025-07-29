"""RAG 기반 질문 분류 및 검색 Agent"""

import redis.asyncio as redis
import json
from datetime import datetime
from typing import Dict, Any, List
from models.agent_state import AgentState
from config.issue_database import ISSUE_DATABASE
from utils.rag_engines import ChromaEngine, ElasticsearchEngine
import logging

logger = logging.getLogger(__name__)

class RAGClassifier:
    """RAG 기반 질문 분류 및 검색 시스템"""

    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.chroma_engine = ChromaEngine()
        self.elasticsearch_engine = ElasticsearchEngine()
        self.issue_db = ISSUE_DATABASE

        # 질문 카테고리별 키워드
        self.category_keywords = {
            "비용문제": ['비용', '얼마', '가격', '돈', '예산', '경제적'],
            "긴급문제": ['빨리', '긴급', '급해', '즉시', '응급', '위급'],
            "안전문제": ['안전', '위험', '사고', '부상', '화재', '폭발'],
            "전기문제": ['전기', '전압', '전류', '회로', '누전', '쇼트'],
            "기계문제": ['기계', '부품', '조립', '설치', '베어링', '모터'],
            "품질문제": ['품질', '불량', '검사', '기준', '규격', '표준']
        }

    async def classify_and_search(self, state: AgentState) -> AgentState:
        """RAG 기반 질문 분류 및 검색"""

        try:
            user_question = state.get('user_message', '')
            issue_code = state.get('issue_code', '')

            logger.info(f"RAG 분류 시작 - 질문: {user_question[:50]}...")

            # 1. 이슈 코드 기반 기본 정보 추출
            issue_info = self.extract_issue_info(issue_code)

            # 2. 질문 카테고리 분류
            question_category = self.classify_question_type(user_question, issue_info)

            # 3. 하이브리드 RAG 검색
            rag_context = await self.perform_hybrid_search(user_question, issue_info)

            # 4. 분류 신뢰도 계산
            classification_confidence = self.calculate_classification_confidence(issue_info, question_category)

            # 상태 업데이트
            state.update({
                'issue_classification': {
                    'issue_info': issue_info,
                    'category': question_category,
                    'classification_confidence': classification_confidence,
                    'classified_at': datetime.now().isoformat()
                },
                'question_category': question_category,
                'rag_context': rag_context,
                'processing_steps': state.get('processing_steps', []) + ['rag_classification_completed']
            })

            logger.info(f"RAG 분류 완료 - 카테고리: {question_category}, 신뢰도: {classification_confidence}")

            return state

        except Exception as e:
            logger.error(f"RAG 분류 오류: {str(e)}")
            state.update({
                'error': f"RAG 분류 실패: {str(e)}",
                'processing_steps': state.get('processing_steps', []) + ['rag_classification_failed']
            })
            return state

    def extract_issue_info(self, issue_code: str) -> Dict[str, Any]:
        """이슈 코드에서 기본 정보 추출"""
        if not issue_code:
            return {"error": "이슈 코드가 없습니다"}

        try:
            # ASBP-DOOR-SCRATCH-20240722001 → ASBP-DOOR-SCRATCH
            parts = issue_code.split('-')
            if len(parts) >= 3:
                issue_prefix = '-'.join(parts[:3])

                if issue_prefix in self.issue_db:
                    issue_data = self.issue_db[issue_prefix].copy()
                    issue_data['full_code'] = issue_code
                    issue_data['datetime'] = '-'.join(parts[3:]) if len(parts) > 3 else ''

                    logger.info(f"이슈 정보 추출 성공: {issue_prefix}")
                    return issue_data

            logger.warning(f"알 수 없는 이슈 코드: {issue_code}")
            return {"error": f"알 수 없는 이슈 코드: {issue_code}"}

        except Exception as e:
            logger.error(f"이슈 코드 추출 오류: {str(e)}")
            return {"error": f"이슈 코드 처리 실패: {str(e)}"}

    def classify_question_type(self, question: str, issue_info: Dict) -> str:
        """질문 타입 분류"""
        question_lower = question.lower()

        # 키워드 기반 분류
        for category, keywords in self.category_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                logger.info(f"키워드 기반 분류: {category}")
                return category

        # 이슈 정보 기반 분류
        if not issue_info.get('error'):
            category = issue_info.get('category', '')
            if category == '표면 손상':
                return "품질문제"
            elif category == '치수 불량':
                return "기계문제"
            elif category == '안전 관련':
                return "안전문제"
            elif category == '성능 이상':
                return "기계문제"

        logger.info("일반문제로 분류")
        return "일반문제"

    async def perform_hybrid_search(self, question: str, issue_info: Dict) -> Dict[str, Any]:
        """하이브리드 RAG 검색"""

        try:
            # 검색 키워드 구성
            search_keywords = issue_info.get('search_keywords', [])
            if isinstance(search_keywords, list):
                enhanced_query = f"{question} {' '.join(search_keywords)}"
            else:
                enhanced_query = question

            logger.info(f"검색 쿼리: {enhanced_query}")

            # 병렬 검색 실행
            chroma_results = await self.chroma_engine.search(enhanced_query, top_k=5)
            elasticsearch_results = await self.elasticsearch_engine.search(enhanced_query, top_k=5)

            # 결과 통합
            unified_context = {
                'chroma_results': chroma_results,
                'elasticsearch_results': elasticsearch_results,
                'search_query': enhanced_query,
                'issue_context': issue_info,
                'searched_at': datetime.now().isoformat(),
                'total_results': len(chroma_results) + len(elasticsearch_results)
            }

            logger.info(f"검색 완료 - ChromaDB: {len(chroma_results)}개, Elasticsearch: {len(elasticsearch_results)}개")

            return unified_context

        except Exception as e:
            logger.error(f"RAG 검색 오류: {str(e)}")
            return {
                'error': f"검색 실패: {str(e)}",
                'chroma_results': [],
                'elasticsearch_results': [],
                'search_query': question,
                'searched_at': datetime.now().isoformat()
            }

    def calculate_classification_confidence(self, issue_info: Dict, category: str) -> float:
        """분류 신뢰도 계산"""
        confidence = 0.5  # 기본값

        # 이슈 정보가 명확한 경우
        if not issue_info.get('error'):
            confidence += 0.3

        # 카테고리가 명확한 경우
        if category != "일반문제":
            confidence += 0.2

        # 키워드 매칭 수에 따른 가중치
        

        return min(0.95, confidence)

    async def get_cached_search(self, query_hash: str) -> Dict[str, Any]:
        """캐시된 검색 결과 조회"""
        try:
            cached = await self.redis_client.get(f"search_cache:{query_hash}")
            if cached:
                logger.info("캐시된 검색 결과 사용")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"캐시 조회 실패: {str(e)}")

        return None

    async def cache_search_result(self, query_hash: str, result: Dict[str, Any], ttl: int = 3600):
        """검색 결과 캐시 저장"""
        try:
            await self.redis_client.setex(
                f"search_cache:{query_hash}",
                ttl,
                json.dumps(result, ensure_ascii=False)
            )
            logger.info("검색 결과 캐시 저장 완료")
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {str(e)}")