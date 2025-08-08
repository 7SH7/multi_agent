# ==========================================
# Smart Factory FastAPI Dockerfile
# ==========================================

# Multi-stage build for optimized image size
FROM python:3.10-slim as builder

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
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# ==========================================
# 최종 런타임 이미지
# ==========================================
FROM python:3.10-slim

# 시스템 패키지 설치 (런타임 필요 + 한글 폰트)
RUN apt-get update && apt-get install -y \
    libhdf5-103 \
    libopenblas0 \
    curl \
    fonts-nanum \
    fonts-nanum-coding \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 보안을 위한 비-root 사용자 생성
RUN groupadd -r chatbot && useradd -r -g chatbot chatbot

# 작업 디렉토리 설정
WORKDIR /app

# 빌더 스테이지에서 설치된 Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사 (소유자 변경)
COPY --chown=chatbot:chatbot . .

# 필요한 디렉토리 생성 및 권한 설정
RUN mkdir -p logs data/embeddings data/knowledge_base backups && \
    chown -R chatbot:chatbot /app && \
    chmod -R 755 /app

# Python 환경 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 기본 환경변수 설정
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV CHROMA_HOST=chroma
ENV CHROMA_PORT=8000
ENV ELASTICSEARCH_HOST=elasticsearch
ENV ELASTICSEARCH_PORT=9200
ENV LOG_LEVEL=INFO
ENV DEBUG=false

# 포트 노출
EXPOSE 8000

# 비-root 사용자로 전환
USER chatbot

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 시작 명령
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# 메타데이터 라벨
LABEL maintainer="Smart Factory Team"
LABEL version="1.0.0"
LABEL description="Multi-Agent Smart Factory Equipment Troubleshooting Chatbot"