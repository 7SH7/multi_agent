"""Configuration settings for Multi-Agent chatbot system."""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # API Keys
    OPENAI_API_KEY: str = ""
    GOOGLE_AI_API_KEY: str = ""
    NAVER_CLIENT_ID: str = ""
    NAVER_CLIENT_SECRET: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Database Configuration
    DATABASE_URL: str = "mysql://chatbot_user:chatbot_password@localhost:3306/chatbot_db"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # ChromaDB Configuration
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIRECTORY: str = "./data/embeddings/chromadb"

    # Elasticsearch Configuration
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USERNAME: str = ""
    ELASTICSEARCH_PASSWORD: str = ""

    # Application Configuration
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SESSION_TIMEOUT_HOURS: int = 24
    MAX_CONVERSATION_COUNT: int = 50

    # Agent Configuration
    CONFIDENCE_THRESHOLD: float = 0.75
    MAX_AGENTS_PER_SESSION: int = 3
    ENABLE_DEBATE: bool = True

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()

# Database URL
DATABASE_URL = settings.DATABASE_URL

# Redis configuration
REDIS_CONFIG = {
    "host": settings.REDIS_HOST,
    "port": settings.REDIS_PORT,
    "db": settings.REDIS_DB,
    "password": settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
    "decode_responses": True
}

# LLM configurations
LLM_CONFIGS = {
    "openai": {
        "api_key": settings.OPENAI_API_KEY,
        "model": "gpt-4o-mini",
        "max_tokens": 2000,
        "temperature": 0.2
    },
    "google": {
        "api_key": settings.GOOGLE_AI_API_KEY,
        "model": "gemini-1.5-flash",
        "max_tokens": 2000,
        "temperature": 0.2
    },
    "naver": {
        "client_id": settings.NAVER_CLIENT_ID,
        "client_secret": settings.NAVER_CLIENT_SECRET,
        "model": "HCX-003",
        "max_tokens": 2000,
        "temperature": 0.2
    },
    "anthropic": {
        "api_key": settings.ANTHROPIC_API_KEY,
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2000,
        "temperature": 0.2
    }
}

# ChromaDB configuration
CHROMADB_CONFIG = {
    "host": settings.CHROMA_HOST,
    "port": settings.CHROMA_PORT,
    "persist_directory": settings.CHROMA_PERSIST_DIRECTORY
}

# Elasticsearch configuration
ELASTICSEARCH_CONFIG = {
    "host": settings.ELASTICSEARCH_HOST,
    "port": settings.ELASTICSEARCH_PORT,
    "username": settings.ELASTICSEARCH_USERNAME,
    "password": settings.ELASTICSEARCH_PASSWORD
}

APP_CONFIG = {
    'debug': settings.DEBUG,
    'log_level': settings.LOG_LEVEL,
    'max_request_size': settings.MAX_REQUEST_SIZE,
    'session_timeout_hours': settings.SESSION_TIMEOUT_HOURS,
    'max_conversation_count': settings.MAX_CONVERSATION_COUNT,
    'confidence_threshold': settings.CONFIDENCE_THRESHOLD,
    'max_agents_per_session': settings.MAX_AGENTS_PER_SESSION,
    'enable_debate': settings.ENABLE_DEBATE
}