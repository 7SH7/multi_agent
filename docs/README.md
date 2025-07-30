# 🤖 Multi-Agent 제조업 챗봇 시스템

> GPT, Gemini, Clova, Claude 4개의 AI Agent가 협력하여 제조업 문제를 해결하는 차세대 챗봇

## 🌟 주요 특징

- **🤝 Multi-Agent 협업**: 각기 다른 전문성을 가진 AI들이 토론하여 최적해 도출
- **🏭 제조업 특화**: 기계 고장, 품질 문제, 안전 관리 등 제조업 도메인 최적화  
- **⚡ 실시간 처리**: FastAPI 기반 고성능 비동기 처리
- **📊 구조화된 응답**: 즉시조치, 상세해결책, 비용추정, 안전수칙 등 체계적 정보 제공
- **🔍 RAG 검색**: ChromaDB + Elasticsearch 하이브리드 지식 검색

## 🚀 빠른 시작

### 1단계: 서버 실행
```bash
# 방법 1: 배치파일 사용 (Windows)
docs\examples\start_server.bat

# 방법 2: 직접 실행
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2단계: 웹 UI에서 테스트
1. 브라우저에서 http://localhost:8000/docs 접속
2. `POST /chat/test` 섹션에서 "Try it out" 클릭
3. 예시 데이터 입력 후 "Execute" 클릭

```json
{
  "user_message": "컨베이어 벨트가 자꾸 멈춰요. 어떻게 해결하면 좋을까요?",
  "issue_code": "CONV-BELT-001", 
  "user_id": "test_user"
}
```

### 3단계: Python 스크립트로 테스트
```bash
# 대화형 테스트
python docs/examples/simple_test.py

# 빠른 질문 테스트  
python docs/examples/quick_chat_test.py "기계에서 소음이 나요"

# 미리 정의된 시나리오 테스트
python docs/examples/quick_chat_test.py 1  # 컨베이어 벨트 문제
```

## 🏗️ 시스템 아키텍처

```
사용자 질문
    ↓
RAG 분류기 (문제 분석 & Agent 선택)
    ↓
선택된 Agent들 순차 실행:
├── 🧠 GPT Agent (종합분석 & 안전성)
├── 🔬 Gemini Agent (기술정확성 & 공학접근)  
└── 💼 Clova Agent (실무경험 & 비용효율)
    ↓
🎭 Claude 토론 진행자 (의견 종합 & 최종 구조화)
    ↓
구조화된 전문가 응답 반환
```

## 📋 API 엔드포인트

| 엔드포인트 | 설명 | 인증 |
|-----------|------|------|
| `GET /ping` | 서버 상태 확인 | 불필요 |
| `GET /health` | 시스템 헬스체크 | 불필요 |
| `POST /chat/test` | 테스트용 챗봇 (API키 불필요) | 불필요 |
| `POST /chat` | 정식 챗봇 서비스 | API키 필요 |
| `GET /session/{id}` | 세션 정보 조회 | 불필요 |

## 🎯 테스트 시나리오 예시

### 기계 고장 문제
```json
{
  "user_message": "CNC 머신에서 이상한 소음이 나고 정밀도가 떨어져요",
  "issue_code": "CNC-PRECISION-001"
}
```

### 품질 관리 문제  
```json
{
  "user_message": "제품 표면에 기포가 생기는 불량이 계속 발생합니다",
  "issue_code": "QUALITY-BUBBLE-002"
}
```

### 안전 문제
```json
{
  "user_message": "작업자가 화학물질에 노출될 위험이 있는 것 같아요", 
  "issue_code": "SAFETY-CHEM-003"
}
```

## 📊 응답 구조

```json
{
  "session_id": "sess_abc123",
  "participating_agents": ["GPT", "Gemini", "Claude"],
  "confidence_level": 0.85,
  "processing_time": 45.2,
  "executive_summary": "전문가들이 합의한 핵심 해결책",
  "immediate_actions": [
    {
      "step": 1,
      "action": "즉시 수행할 조치",
      "time": "10분",
      "priority": "high"
    }
  ],
  "detailed_solution": [
    {
      "phase": "1단계: 진단",
      "actions": ["상세 행동 계획"],
      "estimated_time": "30분"
    }
  ],
  "cost_estimation": {
    "parts": "부품 교체비 50만원",
    "labor": "인건비 20만원", 
    "total": "총 70만원"
  },
  "safety_precautions": ["안전 수칙들"]
}
```

## ⚙️ 환경 설정

### 필수 의존성
- Python 3.8+
- FastAPI, Uvicorn
- OpenAI, Google AI, Anthropic 라이브러리

### 선택적 의존성  
- Redis (세션 저장)
- Elasticsearch (고급 검색)
- ChromaDB (벡터 검색)

### API 키 설정
```bash
# .env 파일 또는 환경변수
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key  
ANTHROPIC_API_KEY=your_anthropic_key
NAVER_CLOVA_API_KEY=your_clova_key
```

## 🔧 개발자 도구

### 개별 Agent 테스트
```bash
python quick_test.py  # 모든 Agent 개별 테스트
```

### 시스템 통합 테스트
```bash  
python test_system.py  # 전체 워크플로우 테스트
python simple_test.py  # API 서버 테스트
```

### 로그 모니터링
서버 실행 시 실시간으로 다음 과정을 확인할 수 있습니다:
- RAG 분류 및 Agent 선택
- 각 Agent별 처리 시간 및 토큰 사용량
- 토론 진행자의 의견 종합 과정
- 최종 응답 구조화 결과

## 📈 성능 최적화

### 응답 시간
- 단일 Agent: 15-30초
- 다중 Agent: 45-90초  
- 복잡한 토론: 90-180초

### 확장성
- 비동기 처리로 동시 다중 요청 지원
- Agent별 독립적 확장 가능
- 외부 서비스 장애 시 Fallback 모드 지원

## 🛠️ 문제 해결

### 자주 묻는 질문

**Q: Agent가 응답하지 않아요**
A: `quick_test.py`로 개별 Agent 상태 확인 후 API 키 점검

**Q: 응답이 너무 느려요**  
A: 정상입니다! 여러 Agent가 순차 분석하므로 시간이 필요합니다.

**Q: Redis/Elasticsearch 오류가 나와요**
A: 무시하세요! 핵심 기능은 이들 없이도 정상 작동합니다.

**Q: 타임아웃이 발생해요**
A: 클라이언트 타임아웃을 최소 3분(180초)으로 설정하세요.

### 디버깅 팁
1. 서버 로그에서 각 Agent의 실행 과정 확인
2. `/health` 엔드포인트로 시스템 상태 모니터링  
3. 개별 Agent 테스트로 문제 격리

## 🤝 기여하기

1. 새로운 Agent 추가
2. 도메인 특화 지식 확장
3. 성능 최적화
4. 테스트 케이스 추가

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

---

**🎉 이제 AI 전문가 팀이 당신의 제조업 문제를 해결해드립니다!**

상세한 실행 가이드는 [`docs/QUICK_START.md`](./QUICK_START.md)를 참조하세요.