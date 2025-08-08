#!/usr/bin/env python3
"""간단한 Kafka 연결 및 메시지 테스트"""

import asyncio
import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

async def test_kafka_connection():
    """Kafka 연결 테스트"""
    print("🔍 Kafka 연결 테스트 시작")
    
    # 1. Producer 테스트
    print("\n1️⃣ Kafka Producer 테스트")
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8')
        )
        await producer.start()
        print("   ✅ Producer 연결 성공")
        
        # 테스트 메시지 전송
        test_message = {
            "issue": "TEST_CONNECTION_001",
            "processType": "장애접수",
            "modeType": "프레스",
            "modeLogId": "TEST_LOG_001",
            "description": "Kafka 연결 테스트 메시지"
        }
        
        await producer.send_and_wait('chatbot-issue-events', value=test_message)
        print("   ✅ 테스트 메시지 전송 성공")
        
        await producer.stop()
        
    except Exception as e:
        print(f"   ❌ Producer 실패: {e}")
        return False
    
    # 2. Consumer 테스트 (빠른 확인용)
    print("\n2️⃣ Kafka Consumer 테스트")
    try:
        consumer = AIOKafkaConsumer(
            'chatbot-issue-events',
            bootstrap_servers='localhost:9092',
            group_id='test-consumer-group',
            auto_offset_reset='latest',
            consumer_timeout_ms=5000  # 5초 타임아웃
        )
        await consumer.start()
        print("   ✅ Consumer 연결 성공")
        
        # 메시지 하나만 읽어보기
        print("   📨 메시지 대기 중...")
        message_received = False
        
        async for message in consumer:
            print(f"   📩 메시지 수신: {message.value}")
            message_received = True
            break  # 첫 번째 메시지만 확인
        
        if not message_received:
            print("   ⏰ 5초 내에 메시지가 없습니다 (정상)")
        
        await consumer.stop()
        
    except Exception as e:
        print(f"   ❌ Consumer 실패: {e}")
        return False
    
    return True

async def check_kafka_topics():
    """Kafka Topic 확인"""
    print("\n3️⃣ Kafka Topic 확인")
    try:
        # aiokafka 클라이언트로 Topic 정보 가져오기
        from aiokafka.cluster import ClusterMetadata
        from kafka import KafkaAdminClient, KafkaConsumer
        
        # 간단한 연결 확인
        consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'])
        topics = consumer.topics()
        consumer.close()
        
        print(f"   📋 사용 가능한 Topics: {list(topics)}")
        
        if 'chatbot-issue-events' in topics:
            print("   ✅ chatbot-issue-events Topic 존재")
        else:
            print("   ⚠️ chatbot-issue-events Topic 없음 (자동 생성 예정)")
            
    except Exception as e:
        print(f"   ❌ Topic 확인 실패: {e}")

async def main():
    print("🚀 Kafka 상태 확인 도구")
    print("=" * 50)
    
    # 기본 연결 확인
    success = await test_kafka_connection()
    
    # Topic 확인
    await check_kafka_topics()
    
    print(f"\n📊 결과:")
    if success:
        print("   🎉 Kafka가 정상적으로 작동하고 있습니다!")
        print("   💡 FastAPI 서버에서 실시간으로 메시지를 받을 준비가 되었습니다.")
    else:
        print("   ❌ Kafka 연결에 문제가 있습니다.")
        print("   💡 docker-compose ps로 Kafka 상태를 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(main())