"""PDF 생성 기능 테스트 스크립트"""

import asyncio
from datetime import datetime
from utils.pdf_generator import generate_session_report

# 테스트 데이터
test_conversation_history = [
    {
        "user_message": "안녕하세요, 저는 김철수입니다. 우리 공장의 프레스 기계에서 이상한 소음이 계속 발생하고 있어요. 어떻게 해결해야 할까요?",
        "bot_response": "안녕하세요, 김철수님. 프레스 기계에서 발생하는 이상한 소음에 대해 문제를 진단하고 해결 방법을 제시하겠습니다.\n\n### 1. 문제의 근본 원인 분석\n프레스 기계에서 발생하는 소음은 여러 원인으로 인해 발생할 수 있습니다:\n- 유압 시스템 문제: 유압 압력이 임계값을 초과하거나 미달할 경우\n- 기계적 마모: 베어링, 기어 등의 마모\n- 진동 문제: 기계의 불균형이나 고정 불량\n- 오일 상태: 유압 오일의 오염이나 점도 변화",
        "timestamp": "2025-08-05 16:27:00"
    },
    {
        "user_message": "네, 감사합니다. 소음은 '끼익끼익' 하는 마찰음 같은 소리가 나요. 그리고 프레스 작동할 때마다 발생합니다. 유압 오일은 언제 교체했는지 기억이 안 나네요.",
        "bot_response": "마찰음에 대한 추가 정보를 주셔서 감사합니다. '끼익끼익' 소음은 일반적으로 기계적 마찰이나 마모로 인해 발생할 수 있습니다.\n\n### 원인 분석\n- 마찰음의 원인: 베어링, 기어, 슬라이드 부품의 마찰\n- 유압 오일 상태: 오일이 오래되어 점도가 낮아지거나 오염\n- 부품 마모: 기계 내부 부품의 마모나 손상 가능성",
        "timestamp": "2025-08-05 16:27:16"
    },
    {
        "user_message": "알겠습니다. 유압 오일을 확인해보니 좀 탁하고 검은색이 섞여 있어요. 그리고 베어링 부분에서 소음이 가장 큰 것 같습니다. 어떻게 처리해야 할까요?",
        "bot_response": "유압 오일이 탁하고 검은색이 섞여 있으며, 베어링 부분에서 소음이 발생한다는 정보를 바탕으로 해결 방법을 제시하겠습니다.\n\n### 해결 방법\n1. 유압 오일 교체: 오염된 오일을 즉시 교체\n2. 오일 필터 점검: 필터도 함께 교체\n3. 베어링 점검: 베어링 상태 확인 및 필요시 교체\n4. 시스템 청소: 전체 유압 시스템 청소",
        "timestamp": "2025-08-05 16:27:30"
    },
    {
        "user_message": "완벽합니다! 매우 도움이 되었습니다. 유압 오일 교체와 베어링 점검을 바로 진행하겠습니다. 대략적인 작업 시간과 비용은 어느 정도 예상되나요?",
        "bot_response": "유압 오일 교체와 베어링 점검을 진행하기로 하신 점에 대해 기쁘게 생각합니다.\n\n### 예상 작업 시간 및 비용\n#### 유압 오일 교체\n- 작업 시간: 약 1~2시간\n- 비용: 유압 오일 200,000~600,000원 (20~30L)\n\n#### 베어링 점검 및 교체\n- 작업 시간: 약 2~4시간\n- 비용: 베어링 50,000~150,000원\n\n총 예상 비용: 250,000~750,000원\n총 작업 시간: 3~6시간",
        "timestamp": "2025-08-05 16:27:47"
    }
]

test_session_info = {
    'session_id': 'sess_test_pdf_demo',
    'user_id': 'kim_chulsu',
    'issue_code': 'PRESS_NOISE',
    'created_at': '2025-08-05 16:25:00',
    'ended_at': '2025-08-05 16:30:00',
    'conversation_count': 4,
    'participating_agents': ['GPT', 'Clova']
}

test_final_summary = """프레스 기계 소음 문제가 성공적으로 해결되었습니다. 
문제 원인: 유압 오일 오염 및 베어링 마모
해결 방안: 
1. 유압 오일 교체 (20-30L, 비용 200,000-600,000원)
2. 베어링 점검 및 교체 (비용 50,000-150,000원)
3. 총 작업 시간: 3-6시간
4. 총 예상 비용: 250,000-750,000원

김철수님께서 만족하시며 즉시 작업을 진행하기로 결정하셨습니다."""

async def test_pdf_generation():
    """PDF 생성 테스트"""
    try:
        print("PDF 생성 테스트 시작...")
        
        # PDF 생성
        pdf_buffer = await generate_session_report(
            session_id=test_session_info['session_id'],
            conversation_history=test_conversation_history,
            session_info=test_session_info,
            final_summary=test_final_summary
        )
        
        # PDF 파일로 저장
        filename = f"test_chatbot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF 생성 성공! 파일명: {filename}")
        print(f"📄 PDF 크기: {len(pdf_buffer.getvalue())} bytes")
        print(f"📝 대화 수: {len(test_conversation_history)}개")
        print(f"👤 사용자: {test_session_info['user_id']}")
        print(f"🔧 이슈 코드: {test_session_info['issue_code']}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_pdf_generation())