# Cloud Kafka Integration with Spring Boot

## 🌐 클라우드 환경에서 Spring Boot ↔ FastAPI Kafka 연동

### 1. Spring Boot Producer (장애/점검 시스템)
```java
// Spring Boot - KafkaProducer
@Service
public class IssueEventProducer {
    
    @Autowired
    private KafkaTemplate<String, Object> kafkaTemplate;
    
    public void sendIssueEvent(ChatbotIssueEvent event) {
        // FastAPI와 동일한 JSON 구조
        Map<String, Object> message = Map.of(
            "issue", event.getIssue(),
            "processType", event.getProcessType(),
            "modeType", event.getModeType(), 
            "modeLogId", event.getModeLogId(),
            "description", event.getDescription(),
            "isSolved", event.getIsSolved(),
            "timestamp", Instant.now().toString()
        );
        
        kafkaTemplate.send("chatbot-issue-events", message);
        log.info("Issue event sent: {}", event.getIssue());
    }
}
```

### 2. FastAPI Consumer (현재 구현)
```python
# services/kafka_consumer.py - 이미 구현됨
async def consume_messages(self):
    async for message in self.consumer:
        issue_data = message.value  # Spring Boot에서 보낸 동일한 JSON
        await self.process_chatbot_issue(issue_data)
```

### 3. 클라우드 배포 환경 설정

#### Docker Compose (Cloud)
```yaml
services:
  # Spring Boot App
  spring-app:
    image: your-registry/smartfactory-spring:latest
    environment:
      - SPRING_KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - SPRING_KAFKA_PRODUCER_VALUE_SERIALIZER=org.springframework.kafka.support.serializer.JsonSerializer
    depends_on:
      - kafka

  # FastAPI App  
  fastapi-app:
    image: your-registry/smartfactory-fastapi:latest
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - KAFKA_CONSUMER_GROUP=chatbot-issue-consumer-group
    depends_on:
      - kafka

  # Kafka Cluster
  kafka:
    image: confluentinc/cp-kafka:7.4.0
    environment:
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
```

#### Kubernetes 배포
```yaml
# kafka-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kafka-config
data:
  KAFKA_BOOTSTRAP_SERVERS: "kafka-service:9092"
  KAFKA_TOPIC: "chatbot-issue-events"

---
# spring-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spring-producer
spec:
  template:
    spec:
      containers:
      - name: spring-app
        envFrom:
        - configMapRef:
            name: kafka-config

---
# fastapi-deployment.yaml  
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-consumer
spec:
  template:
    spec:
      containers:
      - name: fastapi-app
        envFrom:
        - configMapRef:
            name: kafka-config
```

### 4. 실제 운영 시나리오

#### 🏭 Smart Factory 플로우:
```
1. [PLC/센서] → [Spring Boot 모니터링]
     ↓
2. [Spring Boot] → [Kafka Topic: chatbot-issue-events]  
     ↓
3. [FastAPI Consumer] → [ChatBot Session 자동 생성]
     ↓ 
4. [작업자] → [ChatBot 대화] → [문제 해결]
     ↓
5. [해결 완료] → [Kafka: isSolved=true] → [세션 자동 종료]
```

### 5. 메시지 형식 (양방향 호환)

```json
{
  "issue": "PRESS_001_20250808_001",
  "processType": "장애접수",  
  "modeType": "프레스",
  "modeLogId": "PRESS_LOG_001", 
  "description": "100톤 프레스 유압 이상",
  "isSolved": false,
  "timestamp": "2025-08-08T17:05:37.123Z"
}
```

### 6. 클라우드 서비스별 설정

#### AWS MSK (Managed Kafka)
```python
# settings.py
KAFKA_BOOTSTRAP_SERVERS = "b-1.msk-cluster.kafka.us-east-1.amazonaws.com:9092"
KAFKA_SECURITY_PROTOCOL = "SASL_SSL"  
KAFKA_SASL_MECHANISM = "AWS_MSK_IAM"
```

#### Azure Event Hubs
```python
KAFKA_BOOTSTRAP_SERVERS = "your-namespace.servicebus.windows.net:9093"
KAFKA_SECURITY_PROTOCOL = "SASL_SSL"
KAFKA_SASL_MECHANISM = "PLAIN"
```

#### Google Cloud Pub/Sub (Kafka API)
```python  
KAFKA_BOOTSTRAP_SERVERS = "kafka.googleapis.com:443"
KAFKA_SECURITY_PROTOCOL = "SASL_SSL"
```

### 7. 모니터링 및 확인

```bash
# 클라우드에서 메시지 플로우 확인
kubectl logs -f deployment/spring-producer | grep "Issue event sent"
kubectl logs -f deployment/fastapi-consumer | grep "CDC 이벤트 수신"

# Kafka Topic 상태 확인  
kafka-console-consumer --bootstrap-server kafka:9092 --topic chatbot-issue-events
```

## ✅ 결론
- **호환성**: 100% 호환 (Apache Kafka 표준)
- **확장성**: 클라우드 Kafka 클러스터로 무제한 확장
- **안정성**: Consumer Group으로 메시지 중복 방지
- **실시간**: 밀리초 단위 실시간 CDC 처리

클라우드에 배포하면 Spring Boot와 FastAPI가 Kafka를 통해 완벽하게 소통합니다! 🎉