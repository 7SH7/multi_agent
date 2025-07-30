@echo off
echo 🚀 Multi-Agent 챗봇 서버 시작
echo ================================

echo 📁 현재 디렉토리 확인...
cd /d "%~dp0..\.."
echo    경로: %CD%

echo.
echo 🔍 Python 환경 확인...
python --version
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았거나 PATH에 없습니다!
    pause
    exit /b 1
)

echo.
echo 📦 필요한 패키지 확인...
python -c "import fastapi, uvicorn; print('✅ FastAPI 및 Uvicorn 설치됨')" 2>nul
if errorlevel 1 (
    echo ⚠️ 필요한 패키지가 없습니다. 설치 중...
    pip install -r requirements.txt
)

echo.
echo 🌐 서버 시작 중...
echo    URL: http://localhost:8000
echo    API 문서: http://localhost:8000/docs
echo    중지하려면 Ctrl+C를 누르세요
echo.

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload