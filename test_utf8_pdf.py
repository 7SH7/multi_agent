#!/usr/bin/env python3
"""UTF-8 한글 PDF 생성 테스트"""

import asyncio
import os
from datetime import datetime
from utils.pdf_generator import ChatbotReportGenerator

async def test_utf8_korean_pdf():
    """한글 UTF-8 PDF 생성 테스트"""
    print("🇰🇷 한글 UTF-8 PDF 생성 테스트 시작...")
    
    # PDF 생성기 초기화
    pdf_generator = ChatbotReportGenerator()
    
    # 한글 테스트 데이터
    session_info = {
        'session_id': 'sess_한글테스트_12345',
        'user_id': '김철수_사용자',
        'issue_code': '프레스_소음_문제',
        'created_at': '2025-08-08 13:45:00',
        'ended_at': '2025-08-08 13:50:00',
        'conversation_count': 3,
        'participating_agents': ['GPT에이전트', '지미니에이전트', '클로바에이전트']
    }
    
    # 한글 대화 내역
    conversation_history = [
        {
            'user_message': '안녕하세요! 프레스 기계에서 이상한 소음이 납니다. 도움을 받을 수 있을까요? 🔧',
            'bot_response': '안녕하세요! 프레스 기계의 소음 문제로 문의주셨군요. 어떤 종류의 소음인지 자세히 설명해주실 수 있나요? (예: 삐걱거리는 소리, 쿵쿵거리는 소리, 윙윙거리는 소리 등)',
            'timestamp': '2025-08-08 13:45:30'
        },
        {
            'user_message': '기계를 작동시킬 때마다 "쿵쿵" 하는 소리가 나고, 가끔씩 "삐걱삐걱" 소리도 들립니다. 특히 압력이 최대일 때 더 심해집니다.',
            'bot_response': '말씀해주신 증상으로 보아 다음과 같은 원인들을 의심해볼 수 있습니다:\n\n1. 유압 시스템의 압력 불균형\n2. 베어링 마모로 인한 진동\n3. 오일 부족 또는 오염\n\n먼저 유압 오일 레벨을 확인해보시고, 베어링 부분에 이상이 없는지 점검해주세요.',
            'timestamp': '2025-08-08 13:47:15'
        },
        {
            'user_message': '네, 감사합니다! 유압 오일을 확인해보니 색깔이 탁해져 있었습니다. 교체하면 문제가 해결될까요?',
            'bot_response': '네, 정확한 진단이십니다! 유압 오일이 탁해졌다는 것은 오염되었거나 수명이 다했다는 신호입니다. 다음 순서로 조치해주세요:\n\n✅ 1단계: 기존 오일 완전 배출\n✅ 2단계: 필터 교체\n✅ 3단계: 새 유압 오일 주입\n✅ 4단계: 시스템 테스트\n\n작업 후 소음이 줄어들 것으로 예상됩니다. 추가 문제가 있으시면 언제든 문의주세요! 😊',
            'timestamp': '2025-08-08 13:49:30'
        }
    ]
    
    # 최종 요약 (한글)
    final_summary = """프레스 기계 소음 문제 해결 상담 요약:
    
🔍 문제점:
- 프레스 작동 시 쿵쿵거리는 소음
- 압력 최대 시 삐걱거리는 소음 발생
- 유압 오일 탁함 확인

💡 해결방안:
- 유압 오일 교체 (오염된 오일 확인됨)
- 필터 교체 동시 진행
- 시스템 전체 점검 수행

📋 작업 순서:
1. 기존 오일 배출
2. 필터 교체
3. 새 오일 주입
4. 시스템 테스트

예상 결과: 소음 문제 해결 및 기계 성능 향상 기대됩니다."""
    
    try:
        # PDF 생성
        pdf_buffer = await pdf_generator.generate_chat_report(
            session_id=session_info['session_id'],
            conversation_history=conversation_history,
            session_info=session_info,
            final_summary=final_summary
        )
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_utf8_korean_report_{timestamp}.pdf"
        
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        file_size = os.path.getsize(filename)
        
        print(f"✅ UTF-8 한글 PDF 생성 완료!")
        print(f"📄 파일명: {filename}")
        print(f"📊 파일 크기: {file_size:,} bytes")
        print(f"🗣️ 대화 수: {len(conversation_history)}개")
        print(f"👤 사용자: {session_info['user_id']}")
        print(f"🔧 문제: {session_info['issue_code']}")
        print(f"🔤 특수문자 테스트: ✅ 🔧 😊 🇰🇷 💡 📋")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_utf8_korean_pdf())