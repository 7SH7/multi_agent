#!/usr/bin/env python3
"""Kafka CDC 이벤트 테스트"""

import asyncio
import json
from aiokafka import AIOKafkaProducer
from datetime import datetime

async def send_cdc_test_events():
    """CDC 이벤트 시뮬레이션"""
    print("🔄 Kafka CDC 테스트 이벤트 전송")
    print("=" * 50)
    
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8')
    )
    
    try:
        await producer.start()
        print("✅ Kafka Producer 연결 성공")
        
        # 테스트 이벤트들 (실제 CDC 시나리오)
        cdc_events = [
            {
                "issue": "PRESS_001_20250808_001",
                "processType": "장애접수",
                "modeType": "프레스",
                "modeLogId": "PRESS_LOG_20250808_001",
                "description": "100톤 프레스에서 유압 소음 발생",
                "isSolved": False,
                "timestamp": datetime.now().isoformat()
            },
            {
                "issue": "WELDING_002_20250808_001", 
                "processType": "정기점검",
                "modeType": "용접기",
                "modeLogId": "WELDING_LOG_20250808_001",
                "description": "로봇 용접기 정기 점검 필요",
                "isSolved": False,
                "timestamp": datetime.now().isoformat()
            },
            {
                "issue": "PAINTING_003_20250808_001",
                "processType": "장애접수", 
                "modeType": "도장설비",
                "modeLogId": "PAINTING_LOG_20250808_001",
                "description": "도장 부스 온도 이상",
                "isSolved": False,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # 이벤트 전송
        for i, event in enumerate(cdc_events, 1):
            print(f"\n📨 {i}번째 CDC 이벤트 전송:")
            print(f"   이슈: {event['issue']}")
            print(f"   타입: {event['processType']} - {event['modeType']}")
            print(f"   설명: {event['description']}")
            
            await producer.send_and_wait('chatbot-issue-events', value=event)
            print(f"   ✅ 전송 완료")
            
            await asyncio.sleep(1)  # 1초 대기
        
        # 해결 이벤트 전송 (세션 자동 종료 테스트)
        print(f"\n🔧 문제 해결 이벤트 전송 (세션 종료 트리거):")
        resolve_event = {
            "issue": "PRESS_001_20250808_001",  # 첫 번째 이슈 해결
            "processType": "장애접수",
            "modeType": "프레스", 
            "modeLogId": "PRESS_LOG_20250808_001",
            "description": "유압 오일 교체로 소음 문제 해결됨",
            "isSolved": True,  # ← 이것이 관련 세션들을 종료시킴
            "timestamp": datetime.now().isoformat()
        }
        
        await producer.send_and_wait('chatbot-issue-events', value=resolve_event)
        print(f"   ✅ 해결 이벤트 전송 완료")
        print(f"   📝 관련 ChatbotSession들이 자동 종료됩니다")
        
        print(f"\n🎉 CDC 테스트 이벤트 전송 완료!")
        print(f"📊 총 {len(cdc_events) + 1}개 이벤트 전송됨")
        
    except Exception as e:
        print(f"❌ Kafka 전송 실패: {e}")
        print(f"💡 Kafka 서버가 실행 중인지 확인하세요: docker-compose up -d kafka")
        
    finally:
        await producer.stop()

async def main():
    print("🚀 Kafka CDC 테스트 시작")
    print("📋 이 스크립트는 다음을 시뮬레이션합니다:")
    print("   1. 외부 시스템에서 발생하는 장애/점검 이벤트")
    print("   2. CDC를 통한 실시간 데이터 동기화") 
    print("   3. 문제 해결시 자동 세션 종료")
    print()
    
    # Kafka 서버 확인
    try:
        from aiokafka import AIOKafkaConsumer
        consumer = AIOKafkaConsumer(bootstrap_servers='localhost:9092')
        await consumer.start()
        await consumer.stop()
        print("✅ Kafka 서버 연결 확인됨")
    except Exception as e:
        print(f"❌ Kafka 서버 연결 실패: {e}")
        print(f"💡 다음 명령으로 Kafka를 실행하세요:")
        print(f"   docker-compose up -d zookeeper kafka")
        return
    
    print()
    input("FastAPI 서버가 실행 중이면 Enter를 누르세요...")
    
    await send_cdc_test_events()

if __name__ == "__main__":
    asyncio.run(main())