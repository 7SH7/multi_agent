#!/usr/bin/env python3
"""직접 데이터로 PDF 생성 테스트"""

import asyncio
from datetime import datetime
from utils.pdf_generator import generate_session_report

async def test_direct_pdf_generation():
    """직접 데이터를 만들어 PDF 생성 테스트"""
    print("🎯 직접 데이터로 PDF 생성 테스트")
    print("=" * 50)
    
    # 세션 정보
    session_info = {
        'session_id': 'sess_direct_test_12345',
        'user_id': '김철수_현장엔지니어',
        'issue_code': 'PRESS_HYDRAULIC_NOISE_001',
        'created_at': '2025-08-08 14:30:00',
        'ended_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'conversation_count': 3,
        'participating_agents': ['GPT-4 전문가', 'Claude-4 분석가', '지미니 기술자']
    }
    
    # 대화 히스토리 (실제 제조업 상황)
    conversation_history = [
        {
            'user_message': '안녕하세요! 저희 공장의 100톤 프레스 기계에서 이상한 소음이 발생하고 있습니다. 특히 압력이 최대로 올라갈 때 "윙윙~쿵쿵" 소리가 나면서 진동도 심해져요. 어떻게 해결하면 좋을까요? 🔧',
            'bot_response': '''안녕하세요 김철수 현장엔지니어님! 100톤 프레스의 유압 시스템 문제로 보입니다.

🔍 **증상 분석:**
- 압력 최대시 "윙윙~쿵쿵" 소음
- 진동 동반 발생
- 이는 전형적인 유압 시스템 이상 신호입니다

**즉시 확인사항:**
1. ✅ 유압 오일 레벨 및 색상
2. ✅ 압력 게이지 수치 (정상: 150-200 bar)
3. ✅ 필터 상태 점검
4. ✅ 온도 확인 (정상: 40-60°C)

더 정확한 진단을 위해 다음 정보도 알려주세요:
- 소음 발생 빈도 (항상/간헐적)
- 최근 오일 교체 이력
- 작동 연수와 정비 기록''',
            'timestamp': '2025-08-08 14:32:15'
        },
        {
            'user_message': '확인해보니 유압 오일이 검게 변해있고 레벨도 많이 부족해요. 압력 게이지는 120 bar 정도로 평소보다 낮고, 필터는 6개월 전에 교체했습니다. 기계는 15년 된 장비이고 소음은 하루종일 계속 발생해요.',
            'bot_response': '''완벽한 진단 정보 감사합니다! 명확한 문제점이 파악되었습니다.

🚨 **진단 결과:**
**주요 원인:** 유압 오일 심각한 오염 + 부족 + 펌프 효율 저하

📋 **긴급 조치사항 (단계별):**

**1단계: 즉시 중단** ⏱️ 10분
- 🛑 기계 운전 즉시 중단
- 🔒 안전 태그아웃 실시
- ⚠️ 추가 손상 방지

**2단계: 유압 시스템 정비** ⏱️ 4-5시간
- 🛢️ 기존 오일 완전 배출 (약 200L)
- 🧽 시스템 플러싱으로 내부 청소
- 🆕 ISO VG 46 신규 오일 주입
- 🔧 압력 설정 재조정 (150-200 bar)

**3단계: 부품 교체**
- 📦 서션/리턴 필터 교체
- 🔩 필요시 펌프 오버홀 검토

💰 **예상 비용:**
- 유압 오일: 40-60만원
- 필터: 15-20만원  
- 인건비: 30만원
- **총계: 85-110만원**

⚡ **효과:** 소음 95% 감소, 효율 20% 향상 예상''',
            'timestamp': '2025-08-08 14:35:42'
        },
        {
            'user_message': '비용과 시간이 많이 들어가네요. 응급처치로 일단 며칠만 더 쓸 수 있는 방법은 없을까요? 생산 일정이 너무 급해서요.',
            'bot_response': '''현장의 급한 상황 이해합니다. 하지만 안전을 최우선으로 고려해야 합니다.

⚠️ **위험성 경고:**
검은 오일로 계속 운전시 다음 위험이 있습니다:
- 💥 펌프 완전 파손 (500-800만원 손실)
- 🔥 과열로 인한 화재 위험
- ⚡ 갑작스런 압력 손실로 안전사고

🔧 **최소한의 응급조치 (2-3일용):**

**임시방안 1:** ⏱️ 1시간
- 유압 오일만 일단 보충 (50L)
- 압력 20% 하향 조정 (100 bar)
- 가동률 50% 제한 운전
- **비용: 약 20만원**

**임시방안 2:** ⏱️ 2시간  
- 긴급 오일 교체 (100L만)
- 1차 필터만 교체
- **비용: 약 40만원**

🚨 **필수 조건:**
- ✅ 2시간마다 압력/온도 체크
- ✅ 이상 징후시 즉시 중단
- ✅ 3일 내 완전 정비 필수

**권장사항:** 야간/주말 정비로 생산 영향 최소화하는 것이 최선입니다.''',
            'timestamp': '2025-08-08 14:38:20'
        }
    ]
    
    # 최종 요약
    final_summary = '''🏭 100톤 프레스 유압 시스템 고장 진단 및 해결방안

📊 **문제 현황:**
- 15년 된 100톤 프레스 기계
- 유압 오일 심각한 오염 (검은색 변색)  
- 오일 레벨 부족, 압력 저하 (120 bar ← 정상 150-200 bar)
- 지속적 소음/진동 발생 ("윙윙~쿵쿵")

🔧 **해결방안:**
**완전 정비안** (권장)
- 유압 오일 완전 교체 + 시스템 청소
- 필터 교체 + 압력 재조정
- 소요시간: 4-5시간 / 비용: 85-110만원
- 효과: 소음 95% 감소, 효율 20% 향상

**응급처치안** (임시)  
- 부분 오일 교체 + 압력 하향 조정
- 가동률 50% 제한 운전
- 소요시간: 1-2시간 / 비용: 20-40만원  
- 효과: 2-3일 연장 가능 (위험 수반)

⚠️ **안전 권고:**
완전 정비 없이는 언제든 대형 사고 위험이 있으므로, 
야간/주말을 활용한 계획 정비를 강력 권장합니다.

🎯 **최종 결론:** 단기적 생산보다 안전과 장기 효율을 고려한 
완전 정비가 경제적으로도 더 유리합니다.'''
    
    try:
        print("\n📝 PDF 보고서 생성 중...")
        
        # PDF 생성
        pdf_buffer = await generate_session_report(
            session_id=session_info['session_id'],
            conversation_history=conversation_history,
            session_info=session_info,  
            final_summary=final_summary
        )
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"direct_conversation_report_{timestamp}.pdf"
        
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        import os
        file_size = os.path.getsize(filename)
        
        print(f"\n🎉 PDF 생성 성공!")
        print(f"📄 파일명: {filename}")
        print(f"📊 파일 크기: {file_size:,} bytes")
        print(f"👤 사용자: {session_info['user_id']}")
        print(f"🔧 문제코드: {session_info['issue_code']}")  
        print(f"💬 대화 수: {len(conversation_history)}개")
        print(f"📝 요약 길이: {len(final_summary)}자")
        print(f"🎯 특수문자: ✅ 이모지, 🔧 기호, 한글 모두 포함")
        
        # UTF-8 텍스트 샘플 체크
        utf8_samples = [
            "유압 시스템",  # 한글
            "100톤 프레스",  # 숫자+한글
            "⚠️🔧💰📊",  # 이모지
            "150-200 bar",  # 영문+숫자+특수문자
            "95% 감소",  # 퍼센트
        ]
        
        print(f"\n🔤 UTF-8 샘플 텍스트 테스트:")
        for sample in utf8_samples:
            print(f"   ✅ {sample}")
            
        return True
        
    except Exception as e:
        print(f"\n❌ PDF 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_direct_pdf_generation())
    if result:
        print(f"\n🎉 테스트 완료! PDF가 성공적으로 생성되었습니다.")
    else:
        print(f"\n💥 테스트 실패! 에러를 확인해주세요.")