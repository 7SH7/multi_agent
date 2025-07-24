version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - elasticsearch
    env_file:
      - .env

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  elasticsearch:
    image: elasticsearch:8.11.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"


----

# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

# 시스템 패키지 업데이트 및 빌드 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    libhdf5-dev \
    libopenblas-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 빌드를 위한 환경 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 최종 이미지 생성
FROM python:3.11-slim

# 시스템 패키지 설치 (런타임 필요)
RUN apt-get update && apt-get install -y \
    libhdf5-103 \
    libopenblas0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 사용자 생성 (보안을 위해 root 사용자 방지)
RUN groupadd -r chatbot && useradd -r -g chatbot chatbot

# 작업 디렉토리 설정
WORKDIR /app

# 빌더 스테이지에서 설치된 Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY --chown=chatbot:chatbot . .

# 필요한 디렉토리 생성 및 권한 설정
RUN mkdir -p logs data/embeddings data/knowledge_base && \
    chown -R chatbot:chatbot /app

# Python 환경 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 포트 노출
EXPOSE 8000

# 사용자 변경
USER chatbot

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 시작
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# 개발환경용 시작 명령어 (docker-compose에서 오버라이드 가능)
# CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 라벨 추가 (이미지 메타데이터)
LABEL maintainer="Multi-Agent Chatbot Team"
LABEL version="1.0.0"
LABEL description="Multi-Agent Manufacturing Equipment Troubleshooting Chatbot"

# 환경변수 기본값 설정
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV CHROMA_HOST=chroma
ENV CHROMA_PORT=8000
ENV ELASTICSEARCH_HOST=elasticsearch
ENV ELASTICSEARCH_PORT=9200
ENV LOG_LEVEL=INFO
ENV DEBUG=false