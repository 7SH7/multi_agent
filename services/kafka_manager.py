"""Kafka Manager for FastAPI integration"""

import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

from services.kafka_consumer import kafka_issue_consumer

logger = logging.getLogger(__name__)


class KafkaManager:
    """FastAPI와 Kafka Consumer 통합 관리"""
    
    def __init__(self):
        self.consumer_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """Kafka Consumer 시작"""
        if self.is_running:
            logger.warning("Kafka Consumer가 이미 실행 중입니다")
            return
        
        try:
            logger.info("Kafka Consumer 시작 중...")
            
            # Consumer 초기화
            await kafka_issue_consumer.initialize()
            
            # 백그라운드 태스크로 Consumer 실행
            self.consumer_task = asyncio.create_task(
                kafka_issue_consumer.consume_messages()
            )
            
            self.is_running = True
            logger.info("Kafka Consumer 시작 완료")
            
        except Exception as e:
            logger.error(f"Kafka Consumer 시작 실패: {str(e)}")
            raise
    
    async def stop(self):
        """Kafka Consumer 중지"""
        if not self.is_running:
            return
        
        try:
            logger.info("Kafka Consumer 중지 중...")
            
            # Consumer 중지
            await kafka_issue_consumer.stop()
            
            # 태스크 취소
            if self.consumer_task and not self.consumer_task.done():
                self.consumer_task.cancel()
                try:
                    await self.consumer_task
                except asyncio.CancelledError:
                    logger.info("Consumer 태스크가 취소되었습니다")
            
            self.is_running = False
            logger.info("Kafka Consumer 중지 완료")
            
        except Exception as e:
            logger.error(f"Kafka Consumer 중지 실패: {str(e)}")
    
    def get_status(self) -> dict:
        """Consumer 상태 조회"""
        return {
            "is_running": self.is_running,
            "task_status": "running" if self.consumer_task and not self.consumer_task.done() else "stopped",
            "consumer_initialized": kafka_issue_consumer.consumer is not None
        }


# 전역 Kafka Manager 인스턴스
kafka_manager = KafkaManager()


@asynccontextmanager
async def kafka_lifespan():
    """FastAPI lifespan context manager"""
    try:
        # 시작 시
        await kafka_manager.start()
        yield
    except Exception as e:
        logger.error(f"Kafka lifespan 오류: {str(e)}")
        yield
    finally:
        # 종료 시
        await kafka_manager.stop()