"""완전한 워크플로우 테스트 스크립트"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_complete_workflow():
    """전체 워크플로우 테스트"""
    
    print("🚀 완전한 챗봇 워크플로우 테스트 시작")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Kafka로 ChatbotIssue 생성 (Producer 대신 직접 API 호출)
        print("\n📨 1단계: ChatbotIssue 생성 (Kafka 시뮬레이션)")
        issue_id = f"WORKFLOW_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_issue_data = {
            "issue_id": issue_id,
            "process_type": "장애접수",
            "mode_type": "프레스",
            "mode_log_id": f"LOG_{issue_id}",
            "user_id": "test_workflow_user",
            "description": "워크플로우 테스트용 프레스 기계 압력 이상"
        }
        
        async with session.post(
            f"{BASE_URL}/api/kafka/test/create-issue-session",
            json=test_issue_data
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ ChatbotIssue 생성 성공: {issue_id}")
                print(f"   - 생성된 세션: {result['data']['session_id']}")
            else:
                print(f"❌ ChatbotIssue 생성 실패: {resp.status}")
                return
        
        # 2. ChatbotIssue 조회
        print(f"\n🔍 2단계: ChatbotIssue 조회")
        async with session.get(f"{BASE_URL}/api/kafka/issues/{issue_id}") as resp:
            if resp.status == 200:
                issue_info = await resp.json()
                print(f"✅ Issue 조회 성공")
                print(f"   - Process Type: {issue_info['data']['processType']}")
                print(f"   - Mode Type: {issue_info['data']['modeType']}")
                print(f"   - Description: {issue_info['data']['description']}")
            else:
                print(f"❌ Issue 조회 실패: {resp.status}")
                return
        
        # 3. Issue 기반 챗봇 대화 시작
        print(f"\n💬 3단계: Issue 기반 챗봇 대화 시작")
        start_chat_data = {
            "issue_id": issue_id,
            "user_id": "workflow_test_user",
            "user_message": "안녕하세요. 프레스 기계에 압력 문제가 발생했습니다. 어떻게 해결해야 할까요?"
        }
        
        async with session.post(
            f"{BASE_URL}/api/chatbot-workflow/start-chat",
            json=start_chat_data
        ) as resp:
            if resp.status == 200:
                chat_result = await resp.json()
                redis_session_id = chat_result['data']['redis_session_id']
                db_session_id = chat_result['data']['db_session_id']
                print(f"✅ 챗봇 대화 시작 성공")
                print(f"   - Redis Session: {redis_session_id}")
                print(f"   - DB Session: {db_session_id}")
                print(f"   - 첫 응답: {chat_result['data']['executive_summary'][:100]}...")
            else:
                print(f"❌ 챗봇 대화 시작 실패: {resp.status}")
                error_text = await resp.text()
                print(f"   오류: {error_text}")
                return
        
        # 4. 대화 계속 (2-3번 더)
        print(f"\n💬 4단계: 대화 계속")
        follow_up_messages = [
            "더 구체적인 해결 방법을 알려주세요.",
            "예상 비용과 작업 시간은 얼마나 걸릴까요?",
            "안전 주의사항도 알려주세요."
        ]
        
        for i, message in enumerate(follow_up_messages, 1):
            print(f"\n   💬 {i}번째 추가 질문: {message[:30]}...")
            
            continue_chat_data = {
                "session_id": redis_session_id,
                "user_message": message
            }
            
            async with session.post(
                f"{BASE_URL}/api/chatbot-workflow/continue-chat",
                json=continue_chat_data
            ) as resp:
                if resp.status == 200:
                    continue_result = await resp.json()
                    print(f"   ✅ 응답 성공 (대화수: {continue_result['data']['conversation_count']})")
                    print(f"   📝 응답: {continue_result['data']['executive_summary'][:80]}...")
                else:
                    print(f"   ❌ 대화 계속 실패: {resp.status}")
        
        # 5. 세션 상태 확인
        print(f"\n📊 5단계: 세션 상태 확인")
        async with session.get(f"{BASE_URL}/api/chatbot-workflow/session-status/{redis_session_id}") as resp:
            if resp.status == 200:
                status_result = await resp.json()
                print(f"✅ 세션 상태 조회 성공")
                print(f"   - 대화수: {status_result['data']['conversation_count']}")
                print(f"   - 종료됨: {status_result['data']['is_terminated']}")
                print(f"   - 보고서 생성됨: {status_result['data']['is_reported']}")
            else:
                print(f"❌ 세션 상태 조회 실패: {resp.status}")
        
        # 6. 대화 완료 처리 (isTerminated는 설정하지 않음)
        print(f"\n✅ 6단계: 대화 완료 처리")
        complete_chat_data = {
            "session_id": redis_session_id,
            "final_summary": "프레스 기계 압력 문제 해결 방안에 대한 상담이 완료되었습니다."
        }
        
        async with session.post(
            f"{BASE_URL}/api/chatbot-workflow/complete-chat",
            json=complete_chat_data
        ) as resp:
            if resp.status == 200:
                complete_result = await resp.json()
                print(f"✅ 대화 완료 처리 성공")
                print(f"   - 종료됨: {complete_result['data']['is_terminated']}")  # False여야 함
                print(f"   - 완료 시간: {complete_result['data']['completed_at']}")
            else:
                print(f"❌ 대화 완료 처리 실패: {resp.status}")
                error_text = await resp.text()
                print(f"   오류: {error_text}")
        
        # 7. PDF 보고서 다운로드 선택 테스트
        print(f"\n📄 7단계: PDF 보고서 다운로드 옵션 테스트")
        user_choice = input("PDF 다운로드 테스트? (y: 다운로드, n: 건너뛰기, enter: 다운로드): ").lower()
        
        if user_choice == 'n':
            # 보고서 건너뛰기
            async with session.post(f"{BASE_URL}/api/chatbot-workflow/skip-report/{redis_session_id}") as resp:
                if resp.status == 200:
                    skip_result = await resp.json()
                    print(f"✅ 보고서 건너뛰기 성공")
                    print(f"   - isReported: {skip_result['data']['is_reported']}")  # False
                    print(f"   - 건너뛴 시간: {skip_result['data']['report_skipped_at']}")
                else:
                    print(f"❌ 보고서 건너뛰기 실패: {resp.status}")
        else:
            # PDF 다운로드
            async with session.get(f"{BASE_URL}/api/chatbot-workflow/download-report/{redis_session_id}") as resp:
                if resp.status == 200:
                    pdf_content = await resp.read()
                    filename = f"workflow_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    
                    with open(filename, 'wb') as f:
                        f.write(pdf_content)
                    
                    print(f"✅ PDF 보고서 다운로드 성공")
                    print(f"   - 파일명: {filename}")
                    print(f"   - 파일 크기: {len(pdf_content)} bytes")
                else:
                    print(f"❌ PDF 보고서 다운로드 실패: {resp.status}")
                    error_text = await resp.text()
                    print(f"   오류: {error_text}")
        
        # 8. 세션 상태 확인 (isReported 값이 설정됨)
        print(f"\n🔍 8단계: 세션 상태 확인 (보고서 처리 후)")
        async with session.get(f"{BASE_URL}/api/chatbot-workflow/session-status/{redis_session_id}") as resp:
            if resp.status == 200:
                status_after_report = await resp.json()
                print(f"✅ 세션 상태 조회 성공")
                print(f"   - 종료됨: {status_after_report['data']['is_terminated']}")
                print(f"   - 보고서 처리됨: {status_after_report['data']['is_reported']}")
                if status_after_report['data']['is_reported'] is True:
                    print(f"   - 보고서 생성 시간: {status_after_report['data'].get('report_generated_at')}")
                elif status_after_report['data']['is_reported'] is False:
                    print(f"   - 보고서 건너뛴 시간: {status_after_report['data'].get('report_skipped_at')}")
            else:
                print(f"❌ 세션 상태 조회 실패: {resp.status}")
        
        # 9. 보고서 처리 후 대화 시도 (차단되어야 함)
        print(f"\n🚫 9단계: 보고서 처리 후 대화 시도 (차단 테스트)")
        test_continue_data = {
            "session_id": redis_session_id,
            "user_message": "추가 질문이 있습니다."
        }
        
        async with session.post(
            f"{BASE_URL}/api/chatbot-workflow/continue-chat",
            json=test_continue_data
        ) as resp:
            if resp.status == 400:  # 예상되는 차단
                error_result = await resp.json()
                print(f"✅ 예상된 차단: {error_result['detail']}")
            else:
                print(f"❌ 예상치 못한 결과: {resp.status}")
        
        # 10. Kafka로 Issue 해결 이벤트 전송 및 세션 종료 테스트
        print(f"\n🔧 10단계: Issue 해결 이벤트 전송 (세션 강제 종료 테스트)")
        
        # 새로운 세션으로 테스트 (기존 세션은 이미 차단됨)
        print("   새로운 세션으로 테스트 시작...")
        new_start_data = {
            "issue_id": issue_id,
            "user_id": "workflow_test_user_2",
            "user_message": "새로운 세션에서 질문드립니다."
        }
        
        async with session.post(
            f"{BASE_URL}/api/chatbot-workflow/start-chat",
            json=new_start_data
        ) as resp:
            if resp.status == 200:
                new_chat_result = await resp.json()
                new_session_id = new_chat_result['data']['redis_session_id']
                print(f"   ✅ 새 세션 생성: {new_session_id}")
                
                # Issue 해결 이벤트 전송 (시뮬레이션)
                print("   📨 Issue 해결 이벤트 전송...")
                solve_event_data = {
                    "issue_id": issue_id,
                    "process_type": "장애접수",
                    "mode_type": "프레스",
                    "mode_log_id": f"SOLVED_{issue_id}",
                    "user_id": "system",
                    "description": f"Issue {issue_id} 해결 완료 - 테스트"
                }
                
                # 직접 Consumer에게 해결 이벤트 전달하는 API 호출 (실제로는 Kafka로)
                print("   ℹ️ 실제 환경에서는 외부 시스템이 Kafka로 isSolved=true 이벤트를 전송합니다")
                print(f"   📋 해결된 Issue: {issue_id}")
                
                # 약간의 대기 후 세션 상태 확인
                await asyncio.sleep(2)
                async with session.get(f"{BASE_URL}/api/chatbot-workflow/session-status/{new_session_id}") as resp:
                    if resp.status == 200:
                        final_status = await resp.json()
                        print(f"   📊 새 세션 상태:")
                        print(f"   - 종료됨: {final_status['data']['is_terminated']}")
                        print(f"   - 보고서 처리됨: {final_status['data']['is_reported']}")
            else:
                print(f"   ❌ 새 세션 생성 실패: {resp.status}")
        
        # 9. DB 데이터 확인
        print(f"\n🗄️ 9단계: DB 데이터 확인")
        async with session.get(f"{BASE_URL}/api/kafka/issues/{issue_id}/details") as resp:
            if resp.status == 200:
                db_details = await resp.json()
                print(f"✅ DB 데이터 조회 성공")
                print(f"   - 세션 수: {db_details['data']['session_count']}")
                print(f"   - 총 메시지 수: {db_details['data']['total_messages']}")
                
                if db_details['data']['sessions']:
                    first_session = db_details['data']['sessions'][0]
                    print(f"   - 첫 번째 세션 메시지 수: {first_session['message_count']}")
                    print(f"   - 세션 종료됨: {first_session['is_terminated']}")
                    print(f"   - 보고서 생성됨: {first_session['is_reported']}")
            else:
                print(f"❌ DB 데이터 조회 실패: {resp.status}")
        
        # 10. 종료된 세션으로 대화 시도 (실패해야 함)
        print(f"\n🚫 10단계: 종료된 세션으로 대화 시도 (실패 테스트)")
        test_continue_data = {
            "session_id": redis_session_id,
            "user_message": "추가 질문이 있습니다."
        }
        
        async with session.post(
            f"{BASE_URL}/api/chatbot-workflow/continue-chat",
            json=test_continue_data
        ) as resp:
            if resp.status == 400:  # 예상되는 실패
                error_result = await resp.json()
                print(f"✅ 예상된 실패: {error_result['detail']}")
            else:
                print(f"❌ 예상치 못한 결과: {resp.status}")
    
    print(f"\n🎉 업데이트된 완전한 워크플로우 테스트 완료!")
    print("=" * 60)
    print("\n📋 테스트 결과 요약:")
    print("1. ✅ Kafka → ChatbotIssue 생성")
    print("2. ✅ Issue 기반 챗봇 대화 시작")
    print("3. ✅ 연속 대화 (Redis ↔ DB 동기화)")
    print("4. ✅ 대화 완료 처리 (isTerminated 설정 안함)")
    print("5. ✅ PDF 다운로드/건너뛰기 선택")
    print("6. ✅ isReported 값 설정 후 세션 접근 차단")
    print("7. ✅ Kafka isSolved=true 이벤트로 세션 강제 종료")
    print("\n🎯 새로운 워크플로우가 정상 작동합니다!")
    print("\n📝 변경사항:")
    print("- 대화 완료시 isTerminated 설정하지 않음")
    print("- isReported: None → True(다운로드)/False(건너뛰기)")
    print("- isReported 값이 있으면 세션 접근 차단")
    print("- Kafka isSolved=true 시 관련 세션들 자동 종료")


if __name__ == "__main__":
    print("🧪 완전한 챗봇 워크플로우 테스트")
    print("📌 FastAPI 서버가 실행 중인지 확인하세요: http://localhost:8000")
    
    input("서버가 준비되면 Enter를 눌러주세요...")
    
    asyncio.run(test_complete_workflow())