"""Kafka Consumer for ChatbotIssue events"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from pydantic import BaseModel, ValidationError

from models.database_models import ChatbotIssue, ChatbotSession, Base
from config.settings import settings

logger = logging.getLogger(__name__)


class ChatbotIssueEvent(BaseModel):
    """Kafka 이벤트 모델"""
    issue: str
    processType: str  # '장애접수' 또는 '정기점검'
    modeType: str     # '프레스', '용접기', '도장설비', '차량조립설비'
    modeLogId: str
    description: Optional[str] = None  # 문제 설명
    isSolved: Optional[bool] = None    # 문제 해결 여부 (True시 관련 세션들 종료)
    timestamp: Optional[str] = None


class KafkaIssueConsumer:
    """ChatbotIssue Kafka Consumer"""
    
    def __init__(self):
        # 비동기 데이터베이스 엔진 설정
        try:
            # Use the DATABASE_URL from settings, but replace mysql:// with mysql+aiomysql://
            self.database_url = settings.DATABASE_URL.replace('mysql://', 'mysql+aiomysql://')
            is_mysql = True
        except Exception:
            # Fallback to SQLite
            self.database_url = "sqlite+aiosqlite:///./temp_database.db"
            is_mysql = False
        
        # Create engine with appropriate settings
        if is_mysql:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=10,
                max_overflow=20
            )
        else:
            self.engine = create_async_engine(
                self.database_url,
                echo=False
            )
        self.async_session = sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Kafka Consumer 설정
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
        
    async def initialize(self):
        """Consumer 초기화"""
        try:
            # 데이터베이스 테이블 생성
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Kafka Consumer 생성
            self.consumer = AIOKafkaConsumer(
                'chatbot-issue-events',  # 토픽 이름
                bootstrap_servers=getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
                group_id=getattr(settings, 'KAFKA_CONSUMER_GROUP', 'chatbot-issue-consumer-group'),
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',  # 최신 메시지부터 읽기
                enable_auto_commit=True,
                consumer_timeout_ms=1000
            )
            
            await self.consumer.start()
            logger.info("Kafka Consumer 초기화 완료")
            
        except Exception as e:
            logger.error(f"Consumer 초기화 실패: {str(e)}")
            raise
    
    async def process_chatbot_issue_event(self, event_data: Dict[str, Any]) -> bool:
        """ChatbotIssue 이벤트 처리"""
        try:
            # 이벤트 데이터 검증
            issue_event = ChatbotIssueEvent(**event_data)
            
            logger.info(f"ChatbotIssue 이벤트 처리 시작: {issue_event.issue}")
            
            async with self.async_session() as session:
                # 기존 이슈 확인
                result = await session.execute(
                    select(ChatbotIssue).where(ChatbotIssue.issue == issue_event.issue)
                )
                existing_issue = result.scalar_one_or_none()
                
                if existing_issue:
                    # 기존 이슈 업데이트
                    await session.execute(
                        update(ChatbotIssue)
                        .where(ChatbotIssue.issue == issue_event.issue)
                        .values(
                            processType=issue_event.processType,
                            modeType=issue_event.modeType,
                            modeLogId=issue_event.modeLogId,
                            description=issue_event.description,
                            updatedAt=datetime.now()
                        )
                    )
                    logger.info(f"기존 ChatbotIssue 업데이트: {issue_event.issue}")
                else:
                    # 새 이슈 생성
                    new_issue = ChatbotIssue(
                        issue=issue_event.issue,
                        processType=issue_event.processType,
                        modeType=issue_event.modeType,
                        modeLogId=issue_event.modeLogId,
                        description=issue_event.description
                    )
                    session.add(new_issue)
                    logger.info(f"새 ChatbotIssue 생성: {issue_event.issue}")
                
                # isSolved=True인 경우 관련 세션들 종료 처리
                if issue_event.isSolved is True:
                    logger.info(f"Issue {issue_event.issue} 해결됨 - 관련 세션들 종료 처리")
                    
                    # 해당 Issue와 연결된 모든 ChatbotSession 조회
                    sessions_result = await session.execute(
                        select(ChatbotSession).where(ChatbotSession.issue == issue_event.issue)
                    )
                    related_sessions = sessions_result.scalars().all()
                    
                    # 모든 관련 세션을 종료 상태로 변경
                    terminated_count = 0
                    for chat_session in related_sessions:
                        if not chat_session.isTerminated:  # 아직 종료되지 않은 세션만
                            chat_session.isTerminated = True
                            chat_session.endedAt = datetime.now()
                            terminated_count += 1
                    
                    logger.info(f"Issue {issue_event.issue} - {terminated_count}개 세션 종료 처리 완료")
                
                await session.commit()
                return True
                
        except ValidationError as e:
            logger.error(f"이벤트 데이터 검증 실패: {str(e)}")
            logger.error(f"받은 데이터: {event_data}")
            return False
            
        except Exception as e:
            logger.error(f"ChatbotIssue 이벤트 처리 실패: {str(e)}")
            return False
    
    async def consume_messages(self):
        """메시지 소비 시작"""
        if not self.consumer:
            raise RuntimeError("Consumer가 초기화되지 않았습니다")
        
        self.running = True
        logger.info("Kafka 메시지 소비 시작...")
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    # 메시지 로깅
                    logger.info(f"메시지 수신 - Topic: {message.topic}, Partition: {message.partition}, Offset: {message.offset}")
                    logger.debug(f"메시지 내용: {message.value}")
                    
                    # 이벤트 처리
                    success = await self.process_chatbot_issue_event(message.value)
                    
                    if success:
                        logger.info(f"메시지 처리 성공 - Offset: {message.offset}")
                    else:
                        logger.warning(f"메시지 처리 실패 - Offset: {message.offset}")
                        
                except Exception as e:
                    logger.error(f"메시지 처리 중 오류: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"메시지 소비 중 오류: {str(e)}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Consumer 중지"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka Consumer 중지됨")
        
        if self.engine:
            await self.engine.dispose()
            logger.info("데이터베이스 연결 종료됨")


# 전역 Consumer 인스턴스
kafka_issue_consumer = KafkaIssueConsumer()


async def start_kafka_consumer():
    """Kafka Consumer 시작 함수"""
    try:
        await kafka_issue_consumer.initialize()
        await kafka_issue_consumer.consume_messages()
    except Exception as e:
        logger.error(f"Kafka Consumer 시작 실패: {str(e)}")
        raise


async def stop_kafka_consumer():
    """Kafka Consumer 중지 함수"""
    await kafka_issue_consumer.stop()


if __name__ == "__main__":
    # 단독 실행을 위한 코드
    import asyncio
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        try:
            await start_kafka_consumer()
        except KeyboardInterrupt:
            logger.info("사용자에 의해 중단됨")
        except Exception as e:
            logger.error(f"Consumer 실행 오류: {str(e)}")
        finally:
            await stop_kafka_consumer()
    
    asyncio.run(main())