"""Issue 해결 이벤트 전송용 Kafka Producer"""

import asyncio
import json
import logging
from datetime import datetime
from aiokafka import AIOKafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_issue_solved_event(issue_id: str, description: str = None):
    """특정 Issue 해결 이벤트 전송"""
    
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8')
    )
    
    try:
        await producer.start()
        
        # Issue 해결 이벤트
        solve_event = {
            "issue": issue_id,
            "processType": "장애접수",  # 기본값
            "modeType": "프레스",      # 기본값
            "modeLogId": f"SOLVED_{issue_id}",
            "description": description or f"Issue {issue_id} 해결됨",
            "isSolved": True,  # 해결됨!
            "timestamp": datetime.now().isoformat()
        }
        
        # 메시지 전송
        await producer.send_and_wait(
            'chatbot-issue-events',
            value=solve_event
        )
        
        logger.info(f"✅ Issue 해결 이벤트 전송 완료: {issue_id}")
        logger.info(f"📝 설명: {solve_event['description']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Issue 해결 이벤트 전송 실패: {str(e)}")
        return False
    finally:
        await producer.stop()


async def solve_multiple_issues():
    """여러 Issue 해결 이벤트 전송"""
    
    issues_to_solve = [
        {
            "issue_id": "PRESS_001_20250806_001",
            "description": "프레스 기계 유압 시스템 수리 완료"
        },
        {
            "issue_id": "WELDING_002_20250806_001", 
            "description": "용접 로봇 정기 점검 및 캘리브레이션 완료"
        },
        {
            "issue_id": "PAINTING_003_20250806_001",
            "description": "도장 부스 스프레이 노즐 교체 및 청소 완료"
        }
    ]
    
    logger.info(f"🔧 {len(issues_to_solve)}개 Issue 해결 이벤트 전송 시작...")
    
    success_count = 0
    for issue_info in issues_to_solve:
        success = await send_issue_solved_event(
            issue_info["issue_id"],
            issue_info["description"]
        )
        
        if success:
            success_count += 1
            
        # 잠시 대기
        await asyncio.sleep(1)
    
    logger.info(f"✅ {success_count}/{len(issues_to_solve)}개 Issue 해결 이벤트 전송 완료")


if __name__ == "__main__":
    print("🔧 Issue 해결 이벤트 Producer")
    print("=" * 50)
    
    mode = input("모드 선택 (1: 단일 Issue, 2: 여러 Issue, 3: 직접 입력): ")
    
    if mode == "1":
        issue_id = input("해결할 Issue ID: ")
        description = input("해결 설명 (선택사항): ")
        
        asyncio.run(send_issue_solved_event(issue_id, description or None))
        
    elif mode == "2":
        asyncio.run(solve_multiple_issues())
        
    elif mode == "3":
        issue_id = input("Issue ID: ")
        description = input("해결 설명: ")
        
        asyncio.run(send_issue_solved_event(issue_id, description))
        
    else:
        print("잘못된 선택입니다.")
    
    print("\n📋 확인 방법:")
    print("1. FastAPI 서버 로그에서 '관련 세션들 종료 처리' 메시지 확인")
    print("2. GET /api/kafka/issues/{issue_id}/details - 세션 상태 확인")
    print("3. 해당 세션으로 대화 시도 - 접근 차단 확인")