"""외부 서비스 의존성 헬스체크 및 fallback 관리"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"

@dataclass 
class ServiceHealth:
    service_name: str
    status: ServiceStatus
    response_time_ms: Optional[float]
    last_check: datetime
    error_message: Optional[str] = None
    consecutive_failures: int = 0

class ServiceHealthChecker:
    """외부 서비스 헬스체크 관리자"""
    
    def __init__(self):
        self.service_health: Dict[str, ServiceHealth] = {}
        self.check_intervals = {
            'redis': 30,        # 30초
            'elasticsearch': 60,  # 1분  
            'chromadb': 60,     # 1분
            'database': 120     # 2분
        }
        self.max_failures = 3  # 연속 실패 임계값
        
    async def check_redis_health(self) -> ServiceHealth:
        """Redis 헬스체크"""
        start_time = datetime.now()
        try:
            import redis
            from config.settings import REDIS_CONFIG
            
            # Redis 연결 테스트
            r = redis.Redis(**REDIS_CONFIG)
            await asyncio.wait_for(
                asyncio.to_thread(r.ping), 
                timeout=5.0
            )
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health = ServiceHealth(
                service_name="redis",
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                consecutive_failures=0
            )
            
            logger.debug(f"Redis 헬스체크 성공: {response_time:.2f}ms")
            return health
            
        except asyncio.TimeoutError:
            logger.warning("Redis 헬스체크 타임아웃")
            return self._create_failed_health("redis", "연결 타임아웃")
        except Exception as e:
            logger.error(f"Redis 헬스체크 실패: {str(e)}")
            return self._create_failed_health("redis", str(e))
    
    async def check_elasticsearch_health(self) -> ServiceHealth:
        """Elasticsearch 헬스체크"""
        start_time = datetime.now()
        try:
            from elasticsearch import AsyncElasticsearch
            from config.settings import ELASTICSEARCH_CONFIG
            
            # Elasticsearch 연결 테스트
            es_client = AsyncElasticsearch([{
                'host': ELASTICSEARCH_CONFIG['host'],
                'port': ELASTICSEARCH_CONFIG['port']
            }])
            
            # 클러스터 헬스 체크
            health_response = await asyncio.wait_for(
                es_client.cluster.health(),
                timeout=10.0
            )
            
            await es_client.close()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Elasticsearch 상태에 따른 서비스 상태 결정
            es_status = health_response.get('status', 'red')
            if es_status == 'green':
                status = ServiceStatus.HEALTHY
            elif es_status == 'yellow':
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.DOWN
            
            health = ServiceHealth(
                service_name="elasticsearch",
                status=status,
                response_time_ms=response_time,
                last_check=datetime.now(),
                consecutive_failures=0 if status != ServiceStatus.DOWN else 1
            )
            
            logger.debug(f"Elasticsearch 헬스체크: {es_status} ({response_time:.2f}ms)")
            return health
            
        except asyncio.TimeoutError:
            logger.warning("Elasticsearch 헬스체크 타임아웃")
            return self._create_failed_health("elasticsearch", "연결 타임아웃")
        except Exception as e:
            logger.error(f"Elasticsearch 헬스체크 실패: {str(e)}")
            return self._create_failed_health("elasticsearch", str(e))
    
    async def check_chromadb_health(self) -> ServiceHealth:
        """ChromaDB 헬스체크"""
        start_time = datetime.now()
        try:
            import chromadb
            from config.settings import CHROMADB_CONFIG
            
            # ChromaDB 연결 테스트
            client = chromadb.HttpClient(
                host=CHROMADB_CONFIG['host'],
                port=CHROMADB_CONFIG['port']
            )
            
            # 간단한 버전 체크로 연결 확인
            await asyncio.wait_for(
                asyncio.to_thread(client.heartbeat),
                timeout=10.0
            )
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health = ServiceHealth(
                service_name="chromadb",
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                consecutive_failures=0
            )
            
            logger.debug(f"ChromaDB 헬스체크 성공: {response_time:.2f}ms")
            return health
            
        except asyncio.TimeoutError:
            logger.warning("ChromaDB 헬스체크 타임아웃")
            return self._create_failed_health("chromadb", "연결 타임아웃")
        except Exception as e:
            logger.error(f"ChromaDB 헬스체크 실패: {str(e)}")
            return self._create_failed_health("chromadb", str(e))
    
    async def check_database_health(self) -> ServiceHealth:
        """데이터베이스 헬스체크"""
        start_time = datetime.now()
        try:
            import aiomysql
            from config.settings import settings
            
            # MySQL 연결 테스트
            conn = await asyncio.wait_for(
                aiomysql.connect(
                    host=settings.DB_HOST.split(':')[0],
                    port=int(settings.DB_HOST.split(':')[1]) if ':' in settings.DB_HOST else 3306,
                    user=settings.DB_USERNAME,
                    password=settings.DB_PASSWORD,
                    db=settings.DB_NAME
                ),
                timeout=10.0
            )
            
            # 간단한 쿼리로 연결 확인
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT 1")
                await cursor.fetchone()
            
            conn.close()
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            health = ServiceHealth(
                service_name="database",
                status=ServiceStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now(),
                consecutive_failures=0
            )
            
            logger.debug(f"Database 헬스체크 성공: {response_time:.2f}ms")
            return health
            
        except asyncio.TimeoutError:
            logger.warning("Database 헬스체크 타임아웃")
            return self._create_failed_health("database", "연결 타임아웃")
        except Exception as e:
            logger.error(f"Database 헬스체크 실패: {str(e)}")
            return self._create_failed_health("database", str(e))
    
    def _create_failed_health(self, service_name: str, error_message: str) -> ServiceHealth:
        """실패한 헬스체크 결과 생성"""
        current_health = self.service_health.get(service_name)
        consecutive_failures = (current_health.consecutive_failures + 1) if current_health else 1
        
        return ServiceHealth(
            service_name=service_name,
            status=ServiceStatus.DOWN,
            response_time_ms=None,
            last_check=datetime.now(),
            error_message=error_message,
            consecutive_failures=consecutive_failures
        )
    
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """모든 서비스 헬스체크"""
        logger.info("전체 서비스 헬스체크 시작")
        
        # 모든 헬스체크를 병렬로 실행
        tasks = [
            self.check_redis_health(),
            self.check_elasticsearch_health(), 
            self.check_chromadb_health(),
            self.check_database_health()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 업데이트
        for result in results:
            if isinstance(result, ServiceHealth):
                self.service_health[result.service_name] = result
            elif isinstance(result, Exception):
                logger.error(f"헬스체크 중 예외 발생: {str(result)}")
        
        # 전체 상태 로그
        healthy_count = sum(1 for h in self.service_health.values() if h.status == ServiceStatus.HEALTHY)
        total_count = len(self.service_health)
        
        logger.info(f"헬스체크 완료: {healthy_count}/{total_count} 서비스 정상")
        
        return self.service_health
    
    def get_service_status(self, service_name: str) -> Optional[ServiceHealth]:
        """특정 서비스 상태 조회"""
        return self.service_health.get(service_name)
    
    def is_service_healthy(self, service_name: str) -> bool:
        """서비스가 정상인지 확인"""
        health = self.service_health.get(service_name)
        return health is not None and health.status == ServiceStatus.HEALTHY
    
    def get_degraded_services(self) -> List[str]:
        """성능 저하된 서비스 목록"""
        return [
            name for name, health in self.service_health.items()
            if health.status == ServiceStatus.DEGRADED
        ]
    
    def get_failed_services(self) -> List[str]:
        """실패한 서비스 목록"""
        return [
            name for name, health in self.service_health.items()
            if health.status == ServiceStatus.DOWN
        ]
    
    def get_overall_health_summary(self) -> Dict[str, Any]:
        """전체 헬스 상태 요약"""
        if not self.service_health:
            return {
                "overall_status": "unknown",
                "healthy_services": 0,
                "total_services": 0,
                "failed_services": [],
                "degraded_services": []
            }
        
        healthy_services = [name for name, health in self.service_health.items() if health.status == ServiceStatus.HEALTHY]
        failed_services = self.get_failed_services()
        degraded_services = self.get_degraded_services()
        
        # 전체 상태 결정
        if len(failed_services) > 0:
            overall_status = "critical"
        elif len(degraded_services) > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status, 
            "healthy_services": len(healthy_services),
            "total_services": len(self.service_health),
            "failed_services": failed_services,
            "degraded_services": degraded_services,
            "last_check": max(h.last_check for h in self.service_health.values()).isoformat(),
            "service_details": {
                name: {
                    "status": health.status.value,
                    "response_time_ms": health.response_time_ms,
                    "consecutive_failures": health.consecutive_failures,
                    "error_message": health.error_message
                }
                for name, health in self.service_health.items()
            }
        }

# 글로벌 헬스체커 인스턴스
_health_checker = ServiceHealthChecker()

def get_health_checker() -> ServiceHealthChecker:
    """헬스 체커 인스턴스 반환"""
    return _health_checker