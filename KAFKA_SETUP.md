# Kafka ChatbotIssue 통합 가이드

## 📋 개요

이 시스템은 외부 시스템에서 Kafka를 통해 ChatbotIssue 이벤트를 수신하여 자동으로 데이터베이스에 저장하는 기능을 제공합니다.

## 🏗️ 아키텍처

```
[외부 시스템] → [Kafka Topic: chatbot-issue-events] → [FastAPI Consumer] → [MySQL ChatbotIssue Table]
```

## 🚀 설정 및 실행

### 1. 환경 변수 설정

`.env` 파일에 다음 설정을 추가하세요:

```env
# Kafka 설정
KAFKA_ENABLED=true
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=chatbot-issue-consumer-group
KAFKA_TOPIC_CHATBOT_ISSUES=chatbot-issue-events

# 데이터베이스 설정 (기존 설정)
DB_HOST=localhost:3306
DB_NAME=chatbot_db
DB_USERNAME=chatbot_user
DB_PASSWORD=your_password
```

### 2. 의존성 설치

```bash
pip install aiokafka==0.8.11
# 또는
pip install -r requirements.txt
```

### 3. Kafka 서버 실행

```bash
# Kafka 및 Zookeeper 실행 (Docker Compose 예시)
version: '3.8'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

### 4. FastAPI 서버 실행

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📨 이벤트 스키마

### ChatbotIssue 이벤트 형식

```json
{
  "issue": "PRESS_001_20250806_001",
  "processType": "장애접수",  // "장애접수" 또는 "정기점검"
  "modeType": "프레스",       // "프레스", "용접기", "도장설비", "차량조립설비"
  "modeLogId": "PRESS_LOG_20250806_001",
  "timestamp": "2025-08-06T10:30:00"  // 선택사항, 자동 생성됨
}
```

### 유효한 값들

- **processType**: `"장애접수"`, `"정기점검"`
- **modeType**: `"프레스"`, `"용접기"`, `"도장설비"`, `"차량조립설비"`

## 🔧 API 엔드포인트

### Kafka 관리 API

- `GET /api/kafka/status` - Kafka Consumer 상태 조회
- `POST /api/kafka/start` - Consumer 수동 시작
- `POST /api/kafka/stop` - Consumer 수동 중지
- `POST /api/kafka/restart` - Consumer 재시작

### ChatbotIssue 조회 API

- `GET /api/kafka/issues` - ChatbotIssue 목록 조회
- `GET /api/kafka/issues/{issue_id}` - 특정 ChatbotIssue 조회
- `DELETE /api/kafka/issues/{issue_id}` - ChatbotIssue 삭제

### API 사용 예시

```bash
# Consumer 상태 확인
curl -X GET "http://localhost:8000/api/kafka/status"

# ChatbotIssue 목록 조회
curl -X GET "http://localhost:8000/api/kafka/issues?limit=10&offset=0"

# 특정 ChatbotIssue 조회
curl -X GET "http://localhost:8000/api/kafka/issues/PRESS_001_20250806_001"
```

## 🧪 테스트

### 1. 테스트 이벤트 전송

```bash
python scripts/kafka_test_producer.py
```

### 2. 수동 이벤트 전송 (Python)

```python
import asyncio
import json
from aiokafka import AIOKafkaProducer

async def send_test_event():
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8')
    )
    
    await producer.start()
    
    event = {
        "issue": "TEST_001_20250806_001",
        "processType": "장애접수",
        "modeType": "프레스", 
        "modeLogId": "TEST_LOG_001"
    }
    
    await producer.send_and_wait('chatbot-issue-events', value=event)
    await producer.stop()

asyncio.run(send_test_event())
```

### 3. 결과 확인

1. **로그 확인**: FastAPI 서버 로그에서 Consumer 처리 메시지 확인
2. **API 호출**: `GET /api/kafka/issues`로 저장된 데이터 확인
3. **DB 직접 확인**: MySQL에서 `ChatbotIssue` 테이블 조회

```sql
SELECT * FROM ChatbotIssue ORDER BY issue DESC;
```

## 🔍 모니터링 및 디버깅

### 로그 확인

```bash
# FastAPI 로그에서 Kafka 관련 메시지 확인
grep -i kafka logs/app.log
grep -i "chatbot.*issue" logs/app.log
```

### 상태 확인

```bash
# Consumer 상태
curl -X GET "http://localhost:8000/api/kafka/status"

# 시스템 헬스 체크
curl -X GET "http://localhost:8000/health"
```

### 일반적인 문제 해결

1. **Kafka 연결 실패**
   - Kafka 서버가 실행 중인지 확인
   - `KAFKA_BOOTSTRAP_SERVERS` 설정 확인
   
2. **Consumer 시작 실패**
   - 데이터베이스 연결 확인
   - Topic이 존재하는지 확인
   
3. **이벤트 처리 실패**
   - 이벤트 스키마가 올바른지 확인
   - 로그에서 validation 오류 확인

## 🔧 고급 설정

### Consumer 그룹 관리

```bash
# Consumer 그룹 상태 확인
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group chatbot-issue-consumer-group --describe

# Offset 리셋
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group chatbot-issue-consumer-group --reset-offsets \
  --to-earliest --topic chatbot-issue-events --execute
```

### 성능 튜닝

환경변수로 다음 설정들을 조정할 수 있습니다:

```env
# Consumer 설정
KAFKA_MAX_POLL_RECORDS=500
KAFKA_SESSION_TIMEOUT_MS=30000
KAFKA_HEARTBEAT_INTERVAL_MS=3000

# 데이터베이스 연결 풀
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## 📚 참고 자료

- [aiokafka 문서](https://aiokafka.readthedocs.io/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async 문서](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Apache Kafka 문서](https://kafka.apache.org/documentation/)