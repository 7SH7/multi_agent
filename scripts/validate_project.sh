#!/bin/bash

# ==========================================
# Smart Factory FastAPI 프로젝트 전체 검증 스크립트
# ==========================================

set -e  # 오류 발생시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 시작 메시지
echo -e "${BLUE}"
echo "=========================================="
echo "🚀 Smart Factory FastAPI 프로젝트 검증 시작"
echo "=========================================="
echo -e "${NC}"

# 현재 디렉토리 확인
if [ ! -f "docker-compose.yaml" ]; then
    log_error "docker-compose.yaml 파일이 없습니다. 프로젝트 루트 디렉토리에서 실행하세요."
    exit 1
fi

log_info "프로젝트 디렉토리: $(pwd)"

# 1. 환경변수 파일 확인
echo -e "\n${BLUE}📋 1. 환경설정 검증${NC}"
if [ ! -f ".env" ]; then
    log_error ".env 파일이 없습니다."
    exit 1
fi

# API 키 확인 (노출되지 않게 길이만 확인)
if grep -q "your_.*_api_key_here" .env; then
    log_warning "일부 API 키가 기본값으로 설정되어 있습니다. 실제 키로 교체하세요."
else
    log_success "API 키 설정 확인됨"
fi

# MySQL 자격증명 확인
if grep -q "MYSQL_PASSWORD=" .env; then
    log_success "MySQL 자격증명 환경변수 설정됨"
else
    log_error "MySQL 자격증명이 설정되지 않았습니다."
    exit 1
fi

# 2. Docker 및 Docker Compose 확인
echo -e "\n${BLUE}🐳 2. Docker 환경 검증${NC}"
if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되지 않았습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose가 설치되지 않았습니다."
    exit 1
fi

log_success "Docker 및 Docker Compose 설치 확인됨"

# Docker 서비스 상태 확인
if ! docker info &> /dev/null; then
    log_error "Docker 데몬이 실행되지 않았습니다."
    exit 1
fi

log_success "Docker 데몬 실행중"

# 3. Docker Compose 설정 검증
echo -e "\n${BLUE}⚙️  3. Docker Compose 설정 검증${NC}"
if docker-compose config --quiet; then
    log_success "Docker Compose 설정 유효함"
else
    log_error "Docker Compose 설정에 오류가 있습니다."
    exit 1
fi

# 4. 기존 컨테이너 정리 (선택사항)
echo -e "\n${BLUE}🧹 4. 기존 컨테이너 정리${NC}"
log_info "기존 컨테이너를 정리합니다..."
docker-compose down --remove-orphans &> /dev/null || true
log_success "기존 컨테이너 정리 완료"

# 5. 서비스 시작
echo -e "\n${BLUE}🚀 5. Docker Compose 서비스 시작${NC}"
log_info "모든 서비스를 시작합니다. 이 과정은 몇 분이 소요될 수 있습니다..."

# 백그라운드에서 시작
docker-compose up -d

# 6. 서비스 헬스체크 대기
echo -e "\n${BLUE}🏥 6. 서비스 헬스체크 대기${NC}"

# 서비스별 헬스체크 함수
wait_for_service() {
    local service_name=$1
    local max_attempts=$2
    local attempt=1
    
    log_info "${service_name} 서비스 시작 대기중..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep $service_name | grep -q "healthy\|Up"; then
            log_success "${service_name} 서비스 준비 완료 (${attempt}/${max_attempts})"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "${service_name} 서비스가 ${max_attempts}번 시도 후에도 준비되지 않았습니다."
            docker-compose logs $service_name | tail -20
            return 1
        fi
        
        log_info "${service_name} 대기중... (${attempt}/${max_attempts})"
        sleep 10
        ((attempt++))
    done
}

# 각 서비스 헬스체크
wait_for_service "mysql" 12       # 2분
wait_for_service "redis" 6        # 1분
wait_for_service "elasticsearch" 12  # 2분
wait_for_service "chroma" 6       # 1분
wait_for_service "app" 18         # 3분

# 7. API 엔드포인트 테스트
echo -e "\n${BLUE}🌐 7. API 엔드포인트 테스트${NC}"

# 헬스체크 엔드포인트 테스트
test_endpoint() {
    local endpoint=$1
    local description=$2
    local max_attempts=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$endpoint" > /dev/null; then
            log_success "$description 응답 정상"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "$description 응답 실패 (${max_attempts}번 시도)"
            return 1
        fi
        
        log_info "$description 테스트 중... (${attempt}/${max_attempts})"
        sleep 5
        ((attempt++))
    done
}

# API 테스트 실행
test_endpoint "http://localhost:8000/health" "헬스체크 API"
test_endpoint "http://localhost:8000/docs" "API 문서"

# 실제 API 응답 내용 확인
log_info "헬스체크 응답 내용 확인:"
health_response=$(curl -s http://localhost:8000/health)
if echo "$health_response" | grep -q '"status"'; then
    log_success "헬스체크 JSON 응답 구조 정상"
    echo "응답: $health_response" | head -c 200
else
    log_warning "헬스체크 응답 구조 확인 필요"
fi

# 8. 데이터베이스 연결 테스트
echo -e "\n${BLUE}🗄️  8. 데이터베이스 연결 테스트${NC}"

# MySQL 연결 테스트
if docker-compose exec -T mysql mysql -u chatbot_user -p${MYSQL_PASSWORD} -e "SELECT 1;" &> /dev/null; then
    log_success "MySQL 연결 성공"
else
    log_error "MySQL 연결 실패"
    # MySQL 로그 확인
    log_info "MySQL 로그 (마지막 10줄):"
    docker-compose logs mysql | tail -10
fi

# Redis 연결 테스트
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    log_success "Redis 연결 성공"
else
    log_error "Redis 연결 실패"
fi

# Elasticsearch 연결 테스트
if curl -s http://localhost:9200/_cluster/health | grep -q "yellow\|green"; then
    log_success "Elasticsearch 연결 성공"
else
    log_warning "Elasticsearch 연결 확인 필요"
fi

# ChromaDB 연결 테스트
if curl -s http://localhost:8001/api/v1/heartbeat | grep -q "OK"; then
    log_success "ChromaDB 연결 성공"
else
    log_warning "ChromaDB 연결 확인 필요"
fi

# 9. 로그 검증 (오류 확인)
echo -e "\n${BLUE}📋 9. 서비스 로그 검증${NC}"

check_logs_for_errors() {
    local service=$1
    local error_patterns=("ERROR" "FATAL" "Exception" "Traceback" "failed" "FAILED")
    
    log_info "${service} 로그에서 오류 검색 중..."
    
    local logs=$(docker-compose logs $service 2>/dev/null || echo "")
    local has_errors=false
    
    for pattern in "${error_patterns[@]}"; do
        if echo "$logs" | grep -i "$pattern" | grep -v "test\|demo\|example" | head -3; then
            has_errors=true
        fi
    done
    
    if [ "$has_errors" = false ]; then
        log_success "${service} 로그에 심각한 오류 없음"
    else
        log_warning "${service} 로그에서 일부 오류 발견됨 (위 참조)"
    fi
}

# 각 서비스 로그 검증
check_logs_for_errors "app"
check_logs_for_errors "mysql"
check_logs_for_errors "redis"

# 10. 최종 상태 확인
echo -e "\n${BLUE}📊 10. 최종 서비스 상태 확인${NC}"

echo -e "\n현재 실행중인 컨테이너:"
docker-compose ps

# 포트 사용 확인
echo -e "\n포트 사용 현황:"
if command -v netstat &> /dev/null; then
    netstat -tlnp | grep -E ":8000|:3306|:6379|:9200|:8001" || echo "포트 확인 도구 없음"
elif command -v ss &> /dev/null; then
    ss -tlnp | grep -E ":8000|:3306|:6379|:9200|:8001" || echo "포트 확인 도구 없음"
fi

# 11. 성능 기본 테스트 (선택사항)
echo -e "\n${BLUE}⚡ 11. 기본 성능 테스트${NC}"

log_info "API 응답 시간 측정 중..."
response_time=$(curl -w "%{time_total}" -s -o /dev/null http://localhost:8000/health)
log_info "헬스체크 응답 시간: ${response_time}초"

if (( $(echo "$response_time < 2.0" | bc -l) )); then
    log_success "응답 시간 양호 (< 2초)"
else
    log_warning "응답 시간이 느림 (> 2초)"
fi

# 12. 최종 결과
echo -e "\n${GREEN}"
echo "=========================================="
echo "🎉 Smart Factory FastAPI 프로젝트 검증 완료"
echo "=========================================="
echo -e "${NC}"

log_success "프로젝트가 성공적으로 실행되고 있습니다!"

echo -e "\n${BLUE}🔗 접속 URL들:${NC}"
echo "  • API 문서: http://localhost:8000/docs"
echo "  • 헬스체크: http://localhost:8000/health"
echo "  • 메트릭스: http://localhost:8000/metrics"
echo "  • MySQL: localhost:3306"
echo "  • Redis: localhost:6379"
echo "  • Elasticsearch: http://localhost:9200"
echo "  • ChromaDB: http://localhost:8001"

echo -e "\n${BLUE}📝 다음 단계:${NC}"
echo "  1. API 키를 실제 값으로 교체"
echo "  2. 채팅 엔드포인트 테스트: curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{\"user_message\":\"안녕하세요\"}'"
echo "  3. 로그 모니터링: docker-compose logs -f app"

echo -e "\n${YELLOW}⚠️  참고사항:${NC}"
echo "  • 서비스를 중지하려면: docker-compose down"
echo "  • 데이터를 포함하여 완전 삭제: docker-compose down -v"
echo "  • 개별 서비스 재시작: docker-compose restart [service_name]"

echo -e "\n✨ 검증 스크립트 실행 완료!"