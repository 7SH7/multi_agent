@echo off
echo ====================================================
echo Smart Factory Docker Services 시작 스크립트
echo ====================================================

echo.
echo 🔍 Docker 상태 확인 중...
docker --version
if %errorlevel% neq 0 (
    echo ❌ Docker가 설치되지 않았거나 실행되지 않았습니다.
    echo    Docker Desktop을 설치하고 실행해주세요.
    pause
    exit /b 1
)

echo.
echo 🚀 Docker 서비스 시작 중...
echo    - Redis (세션 관리)
echo    - ChromaDB (벡터 데이터베이스)  
echo    - Elasticsearch (검색 엔진)

docker-compose up -d redis chroma elasticsearch

if %errorlevel% neq 0 (
    echo.
    echo ❌ Docker 서비스 시작 실패
    echo    Docker Desktop이 실행 중인지 확인해주세요.
    pause
    exit /b 1
)

echo.
echo ⏳ 서비스 초기화 대기 중... (30초)
timeout /t 30 /nobreak

echo.
echo 🔍 서비스 상태 확인 중...
docker-compose ps

echo.
echo 🧪 서비스 연결 테스트 실행...
python scripts/test_docker_services.py

echo.
echo ✅ 스크립트 완료!
echo    서비스가 정상적으로 실행되면 Multi-Agent 시스템을 사용할 수 있습니다.
echo.
pause