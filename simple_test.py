#!/usr/bin/env python3
"""간단한 API 테스트"""

import requests
import json
import time

def test_server_startup():
    """서버 시작 테스트"""
    print("🚀 서버 시작 테스트...")
    
    # 서버가 시작될 때까지 대기
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:8000/ping", timeout=5)
            if response.status_code == 200:
                print("✅ 서버 응답 확인!")
                return True
        except requests.exceptions.RequestException:
            print(f"서버 시작 대기 중... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
    
    print("❌ 서버가 응답하지 않습니다. 서버를 먼저 시작해주세요.")
    return False

def test_ping_endpoint():
    """단순 ping 테스트"""
    print("📡 ping 엔드포인트 테스트...")
    
    try:
        response = requests.get("http://localhost:8000/ping")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ping 성공: {data.get('status')}")
            return True
    except Exception as e:
        print(f"❌ ping 실패: {str(e)}")
    
    return False

def test_health_endpoint():
    """헬스체크 테스트"""
    print("🏥 헬스체크 엔드포인트 테스트...")
    
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"응답 상태코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 헬스체크 성공: {data.get('status')}")
            print(f"📊 업타임: {data.get('uptime_seconds', 0):.1f}초")
            return True
        else:
            print(f"⚠️  헬스체크 응답 이상: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 헬스체크 실패: {str(e)}")
    
    return False

def test_chat_endpoint():
    """채팅 테스트 엔드포인트 테스트"""
    print("💬 채팅 테스트 엔드포인트 테스트...")
    
    test_message = {
        "user_message": "서버가 정상적으로 작동하는지 테스트합니다.",
        "user_id": "test_user_001"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/chat/test",
            json=test_message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"응답 상태코드: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 채팅 테스트 성공!")
            
            # 응답 구조 확인
            if 'session_id' in data:
                print(f"📝 세션 ID: {data['session_id']}")
            if 'processing_time' in data:
                print(f"⏱️  처리 시간: {data['processing_time']:.2f}초")
            
            return True
        else:
            print(f"❌ 채팅 테스트 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ 채팅 테스트 타임아웃 (외부 서비스 연결 대기 중일 수 있음)")
        return False
    except Exception as e:
        print(f"❌ 채팅 테스트 오류: {str(e)}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 Multi-Agent 챗봇 API 테스트")
    print("=" * 50)
    
    # 서버 시작 확인
    if not test_server_startup():
        print("\n❌ 서버가 실행되지 않았습니다.")
        print("다음 명령으로 서버를 시작해주세요:")
        print("python -m api.main")
        return
    
    print()
    
    # 기본 엔드포인트 테스트
    tests = [
        ("ping", test_ping_endpoint),
        ("헬스체크", test_health_endpoint),
        ("채팅 테스트", test_chat_endpoint)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print()
        success = test_func()
        if success:
            passed += 1
        print("-" * 30)
    
    print()
    print("📊 테스트 결과")
    print(f"성공: {passed}/{total}")
    
    if passed == total:
        print("🎉 모든 테스트 통과!")
        print("💡 API 서버가 정상적으로 작동하고 있습니다.")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        print("💡 외부 서비스(Redis, Elasticsearch) 연결 문제일 수 있습니다.")

if __name__ == "__main__":
    main()