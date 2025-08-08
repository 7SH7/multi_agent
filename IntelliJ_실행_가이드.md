# 🚀 IntelliJ에서 FastAPI 프로젝트 실행 가이드

## 1️⃣ 프로젝트 열기

1. **IntelliJ IDEA 실행**
2. **File → Open**
3. **폴더 선택**: `D:\workplace\smartfactory_fastapi`
4. **Open as Project** 클릭

## 2️⃣ Python 인터프리터 설정

1. **File → Settings (Ctrl+Alt+S)**
2. **Project → Python Interpreter**
3. **⚙️ 버튼 → Add Interpreter → Add Local Interpreter**
4. **Existing Environment** 선택
5. **Interpreter 경로**: `D:\workplace\smartfactory_fastapi\.big_proj_venv\Scripts\python.exe`
6. **OK** 클릭

## 3️⃣ 실행 구성 만들기

### 방법 1: uvicorn으로 서버 실행 (권장)

1. **Run → Edit Configurations**
2. **+ 버튼 → Python**
3. **설정값 입력:**
   ```
   Name: FastAPI Server
   Script path: D:\workplace\smartfactory_fastapi\.big_proj_venv\Scripts\uvicorn.exe
   Parameters: api.main:app --host 0.0.0.0 --port 8000 --reload
   Working directory: D:\workplace\smartfactory_fastapi
   Python interpreter: .big_proj_venv\Scripts\python.exe
   ```

### 방법 2: Python 모듈로 실행

1. **Run → Edit Configurations**
2. **+ 버튼 → Python**  
3. **설정값 입력:**
   ```
   Name: FastAPI Module
   Module name: uvicorn
   Parameters: api.main:app --host 0.0.0.0 --port 8000 --reload
   Working directory: D:\workplace\smartfactory_fastapi
   Python interpreter: .big_proj_venv\Scripts\python.exe
   ```

## 4️⃣ 환경변수 설정 (선택사항)

실행 구성에서 **Environment variables** 섹션에 추가:
```
PYTHONPATH=D:\workplace\smartfactory_fastapi
PYTHONIOENCODING=utf-8
```

## 5️⃣ 실행하기

1. **실행 구성 선택**: 상단 드롭다운에서 `FastAPI Server` 선택
2. **▶️ 실행 버튼** 클릭 또는 **Shift+F10**
3. **콘솔에서 확인**:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   INFO:     Application startup complete.
   ```

## 6️⃣ 테스트하기

1. **브라우저 열기**: http://localhost:8000/docs
2. **API 문서 확인**: FastAPI Swagger UI가 표시되면 성공!
3. **Health Check**: http://localhost:8000/health

## 🔧 문제 해결

### 문제 1: "Module not found" 에러
**해결**: Working Directory가 프로젝트 루트인지 확인

### 문제 2: 패키지 없음 에러  
**해결**: IntelliJ Terminal에서
```bash
.big_proj_venv\Scripts\activate
pip install -r requirements.txt
```

### 문제 3: Port 8000 already in use
**해결**: 다른 포트 사용
```
Parameters: api.main:app --host 0.0.0.0 --port 8001 --reload
```

## 🎯 빠른 실행 (Terminal 사용)

IntelliJ 하단 **Terminal** 탭에서:
```bash
# 가상환경 활성화
.big_proj_venv\Scripts\activate

# 서버 실행
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🚀 추천 실행 순서

1. **프로젝트 열기** → **인터프리터 설정**
2. **Terminal에서 빠른 테스트**:
   ```bash
   .big_proj_venv\Scripts\activate
   python -m uvicorn api.main:app --reload
   ```
3. **정상 작동 확인 후 실행 구성 생성**
4. **▶️ 버튼으로 편리하게 실행**

## 💡 IntelliJ 꿀팁

- **Ctrl+Shift+F10**: 현재 파일 실행
- **Shift+F10**: 마지막 실행 구성 재실행  
- **Ctrl+F2**: 실행 중인 서버 중단
- **Alt+F12**: Terminal 빠르게 열기

---

**이 순서대로 하면 IntelliJ에서 완벽하게 실행됩니다!** 🎉