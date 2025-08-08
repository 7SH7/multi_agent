#!/usr/bin/env python3
"""Kafka로 테스트 메시지 전송"""

import asyncio
import json
from aiokafka import AIOKafkaProducer

async def send_test_message():
    """테스트 메시지 전송"""
    print("📨 Kafka 테스트 메시지 전송 시작")
    
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8')
    )
    
    try:
        await producer.start()
        print("✅ Producer 시작됨")
        
        # 테스트 메시지
        message = {
            "issue": "TEST_MSG_001",
            "processType": "장애접수", 
            "modeType": "프레스",
            "modeLogId": "TEST_LOG_20250808_001",
            "description": "테스트용 프레스 소음 문제",
            "isSolved": False
        }
        
        print(f"📤 메시지 전송: {message}")
        
        # 메시지 전송
        await producer.send_and_wait('chatbot-issue-events', value=message)
        
        print("✅ 메시지 전송 완료!")
        print("💡 FastAPI 서버 로그를 확인하여 메시지가 수신되었는지 확인하세요.")
        
    except Exception as e:
        print(f"❌ 전송 실패: {e}")
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(send_test_message())