# 🚀 Multi-Agent 챗봇 빠른 시작 가이드

## 📋 개요
이 시스템은 GPT, Gemini, Clova, Claude 4개의 AI Agent가 협력하여 제조업 문제를 해결하는 Multi-Agent 챗봇입니다.

## ⚡ 빠른 실행

### 1. 서버 시작
```bash
# 프로젝트 디렉토리로 이동
cd smartfactory_fastapi

# 서버 실행
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 서버 상태 확인
브라우저에서 다음 URL들을 확인해보세요:

- **API 문서**: http://localhost:8000/docs
- **서버 상태**: http://localhost:8000/ping
- **헬스체크**: http://localhost:8000/health

## 🤖 Multi-Agent 챗봇 테스트

### 방법 1: 웹 브라우저 (Swagger UI)
1. http://localhost:8000/docs 접속
2. `POST /chat/test` 섹션 클릭
3. "Try it out" 버튼 클릭
4. 다음 예시 데이터 입력:

```json
{
  "user_message": "컨베이어 벨트가 자꾸 멈춰요. 어떻게 해결하면 좋을까요?",
  "issue_code": "CONV-BELT-001",
  "user_id": "test_user"
}
```

5. "Execute" 버튼 클릭
6. 2-3분 후 전문가들의 종합 분석 결과 확인!

### 방법 2: curl 명령어
```bash
curl -X POST "http://localhost:8000/chat/test" \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "도어에 스크래치가 생겼는데 어떻게 해결하면 좋을까요?",
    "issue_code": "DOOR-SCRATCH-001",
    "user_id": "curl_user"
  }'
```

### 방법 3: Python 스크립트
```python
import requests
import json

# 테스트 데이터
test_data = {
    "user_message": "용접 부위에서 균열이 발견되었습니다. 긴급 조치가 필요해요!",
    "issue_code": "WELD-CRACK-001",
    "user_id": "python_user"
}

# API 호출
response = requests.post(
    "http://localhost:8000/chat/test",
    json=test_data,
    headers={"Content-Type": "application/json"},
    timeout=180  # 3분 타임아웃
)

# 결과 출력
if response.status_code == 200:
    result = response.json()
    print("🎉 성공!")
    print(f"참여 전문가: {result['participating_agents']}")
    print(f"처리 시간: {result['processing_time']:.2f}초")
    print(f"신뢰도: {result['confidence_level']:.2f}")
    print(f"\n핵심 해결책:\n{result['executive_summary']}")
else:
    print(f"❌ 오류: {response.text}")
```

## 🧪 다양한 테스트 시나리오

### 1. 기계 고장 문제
```json
{
  "user_message": "CNC 머신에서 이상한 소음이 나고 정밀도가 떨어져요",
  "issue_code": "CNC-PRECISION-001",
  "user_id": "operator_kim"
}
```

### 2. 품질 관리 문제
```json
{
  "user_message": "제품 표면에 기포가 생기는 불량이 계속 발생합니다",
  "issue_code": "QUALITY-BUBBLE-002",
  "user_id": "qc_lee"
}
```

### 3. 안전 문제
```json
{
  "user_message": "작업자가 화학물질에 노출될 위험이 있는 것 같아요",
  "issue_code": "SAFETY-CHEM-003",
  "user_id": "safety_park"
}
```

### 4. 유지보수 문제
```json
{
  "user_message": "펌프 효율이 갑자기 떨어졌고 진동이 심해졌어요",
  "issue_code": "PUMP-MAINT-004",
  "user_id": "maint_choi"
}
```

## 📊 응답 구조 이해하기

Multi-Agent 시스템의 응답은 다음과 같이 구성됩니다:

```json
{
  "session_id": "sess_abc123",
  "conversation_count": 1,
  "response_type": "test",
  "executive_summary": "전문가들이 합의한 핵심 해결책",
  "immediate_actions": [
    {
      "step": 1,
      "action": "즉시 수행해야 할 조치",
      "time": "소요 시간",
      "priority": "high/medium/low"
    }
  ],
  "detailed_solution": [
    {
      "phase": "1단계: 진단",
      "actions": ["상세 행동 계획"],
      "estimated_time": "예상 소요 시간"
    }
  ],
  "cost_estimation": {
    "parts": "부품 비용",
    "labor": "인건비",
    "total": "총 예상 비용"
  },
  "safety_precautions": ["안전 수칙들"],
  "participating_agents": ["GPT", "Gemini"],
  "confidence_level": 0.85,
  "processing_time": 45.23,
  "timestamp": "2025-07-30T13:45:00"
}
```

## 🔍 처리 과정 모니터링

### 실시간 로그 확인
서버 실행 터미널에서 다음 과정을 실시간으로 볼 수 있습니다:

```
1. 📝 RAG 분류기: 문제 분석 및 Agent 선택
2. 🤖 GPT Agent: 종합 분석 (안전성 중심)
3. 🔬 Gemini Agent: 기술적 분석 (공학적 접근)
4. 💬 Claude 토론 진행자: 의견 종합 및 최종 구조화
```

### 예상 처리 시간
- **단일 Agent**: 15-30초
- **다중 Agent**: 45-90초 (Agent 수에 따라)
- **복잡한 토론**: 90-180초

## ⚠️ 주의사항

### 1. 타임아웃 설정
- 웹 브라우저: 자동으로 기다림
- curl/Python: 최소 3분(180초) 타임아웃 설정 필요

### 2. API 키 확인
시스템이 다음 API 키들을 사용합니다:
- OpenAI (GPT)
- Google (Gemini) 
- Naver (Clova)
- Anthropic (Claude)

키가 없어도 일부 Agent는 fallback 모드로 작동합니다.

### 3. 외부 서비스 의존성
- **Redis**: 세션 저장 (없어도 메모리에서 임시 처리)
- **Elasticsearch**: RAG 검색 (없어도 Agent 지식으로 처리)

## 🎯 성공 확인 방법

### ✅ 정상 작동 신호
- HTTP 200 응답
- `participating_agents` 필드에 Agent 이름들
- `executive_summary`에 의미있는 분석 결과
- `processing_time` > 10초 (Agent들이 실제 작업한 증거)

### ❌ 문제 발생 신호
- HTTP 500 응답
- 빈 `participating_agents` 배열
- 타임아웃 오류 (3분 초과)

## 🚀 다음 단계

1. **정식 API 사용**: `/chat` 엔드포인트 (API 키 필요)
2. **세션 관리**: 연속 대화를 위한 세션 ID 활용
3. **커스텀 Agent**: 특정 도메인 전문 Agent 추가
4. **웹 UI**: React/Vue.js 프론트엔드 개발

---

## 💡 문제 해결

### Q: Agent가 응답하지 않아요
A: API 키 확인 또는 `quick_test.py` 실행해서 개별 Agent 상태 확인

### Q: 응답이 너무 느려요
A: 정상입니다! 여러 Agent가 순차적으로 분석하므로 시간이 걸립니다.

### Q: Redis/Elasticsearch 오류가 나와요
A: 무시하세요! 핵심 기능은 이들 없이도 정상 작동합니다.

---

**🎉 이제 AI 전문가 팀이 당신의 제조업 문제를 해결해드립니다!**