#!/usr/bin/env python3
"""개선된 세션 메모리 기능 테스트"""

import asyncio
import aiohttp

async def test_improved_memory():
    """개선된 conversation_count와 bot_response 저장 테스트"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 개선된 메모리 기능 테스트 시작...")
        
        # 1. 첫 번째 대화
        print("\n1️⃣ 첫 번째 대화 (새 세션)")
        first_message = {
            "user_message": "간단한 질문입니다. 모터 오일은 언제 교체하나요?"
        }
        
        try:
            async with session.post(
                f"{base_url}/chat", 
                json=first_message,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    session_id = data.get('session_id')
                    conv_count_1 = data.get('conversation_count', 0)
                    response_type_1 = data.get('response_type')
                    exec_summary_1 = data.get('executive_summary', '')[:50] + "..."
                    
                    print(f"✅ 세션 ID: {session_id}")
                    print(f"✅ 대화 수: {conv_count_1} (첫 대화는 1이어야 함)")
                    print(f"✅ 응답 타입: {response_type_1}")
                    print(f"✅ 봇 응답 미리보기: {exec_summary_1}")
                    
                    if conv_count_1 == 1:
                        print("🎉 첫 번째 대화 카운트 정상!")
                    else:
                        print(f"❌ 첫 번째 대화 카운트 오류: {conv_count_1} (1 예상)")
                        
                else:
                    print(f"❌ 첫 번째 요청 실패: {resp.status}")
                    return
        except asyncio.TimeoutError:
            print("❌ 첫 번째 요청 타임아웃")
            return
        except Exception as e:
            print(f"❌ 첫 번째 요청 오류: {e}")
            return
        
        # 2. 세션 정보 확인
        print("\n2️⃣ 세션 정보 확인")
        try:
            async with session.get(f"{base_url}/session/{session_id}") as resp:
                if resp.status == 200:
                    session_info = await resp.json()
                    stored_count = session_info.get('conversation_count')
                    print(f"✅ 저장된 대화 수: {stored_count}")
                    
                    if stored_count == 1:
                        print("🎉 세션에 대화 카운트 정상 저장됨!")
                    else:
                        print(f"❌ 세션 대화 카운트 오류: {stored_count} (1 예상)")
                else:
                    print(f"❌ 세션 정보 조회 실패: {resp.status}")
        except Exception as e:
            print(f"❌ 세션 정보 오류: {e}")
        
        # 3. 두 번째 대화
        print("\n3️⃣ 두 번째 대화 (같은 세션)")
        second_message = {
            "user_message": "이전에 물어본 모터 오일 말고, 기어 오일은 어떤가요?",
            "session_id": session_id
        }
        
        try:
            async with session.post(
                f"{base_url}/chat", 
                json=second_message,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    conv_count_2 = data.get('conversation_count', 0)
                    response_type_2 = data.get('response_type')
                    exec_summary_2 = data.get('executive_summary', '')[:50] + "..."
                    
                    print(f"✅ 대화 수: {conv_count_2} (2여야 함)")  
                    print(f"✅ 응답 타입: {response_type_2}")
                    print(f"✅ 봇 응답 미리보기: {exec_summary_2}")
                    
                    if conv_count_2 == 2:
                        print("🎉 두 번째 대화 카운트 증가 정상!")
                    else:
                        print(f"❌ 두 번째 대화 카운트 오류: {conv_count_2} (2 예상)")
                        
                    if response_type_2 == 'follow_up':
                        print("🎉 후속 대화 타입 정상!")
                    else:
                        print(f"⚠️ 응답 타입: {response_type_2} (follow_up 예상)")
                        
                else:
                    print(f"❌ 두 번째 요청 실패: {resp.status}")
        except asyncio.TimeoutError:
            print("❌ 두 번째 요청 타임아웃")
        except Exception as e:
            print(f"❌ 두 번째 요청 오류: {e}")
        
        # 4. 최종 세션 상태 확인 
        print("\n4️⃣ 최종 세션 상태 및 대화 기록 확인")
        try:
            async with session.get(f"{base_url}/session/{session_id}") as resp:
                if resp.status == 200:
                    final_info = await resp.json()
                    final_count = final_info.get('conversation_count')
                    print(f"✅ 최종 대화 수: {final_count}")
                    
                    if final_count == 2:
                        print("🎉 최종 대화 카운트 정상!")
                    else:
                        print(f"❌ 최종 대화 카운트 오류: {final_count} (2 예상)")
                else:
                    print(f"❌ 최종 세션 정보 조회 실패: {resp.status}")
        except Exception as e:
            print(f"❌ 최종 세션 정보 오류: {e}")

        print("\n🔍 테스트 완료!")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_improved_memory())