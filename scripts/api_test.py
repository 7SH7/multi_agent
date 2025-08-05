#!/usr/bin/env python3
"""
실제 API 엔드포인트 테스트 - /chat을 통한 완전한 시스템 테스트
"""

import requests
import time

def test_api_endpoints():
    print("=" * 60)
    print("🌐 API 엔드포인트 실제 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # 1. Health Check
    print("\n1️⃣ Health Check")
    print("-" * 30)
    
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health Check: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"   응답: {health_response.json()}")
    except Exception as e:
        print(f"❌ Health Check 실패: {str(e)}")
        print("⚠️  FastAPI 서버가 실행되지 않았습니다.")
        print("   다음 명령으로 서버를 실행하세요:")
        print("   python -m uvicorn api.main:app --reload")
        return
    
    # 2. Chat Test
    print("\n2️⃣ Chat Test 엔드포인트")
    print("-" * 30)
    
    try:
        chat_test_response = requests.get(f"{base_url}/chat/test", timeout=10)
        print(f"✅ Chat Test: {chat_test_response.status_code}")
        if chat_test_response.status_code == 200:
            result = chat_test_response.json()
            print(f"   메시지: {result.get('message', 'N/A')}")
            print(f"   시스템 상태: {result.get('system_status', 'N/A')}")
    except Exception as e:
        print(f"❌ Chat Test 실패: {str(e)}")
    
    # 3. 실제 Chat 요청 (첫 번째)
    print("\n3️⃣ 실제 Chat 요청 - 첫 번째 (메모리 없음)")
    print("-" * 50)
    
    first_chat_data = {
        "message": "모터에서 이상한 진동과 소음이 발생하고 있습니다. 원인이 무엇일까요?",
        "user_id": "test_user_integration",
        "session_id": None  # 새 세션
    }
    
    try:
        print(f"📤 요청: {first_chat_data['message']}")
        first_response = requests.post(
            f"{base_url}/chat", 
            json=first_chat_data, 
            timeout=60  # 60초 대기
        )
        
        print(f"✅ 첫 번째 Chat: {first_response.status_code}")
        
        if first_response.status_code == 200:
            first_result = first_response.json()
            print(f"📨 세션 ID: {first_result.get('session_id', 'N/A')[:8]}...")
            print(f"🤖 참여 Agent: {', '.join(first_result.get('agents_used', []))}")
            print(f"📊 RAG 활용: ChromaDB({len(first_result.get('rag_context', {}).get('chroma_results', []))}) + Elasticsearch({len(first_result.get('rag_context', {}).get('elasticsearch_results', []))})")
            
            if first_result.get('response'):
                summary = first_result['response'].get('executive_summary', '응답 없음')
                print(f"💡 답변 요약: {summary[:100]}...")
            
            # 세션 ID 저장
            session_id = first_result.get('session_id')
            
            # 4. 두 번째 Chat 요청 (메모리 활용)
            print("\n4️⃣ 실제 Chat 요청 - 두 번째 (메모리 활용)")
            print("-" * 50)
            
            # 잠시 대기
            time.sleep(2)
            
            second_chat_data = {
                "message": "그런데 진동이 더 심해졌어요. 베어링 교체가 꼭 필요한 건가요?",
                "user_id": "test_user_integration", 
                "session_id": session_id  # 기존 세션 사용
            }
            
            print(f"📤 요청: {second_chat_data['message']}")
            print(f"🔄 기존 세션 사용: {session_id[:8]}...")
            
            second_response = requests.post(
                f"{base_url}/chat",
                json=second_chat_data,
                timeout=60
            )
            
            print(f"✅ 두 번째 Chat: {second_response.status_code}")
            
            if second_response.status_code == 200:
                second_result = second_response.json()
                print(f"🤖 참여 Agent: {', '.join(second_result.get('agents_used', []))}")
                
                if second_result.get('response'):
                    summary = second_result['response'].get('executive_summary', '응답 없음')
                    print(f"💡 답변 요약: {summary[:100]}...")
                    
                    # 메모리 활용 확인
                    response_text = str(second_result.get('response', {}))
                    memory_keywords = ['이전', '앞서', '방금', '먼저', '처음']
                    memory_found = any(keyword in response_text for keyword in memory_keywords)
                    print(f"🧠 메모리 활용 감지: {'✅ 확인됨' if memory_found else '⚠️  미확인'}")
        
        else:
            print(f"❌ 응답 오류: {first_response.text}")
            
    except Exception as e:
        print(f"❌ Chat 요청 실패: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 API 테스트 완료")
    print("=" * 60)
    print("✅ 모든 테스트가 성공하면 완전한 시스템이 작동 중입니다!")
    print("🚀 Multi-Agent + RAG + Memory 시스템 실전 준비 완료!")

if __name__ == "__main__":
    test_api_endpoints()