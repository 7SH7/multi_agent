#!/usr/bin/env python3
"""시스템 헬스체크 및 의존성 검증 스크립트"""

import asyncio
import sys
import os

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# 프로젝트 루트 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemHealthChecker:
    """시스템 헬스체크 및 의존성 검증"""
    
    def __init__(self):
        self.results = []
        
    def add_result(self, component: str, status: bool, message: str, critical: bool = False):
        """검사 결과 추가"""
        self.results.append({
            'component': component,
            'status': status,
            'message': message,
            'critical': critical,
            'timestamp': datetime.now().isoformat()
        })
        
    async def check_api_keys(self) -> bool:
        """API 키 설정 확인"""
        logger.info("🔑 API 키 설정 확인 중...")
        
        try:
            from config.settings import LLM_CONFIGS
            
            key_status = {}
            for service, config in LLM_CONFIGS.items():
                api_key = config.get('api_key', '')
                if api_key and not api_key.startswith('your_') and len(api_key) > 10:
                    key_status[service] = True
                    self.add_result(f"API 키 ({service})", True, "설정됨")
                else:
                    key_status[service] = False
                    self.add_result(f"API 키 ({service})", False, "미설정 또는 기본값")
            
            working_keys = sum(key_status.values())
            if working_keys >= 2:  # 최소 2개 이상 작동
                self.add_result("API 키 전체", True, f"{working_keys}/4개 서비스 사용 가능")
                return True
            else:
                self.add_result("API 키 전체", False, f"사용 가능한 키가 부족: {working_keys}/4개", critical=True)
                return False
                
        except Exception as e:
            self.add_result("API 키 확인", False, f"오류: {str(e)}", critical=True)
            return False
    
    async def check_databases(self) -> bool:
        """데이터베이스 연결 확인"""
        logger.info("🗄️ 데이터베이스 연결 확인 중...")
        
        db_results = []
        
        # ChromaDB 확인
        try:
            import chromadb
            client = chromadb.PersistentClient(path="data/embeddings/chromadb")
            collections = client.list_collections()
            self.add_result("ChromaDB", True, f"연결 성공 ({len(collections)}개 컬렉션)")
            db_results.append(True)
        except Exception as e:
            self.add_result("ChromaDB", False, f"연결 실패: {str(e)}")
            db_results.append(False)
        
        # Elasticsearch 확인
        try:
            from elasticsearch import AsyncElasticsearch
            client = AsyncElasticsearch([{
                'host': 'localhost',
                'port': 9200,
                'scheme': 'http'
            }], request_timeout=3)
            
            await client.cluster.health(wait_for_status='yellow', timeout='3s')
            self.add_result("Elasticsearch", True, "연결 성공")
            db_results.append(True)
            await client.close()
        except Exception as e:
            self.add_result("Elasticsearch", False, f"연결 실패: {str(e)} (선택사항)")
            db_results.append(False)
        
        # Redis 확인
        try:
            import redis.asyncio as redis
            client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            await client.ping()
            self.add_result("Redis", True, "연결 성공")
            db_results.append(True)
            await client.aclose()
        except Exception as e:
            self.add_result("Redis", False, f"연결 실패: {str(e)} (선택사항)")
            db_results.append(False)
        
        # ChromaDB만 필수, 나머지는 선택사항
        return db_results[0]  # ChromaDB 상태 반환
    
    async def check_agents(self) -> bool:
        """Agent 시스템 확인"""
        logger.info("🤖 Agent 시스템 확인 중...")
        
        try:
            from agents.gpt_agent import GPTAgent
            from agents.gemini_agent import GeminiAgent
            from agents.clova_agent import ClovaAgent
            from models.agent_state import AgentState
            
            test_state = AgentState()
            test_state.update({
                'user_message': '시스템 테스트',
                'session_id': 'health_check',
                'timestamp': datetime.now()
            })
            
            agents = [
                ("GPT", GPTAgent()),
                ("Gemini", GeminiAgent()),
                ("Clova", ClovaAgent())
            ]
            
            working_agents = 0
            
            for agent_name, agent in agents:
                try:
                    # 간단한 분석 테스트 (실제 API 호출 없이)
                    if hasattr(agent, 'config') and agent.config:
                        self.add_result(f"Agent ({agent_name})", True, "초기화 성공")
                        working_agents += 1
                    else:
                        self.add_result(f"Agent ({agent_name})", False, "초기화 실패")
                except Exception as e:
                    self.add_result(f"Agent ({agent_name})", False, f"오류: {str(e)}")
            
            if working_agents >= 2:
                self.add_result("Agent 시스템", True, f"{working_agents}/3개 Agent 사용 가능")
                return True
            else:
                self.add_result("Agent 시스템", False, f"사용 가능한 Agent 부족: {working_agents}/3개", critical=True)
                return False
                
        except Exception as e:
            self.add_result("Agent 시스템", False, f"시스템 오류: {str(e)}", critical=True)
            return False
    
    async def check_workflow(self) -> bool:
        """워크플로우 시스템 확인"""
        logger.info("🔄 워크플로우 시스템 확인 중...")
        
        try:
            from core.enhanced_workflow import get_enhanced_workflow
            from core.session_manager import SessionManager
            from core.monitoring import get_system_monitor
            
            # 워크플로우 매니저 초기화
            workflow_manager = get_enhanced_workflow()
            self.add_result("워크플로우 매니저", True, "초기화 성공")
            
            # 세션 매니저 초기화
            session_manager = SessionManager()
            self.add_result("세션 매니저", True, "초기화 성공")
            
            # 모니터링 시스템 초기화
            monitor = get_system_monitor()
            self.add_result("모니터링 시스템", True, "초기화 성공")
            
            return True
            
        except Exception as e:
            self.add_result("워크플로우 시스템", False, f"오류: {str(e)}", critical=True)
            return False
    
    def print_results(self):
        """검사 결과 출력"""
        print("\n" + "="*80)
        print("🏥 Multi-Agent 챗봇 시스템 헬스체크 결과")
        print("="*80)
        
        critical_failures = []
        warnings = []
        successes = []
        
        for result in self.results:
            status_icon = "✅" if result['status'] else "❌"
            component = result['component']
            message = result['message']
            
            print(f"{status_icon} {component}: {message}")
            
            if not result['status']:
                if result['critical']:
                    critical_failures.append(component)
                else:
                    warnings.append(component)
            else:
                successes.append(component)
        
        print("\n" + "="*80)
        print("📊 요약")
        print(f"✅ 성공: {len(successes)}개")
        print(f"⚠️  경고: {len(warnings)}개")
        print(f"❌ 치명적 실패: {len(critical_failures)}개")
        
        if critical_failures:
            print(f"\n🚨 치명적 문제:")
            for failure in critical_failures:
                print(f"   - {failure}")
            print("\n💡 시스템을 시작하기 전에 위 문제들을 해결해야 합니다.")
            return False
        elif warnings:
            print(f"\n⚠️  경고 사항:")
            for warning in warnings:
                print(f"   - {warning}")
            print("\n💡 시스템은 시작 가능하지만 일부 기능이 제한될 수 있습니다.")
            return True
        else:
            print("\n🎉 모든 검사를 통과했습니다! 시스템을 안전하게 시작할 수 있습니다.")
            return True

async def main():
    """메인 헬스체크 실행"""
    checker = SystemHealthChecker()
    
    print("🚀 Multi-Agent 챗봇 시스템 헬스체크 시작...")
    print(f"📅 실행 시간: {datetime.now().isoformat()}")
    
    # 순차적으로 검사 실행
    checks = [
        checker.check_api_keys(),
        checker.check_databases(),
        checker.check_agents(),
        checker.check_workflow()
    ]
    
    results = await asyncio.gather(*checks, return_exceptions=True)
    
    # 결과 처리
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            checker.add_result(f"검사 {i+1}", False, f"예외 발생: {str(result)}", critical=True)
    
    # 결과 출력
    success = checker.print_results()
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())