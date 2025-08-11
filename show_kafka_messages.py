#!/usr/bin/env python3
"""실시간 Kafka 메시지 수신 데모"""

import asyncio
import json
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from datetime import datetime

async def show_real_time_messages():
    """실시간 Kafka 메시지 수신 데모"""
    print("🎯 실시간 Kafka 메시지 수신 데모")
    print("=" * 60)
    
    # Consumer 설정
    consumer = AIOKafkaConsumer(
        'chatbot-issue-events',
        bootstrap_servers='localhost:9092',
        group_id='demo-consumer-group',
        auto_offset_reset='latest',  # 최신 메시지부터 읽기
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    try:
        # Consumer 시작
        await consumer.start()
        print("✅ Kafka Consumer 시작됨")
        print("📨 메시지 대기 중... (Ctrl+C로 종료)")
        print("-" * 60)
        
        # 실시간 메시지 수신
        async for message in consumer:
            timestamp = datetime.now().strftime("%H:%M:%S")
            msg_data = message.value
            
            print(f"\n⏰ [{timestamp}] 📩 새 메시지 수신!")
            print(f"   🔧 이슈: {msg_data.get('issue', 'N/A')}")
            print(f"   📋 타입: {msg_data.get('processType', 'N/A')}")
            print(f"   🏭 설비: {msg_data.get('modeType', 'N/A')}")
            print(f"   📝 설명: {msg_data.get('description', 'N/A')}")
            print(f"   ✅ 해결: {'예' if msg_data.get('isSolved', False) else '아니오'}")
            print("-" * 60)
            
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
    finally:
        await consumer.stop()
        print("🔄 Consumer 종료됨")

async def send_demo_message():
    """데모용 메시지 전송"""
    print("\n📤 데모 메시지 전송 중...")
    
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8')
    )
    
    try:
        await producer.start()
        
        demo_message = {
            "issue": f"DEMO_{datetime.now().strftime('%H%M%S')}",
            "processType": "장애접수",
            "modeType": "프레스",
            "modeLogId": f"DEMO_LOG_{datetime.now().strftime('%H%M%S')}",
            "description": f"실시간 데모 메시지 - {datetime.now().strftime('%H:%M:%S')}",
            "isSolved": False,
            "timestamp": datetime.now().isoformat()
        }
        
        await producer.send_and_wait('chatbot-issue-events', value=demo_message)
        print("✅ 데모 메시지 전송 완료!")
        
    except Exception as e:
        print(f"❌ 메시지 전송 실패: {e}")
    finally:
        await producer.stop()

async def main():
    print("🚀 Kafka 실시간 메시지 수신/전송 데모")
    print("\n선택하세요:")
    print("1. 실시간 메시지 수신 (Consumer)")
    print("2. 데모 메시지 전송 (Producer)")
    print("3. 동시 실행 (수신하면서 메시지 전송)")
    
    choice = input("\n번호 선택 (1-3): ").strip()
    
    if choice == "1":
        await show_real_time_messages()
    elif choice == "2":
        await send_demo_message()
    elif choice == "3":
        # 백그라운드에서 Consumer 실행
        consumer_task = asyncio.create_task(show_real_time_messages())
        
        # 2초 후 메시지 전송
        await asyncio.sleep(2)
        await send_demo_message()
        
        # 5초 더 기다린 후 종료
        await asyncio.sleep(5)
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    asyncio.run(main())