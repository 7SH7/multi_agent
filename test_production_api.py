#!/usr/bin/env python3
"""운영용 /chat API 테스트 스크립트"""

import requests
import json
import os
from datetime import datetime

def test_production_chat_api():
    """운영용 /chat API 테스트"""
    
    base_url = "http://localhost:8000"
    
    # API 키 설정
    api_keys = {
        "admin": "admin-super-secret-key-2024",
        "user": "user-access-key-2024"
    }
    
    # 테스트 데이터
    test_requests = [
        {
            "user_message": "100톤 프레스 기계에서 유압 소음이 발생합니다. 어떻게 해결하면 될까요?",
            "user_id": "engineer_kim",
            "issue_code": "PRESS_HYDRAULIC_NOISE"
        },
        {
            "user_message": "컨베이어 벨트가 자꾸 멈춰요. 긴급 상황입니다!",
            "user_id": "operator_lee", 
            "issue_code": "CONVEYOR_STOP"
        }
    ]
    
    print("🔑 운영용 /chat API 테스트 시작")
    print("=" * 60)
    
    for key_type, api_key in api_keys.items():
        print(f"\n🧪 {key_type.upper()} API 키 테스트")
        print(f"API Key: {api_key}")
        
        for i, test_data in enumerate(test_requests, 1):
            print(f"\n📝 테스트 {i}: {test_data['issue_code']}")
            
            # 헤더 설정 - 두 가지 방법 테스트
            headers_options = [
                {
                    "Content-Type": "application/json",
                    "X-API-Key": api_key
                },
                {
                    "Content-Type": "application/json", 
                    "Authorization": f"Bearer {api_key}"
                }
            ]
            
            for j, headers in enumerate(headers_options, 1):
                method = "X-API-Key" if "X-API-Key" in headers else "Authorization Bearer"
                print(f"   방법 {j} ({method}):", end=" ")
                
                try:
                    response = requests.post(
                        f"{base_url}/chat",
                        headers=headers,
                        json=test_data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        print("✅ 성공")
                        data = response.json()
                        print(f"     세션 ID: {data.get('session_id', 'N/A')}")
                        print(f"     처리 시간: {data.get('processing_time', 0):.1f}초")
                        print(f"     응답 길이: {len(data.get('executive_summary', ''))}")
                    elif response.status_code == 401:
                        print("❌ 인증 실패")
                        print(f"     오류: {response.json().get('detail', 'Unknown')}")
                    elif response.status_code == 429:
                        print("⚠️ 사용량 제한")
                        print(f"     오류: {response.json().get('detail', 'Rate limit')}")
                    else:
                        print(f"❌ 실패 (HTTP {response.status_code})")
                        print(f"     오류: {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    print("❌ 연결 실패 - 서버가 실행 중인지 확인하세요")
                except requests.exceptions.Timeout:
                    print("⏰ 타임아웃 - 응답이 30초를 초과했습니다")
                except Exception as e:
                    print(f"❌ 오류: {e}")
                    
        print("-" * 40)
    
    # 잘못된 API 키 테스트
    print(f"\n🚫 잘못된 API 키 테스트")
    try:
        response = requests.post(
            f"{base_url}/chat",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "invalid-key-123"
            },
            json=test_requests[0],
            timeout=10
        )
        print(f"HTTP {response.status_code}: {response.json().get('detail', 'No detail')}")
    except Exception as e:
        print(f"오류: {e}")
    
    # API 키 없이 테스트
    print(f"\n❌ API 키 없이 테스트")
    try:
        response = requests.post(
            f"{base_url}/chat",
            headers={"Content-Type": "application/json"},
            json=test_requests[0],
            timeout=10
        )
        print(f"HTTP {response.status_code}: {response.json().get('detail', 'No detail')}")
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    print("🚀 서버가 실행 중인지 확인하세요:")
    print("   python -m uvicorn api.main:app --reload")
    print()
    
    input("서버가 준비되면 Enter를 누르세요...")
    
    test_production_chat_api()
    
    print(f"\n🎉 테스트 완료!")
    print(f"📚 참고: /chat/test는 API 키 없이도 동작합니다")