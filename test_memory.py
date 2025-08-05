#!/usr/bin/env python3
"""세션 메모리 기능 테스트 스크립트"""

import asyncio
import aiohttp

async def test_session_memory():
    """세션 메모리 연속성 테스트"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("🔍 세션 메모리 테스트 시작...")
        
        # 1. 첫 번째 대화 - 새 세션 생성
        print("\n1️⃣ 첫 번째 대화 (새 세션)")
        first_message = {
            "user_message": "간단한 테스트입니다. 안녕하세요!"
        }
        
        try:
            async with session.post(
                f"{base_url}/chat", 
                json=first_message,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    session_id = data.get('session_id')
                    conv_count = data.get('conversation_count', 0)
                    agents = data.get('participating_agents', [])
                    print(f"✅ 세션 ID: {session_id}")
                    print(f"✅ 대화 수: {conv_count}")
                    print(f"✅ 사용 Agent: {agents}")
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
        print(f"\n2️⃣ 세션 정보 확인: {session_id}")
        try:
            async with session.get(f"{base_url}/session/{session_id}") as resp:
                if resp.status == 200:
                    session_info = await resp.json()
                    print(f"✅ 세션 상태: {session_info.get('status')}")
                    print(f"✅ 대화 수: {session_info.get('conversation_count')}")
                    print(f"✅ 사용된 Agent: {session_info.get('agents_used')}")
                    print(f"✅ 총 토론 수: {session_info.get('total_debates')}")
                else:
                    print(f"❌ 세션 정보 조회 실패: {resp.status}")
        except Exception as e:
            print(f"❌ 세션 정보 오류: {e}")
        
        # 3. 두 번째 대화 - 같은 세션 사용
        print(f"\n3️⃣ 두 번째 대화 (세션 {session_id})")
        second_message = {
            "user_message": "이전 대화 기억하시나요? 추가 질문입니다.",
            "session_id": session_id
        }
        
        try:
            async with session.post(
                f"{base_url}/chat", 
                json=second_message,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    conv_count_2 = data.get('conversation_count', 0)
                    agents_2 = data.get('participating_agents', [])
                    print(f"✅ 대화 수: {conv_count_2} (증가했는가?)")
                    print(f"✅ 사용 Agent: {agents_2}")
                    
                    if conv_count_2 > conv_count:
                        print("🎉 대화 카운트 증가 확인!")
                    else:
                        print("⚠️ 대화 카운트가 증가하지 않음")
                else:
                    print(f"❌ 두 번째 요청 실패: {resp.status}")
        except asyncio.TimeoutError:
            print("❌ 두 번째 요청 타임아웃")
        except Exception as e:
            print(f"❌ 두 번째 요청 오류: {e}")
        
        # 4. 최종 세션 상태 확인
        print("\n4️⃣ 최종 세션 상태 확인")
        try:
            async with session.get(f"{base_url}/session/{session_id}") as resp:
                if resp.status == 200:
                    final_info = await resp.json()
                    print(f"✅ 최종 대화 수: {final_info.get('conversation_count')}")
                    print(f"✅ 누적 사용 Agent: {final_info.get('agents_used')}")
                    print(f"✅ 총 처리 시간: {final_info.get('total_processing_time', 0):.2f}초")
                else:
                    print(f"❌ 최종 세션 정보 조회 실패: {resp.status}")
        except Exception as e:
            print(f"❌ 최종 세션 정보 오류: {e}")

if __name__ == "__main__":
    asyncio.run(test_session_memory())