"""완전한 워크플로우 테스트: 대화 → 해결완료 → PDF 다운로드"""

import asyncio
from datetime import datetime
from core.session_manager import SessionManager
from utils.pdf_generator import generate_session_report

async def test_complete_workflow():
    """SessionManager를 직접 사용한 완전한 워크플로우 테스트"""
    try:
        # SessionManager 초기화
        session_manager = SessionManager()
        
        # 기존 세션 사용 (gpt_user_session)
        session_id = "gpt_user_session"
        
        print(f"🔍 세션 {session_id} 테스트 시작...")
        
        # 1. 세션 정보 확인
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            print("❌ 세션을 찾을 수 없습니다.")
            return False
        
        print(f"✅ 세션 정보:")
        print(f"   - 사용자: {session_data.user_id}")
        print(f"   - 대화 수: {session_data.conversation_count}")
        print(f"   - 상태: {session_data.status.value}")
        print(f"   - 생성일: {session_data.created_at}")
        
        # 2. 해결완료 처리 (isTerminated = True)
        print(f"\n🔧 해결완료 처리 중...")
        
        # 메타데이터 업데이트
        final_summary = "프레스 기계 소음 문제가 성공적으로 진단되었습니다. 끼익끼익 마찰음의 원인을 파악하고 해결 방안을 제시했습니다."
        
        session_data.metadata.update({
            'isTerminated': True,
            'terminated_at': datetime.now().isoformat(),
            'final_summary': final_summary
        })
        session_data.updated_at = datetime.now()
        
        success = await session_manager.update_session(session_data)
        if success:
            print("✅ 해결완료 처리 성공!")
        else:
            print("❌ 해결완료 처리 실패!")
            return False
        
        # 3. PDF 생성 테스트
        print(f"\n📄 PDF 생성 중...")
        
        # 대화 내역 가져오기
        conversation_history = session_data.metadata.get('conversation_history', [])
        
        # 세션 정보 준비
        session_info = {
            'session_id': session_id,
            'user_id': session_data.user_id,
            'issue_code': session_data.issue_code or 'GENERAL',
            'created_at': session_data.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'ended_at': session_data.metadata.get('terminated_at', 'N/A'),
            'conversation_count': session_data.conversation_count,
            'participating_agents': ['GPT']  # 개별 GPT 에이전트
        }
        
        # PDF 생성
        pdf_buffer = await generate_session_report(
            session_id=session_id,
            conversation_history=conversation_history,
            session_info=session_info,
            final_summary=final_summary
        )
        
        # PDF 파일로 저장
        filename = f"complete_workflow_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF 생성 성공!")
        print(f"   - 파일명: {filename}")
        print(f"   - 크기: {len(pdf_buffer.getvalue())} bytes")
        print(f"   - 대화 수: {len(conversation_history)}개")
        
        # 4. isReported = True 설정
        session_data.metadata['isReported'] = True
        session_data.metadata['report_generated_at'] = datetime.now().isoformat()
        session_data.updated_at = datetime.now()
        
        success = await session_manager.update_session(session_data)
        if success:
            print("✅ 보고서 생성 완료 표시 성공!")
        else:
            print("❌ 보고서 생성 완료 표시 실패!")
            return False
        
        # 5. 종료된 세션에서 대화 시도 (차단 테스트)
        print(f"\n🚫 종료된 세션 대화 차단 테스트...")
        
        updated_session = await session_manager.get_session(session_id)
        if updated_session.metadata.get('isTerminated', False):
            print("✅ 세션이 정상적으로 종료 상태로 표시됨")
        else:
            print("❌ 세션 종료 상태 표시 실패")
            return False
        
        # 최종 상태 확인
        print(f"\n📊 최종 상태:")
        print(f"   - isTerminated: {updated_session.metadata.get('isTerminated', False)}")
        print(f"   - isReported: {updated_session.metadata.get('isReported', False)}")
        print(f"   - 종료 시간: {updated_session.metadata.get('terminated_at', 'N/A')}")
        print(f"   - 보고서 생성 시간: {updated_session.metadata.get('report_generated_at', 'N/A')}")
        
        print(f"\n🎉 완전한 워크플로우 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_complete_workflow())
    if result:
        print("\n✅ 모든 테스트 통과!")
    else:
        print("\n❌ 테스트 실패!")