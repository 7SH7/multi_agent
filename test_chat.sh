#!/bin/bash

# 테스트 채팅 요청
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: user-key-456" \
  -d '{
    "user_message": "프레스 기계에서 이상한 소리가 나는데 어떻게 해야 하나요?",
    "issue_code": "PRESS_001", 
    "user_id": "test_user"
  }'