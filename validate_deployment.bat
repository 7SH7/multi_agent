@echo off
echo ===== SmartFactory FastAPI 배포 검증 스크립트 =====
echo.

echo 1. Docker 컨테이너 빌드 및 실행...
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo.
echo 2. 컨테이너 상태 확인 중...
timeout /t 10 /nobreak >nul
docker-compose ps

echo.
echo 3. 애플리케이션 로그 확인...
docker-compose logs app --tail=20

echo.
echo 4. API 헬스체크...
timeout /t 5 /nobreak >nul
curl -f http://localhost:8000/health || echo "헬스체크 실패"

echo.
echo 5. 전체 서비스 상태...
docker-compose ps

echo.
echo ===== 검증 완료 =====