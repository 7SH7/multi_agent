#!/usr/bin/env python3
"""실제 대화 세션으로 PDF 생성 테스트"""

import asyncio
import json
from datetime import datetime
from core.session_manager import SessionManager
from utils.pdf_generator import generate_session_report

async def test_real_conversation_pdf():
    """실제 대화 세션을 만들어 PDF 생성 테스트"""
    print("🎯 실제 대화 세션 PDF 생성 테스트 시작")
    print("=" * 60)
    
    # 세션 매니저 초기화
    session_manager = SessionManager()
    
    try:
        # 1. 새 세션 생성
        print("\n1️⃣ 새 대화 세션 생성...")
        session_id = await session_manager.create_session(
            user_id="김철수_엔지니어",
            issue_code="PRESS_HYDRAULIC_NOISE"
        )
        print(f"✅ 세션 생성 완료: {session_id}")
        
        # 2. 첫 번째 대화 추가
        print("\n2️⃣ 첫 번째 대화 추가...")
        conversation1 = {
            "user_message": "안녕하세요! 프레스 기계에서 이상한 소음이 납니다. 유압 시스템에 문제가 있는 것 같아요. 어떻게 해결하면 좋을까요? 🔧",
            "bot_response": """안녕하세요 김철수 엔지니어님! 프레스 기계의 유압 시스템 소음 문제로 문의주셨군요. 

이런 증상은 다음과 같은 원인들이 있을 수 있습니다:

1. **유압 오일 문제**
   - 오일 레벨 부족
   - 오일 품질 저하 (수분 함유, 오염)
   - 점도 불일치

2. **유압 펌프 문제**  
   - 펌프 내부 마모
   - 밸브 시트 불량
   - 압력 설정 오류

3. **필터 막힘**
   - 서션 필터 막힘
   - 리턴 필터 오염

먼저 다음을 확인해보시기 바랍니다:
✅ 유압 오일 레벨과 색상 확인
✅ 압력 게이지 수치 점검  
✅ 필터 상태 점검

더 구체적인 소음 양상(윙윙, 쿵쿵, 삐걱 등)을 알려주시면 더 정확한 진단을 도와드리겠습니다!""",
            "agent_used": "GPT-4",
            "processing_time": 23.5,
            "timestamp": datetime.now().isoformat()
        }
        
        success1 = await session_manager.add_conversation_detailed(session_id, conversation1)
        print(f"✅ 첫 번째 대화 저장: {success1}")
        
        # 3. 두 번째 대화 추가
        print("\n3️⃣ 두 번째 대화 추가...")
        conversation2 = {
            "user_message": "유압 오일을 확인해보니 색깔이 검게 변해있고, 압력 게이지가 평소보다 낮게 나와요. 그리고 소음은 '윙윙' 거리는 소리가 주로 납니다.",
            "bot_response": """검은색 유압 오일과 낮은 압력, 그리고 윙윙거리는 소음... 명확한 진단이 나왔습니다! 

🔍 **진단 결과:**
유압 오일 오염 및 펌프 효율 저하가 주요 원인입니다.

📋 **즉시 조치사항 (우선순위 순):**

1. **[긴급] 기계 운전 중단** (15분)
   - 추가 손상 방지를 위해 즉시 정지
   - 안전 태그 부착

2. **[1단계] 유압 오일 교체** (2-3시간)  
   - 기존 오일 완전 배출
   - 시스템 플러싱 (청소)
   - ISO VG 46 등급 신규 오일 주입
   - 예상 비용: 약 30-50만원

3. **[2단계] 필터 교체** (30분)
   - 서션/리턴 필터 동시 교체  
   - 예상 비용: 약 10-15만원

4. **[3단계] 압력 재조정** (1시간)
   - 릴리프 밸브 압력 설정
   - 시스템 테스트 운전

⚠️ **주의사항:**
- 작업 중 안전장비 필수 착용
- 오일 교체 시 환경 규정 준수
- 시운전 중 소음/진동 재확인

총 예상 시간: 4-5시간
총 예상 비용: 40-65만원

작업 후 소음은 90% 이상 개선될 것으로 예상됩니다! 🎯""",
            "agent_used": "Claude-4",
            "processing_time": 45.2,
            "timestamp": datetime.now().isoformat()
        }
        
        success2 = await session_manager.add_conversation_detailed(session_id, conversation2)
        print(f"✅ 두 번째 대화 저장: {success2}")
        
        # 4. 세션 정보 조회
        print("\n4️⃣ 세션 정보 조회...")
        session_data = await session_manager.get_session(session_id)
        print(f"✅ 대화 수: {session_data.conversation_count}")
        
        # 5. 대화 히스토리 조회
        print("\n5️⃣ 대화 히스토리 조회...")
        conversations = await session_manager.get_conversation_history(session_id)
        print(f"✅ 히스토리 조회: {len(conversations)}개 대화")
        
        # 6. PDF 생성을 위한 데이터 준비
        print("\n6️⃣ PDF 생성 데이터 준비...")
        session_info = {
            'session_id': session_id,
            'user_id': session_data.user_id,
            'issue_code': session_data.issue_code,
            'created_at': session_data.created_at.strftime('%Y-%m-%d %H:%M:%S') if session_data.created_at else '',
            'ended_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'conversation_count': session_data.conversation_count,
            'participating_agents': ['GPT-4', 'Claude-4']
        }
        
        conversation_history = []
        for conv in conversations:
            conversation_history.append({
                'user_message': conv.get('user_message', ''),
                'bot_response': conv.get('bot_response', ''),
                'timestamp': conv.get('timestamp', '')
            })
        
        final_summary = """프레스 유압 시스템 소음 문제 해결 상담 완료

🔍 **문제 진단:**
- 유압 오일 심각한 오염 (검은색 변색)
- 시스템 압력 저하 
- 펌프 효율 저하로 인한 윙윙 소음

💡 **해결 방안:**
- 유압 오일 완전 교체 (ISO VG 46)
- 필터 시스템 교체
- 압력 재조정 및 시스템 점검

💰 **예상 비용:** 40-65만원
⏰ **예상 시간:** 4-5시간  
📈 **개선 효과:** 90% 이상 소음 감소 예상

✅ 전문가 의견: 즉시 정비 진행 권장"""
        
        # 7. PDF 생성
        print("\n7️⃣ PDF 보고서 생성 중...")
        pdf_buffer = await generate_session_report(
            session_id=session_id,
            conversation_history=conversation_history,
            session_info=session_info,
            final_summary=final_summary
        )
        
        # 8. PDF 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_conversation_report_{timestamp}.pdf"
        
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        import os
        file_size = os.path.getsize(filename)
        
        print(f"\n🎉 PDF 생성 성공!")
        print(f"📄 파일명: {filename}")
        print(f"📊 파일 크기: {file_size:,} bytes")
        print(f"👤 사용자: {session_info['user_id']}")
        print(f"🔧 문제: {session_info['issue_code']}")
        print(f"💬 대화 수: {len(conversation_history)}개")
        print(f"📝 요약 길이: {len(final_summary)}자")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_real_conversation_pdf())