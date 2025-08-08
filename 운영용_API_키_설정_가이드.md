# 🔑 운영용 API 키 설정 가이드

## 현재 상황
- `/chat/test` → API 키 불필요 (테스트용)
- `/chat` → API 키 필요 (운영용) ← 이걸 설정해야 함

## 🛠️ 설정 방법

### 1단계: 환경변수 파일 생성

프로젝트 루트에 `.env` 파일 생성:
```bash
# D:\workplace\smartfactory_fastapi\.env

# 운영용 API 키들
ADMIN_API_KEY=admin-super-secret-key-2024
USER_API_KEY=user-access-key-2024

# 개발 모드 (false로 하면 API 키 필수)
DEBUG=false
```

### 2단계: IntelliJ 환경변수 설정

**Run → Edit Configurations → Environment variables에 추가:**
```
ADMIN_API_KEY=admin-super-secret-key-2024
USER_API_KEY=user-access-key-2024
DEBUG=false
```

### 3단계: 사용 방법

#### 방법 1: X-API-Key 헤더 (추천)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin-super-secret-key-2024" \
  -d '{
    "user_message": "프레스 기계 소음 문제",
    "user_id": "engineer01", 
    "issue_code": "PRESS_NOISE"
  }'
```

#### 방법 2: Authorization Bearer
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin-super-secret-key-2024" \
  -d '{
    "user_message": "프레스 기계 소음 문제",
    "user_id": "engineer01",
    "issue_code": "PRESS_NOISE" 
  }'
```

#### 방법 3: JavaScript/Fetch
```javascript
fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'admin-super-secret-key-2024'
  },
  body: JSON.stringify({
    user_message: '프레스 기계 소음 문제',
    user_id: 'engineer01',
    issue_code: 'PRESS_NOISE'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## 🔐 API 키 종류

### ADMIN_API_KEY
- 권한: 모든 기능 사용 가능
- 사용량: 시간당 1000회 요청
- 용도: 관리자, 시스템 관리

### USER_API_KEY  
- 권한: 일반 챗봇 기능
- 사용량: 시간당 100회 요청
- 용도: 일반 사용자, 클라이언트 앱

## 🧪 테스트 스크립트 만들기