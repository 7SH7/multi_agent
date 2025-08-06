"""Kafka Producer for testing ChatbotIssue events"""

import asyncio
import json
import logging
from datetime import datetime
from aiokafka import AIOKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaTestProducer:
    """테스트용 Kafka Producer"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
    
    async def start(self):
        """Producer 시작"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8')
        )
        await self.producer.start()
        logger.info("Kafka Producer 시작됨")
    
    async def stop(self):
        """Producer 중지"""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka Producer 중지됨")
    
    async def send_chatbot_issue_event(self, issue_data: dict):
        """ChatbotIssue 이벤트 전송"""
        try:
            # 타임스탬프 추가
            issue_data['timestamp'] = datetime.now().isoformat()
            
            # 메시지 전송
            await self.producer.send_and_wait(
                'chatbot-issue-events',
                value=issue_data
            )
            
            logger.info(f"ChatbotIssue 이벤트 전송 완료: {issue_data['issue']}")
            return True
            
        except Exception as e:
            logger.error(f"ChatbotIssue 이벤트 전송 실패: {str(e)}")
            return False


async def send_test_events():
    """테스트 이벤트들 전송"""
    producer = KafkaTestProducer()
    
    try:
        await producer.start()
        
        # 테스트 이벤트 데이터 (일반 이슈들)
        test_events = [
            {
                "issue": "PRESS_001_20250806_001",
                "processType": "장애접수",
                "modeType": "프레스",
                "modeLogId": "PRESS_LOG_20250806_001",
                "description": "프레스 기계 유압 시스템 압력 이상으로 인한 장애 발생",
                "isSolved": False  # 아직 해결되지 않음
            },
            {
                "issue": "WELDING_002_20250806_001", 
                "processType": "정기점검",
                "modeType": "용접기",
                "modeLogId": "WELDING_LOG_20250806_001",
                "description": "용접 로봇 정기 점검 및 캘리브레이션 작업",
                "isSolved": False  # 아직 해결되지 않음
            },
            {
                "issue": "PAINTING_003_20250806_001",
                "processType": "장애접수", 
                "modeType": "도장설비",
                "modeLogId": "PAINTING_LOG_20250806_001",
                "description": "도장 부스 내 스프레이 노즐 막힘으로 인한 불균일 도장 문제",
                "isSolved": False  # 아직 해결되지 않음
            },
            {
                "issue": "ASSEMBLY_004_20250806_001",
                "processType": "정기점검",
                "modeType": "차량조립설비", 
                "modeLogId": "ASSEMBLY_LOG_20250806_001",
                "description": "차량 조립 라인 컨베이어 벨트 정기 점검 및 교체",
                "isSolved": True   # 해결됨 - 관련 세션들 자동 종료
            }
        ]
        
        # 이벤트 전송
        for event in test_events:
            success = await producer.send_chatbot_issue_event(event)
            if success:
                logger.info(f"✅ 이벤트 전송 성공: {event['issue']}")
            else:
                logger.error(f"❌ 이벤트 전송 실패: {event['issue']}")
            
            # 잠시 대기
            await asyncio.sleep(1)
        
        logger.info(f"총 {len(test_events)}개 테스트 이벤트 전송 완료")
        
    except Exception as e:
        logger.error(f"테스트 이벤트 전송 중 오류: {str(e)}")
    finally:
        await producer.stop()


if __name__ == "__main__":
    print("🚀 Kafka 테스트 Producer 시작...")
    print("📨 ChatbotIssue 테스트 이벤트들을 전송합니다...")
    
    asyncio.run(send_test_events())
    
    print("✅ 테스트 완료!")
    print("\n📋 확인 방법:")
    print("1. FastAPI 서버가 실행 중인지 확인")
    print("2. GET /api/kafka/status - Kafka Consumer 상태 확인")
    print("3. GET /api/kafka/issues - ChatbotIssue 목록 확인")
    print("4. 로그에서 Consumer 처리 메시지 확인")