"""Configuration settings for Multi-Agent chatbot system."""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # API Keys
    OPENAI_API_KEY: str = ""
    GOOGLE_AI_API_KEY: str = ""
    NAVER_API_KEY: str = ""
    NAVER_API_KEY_ID: str = ""  # Naver Cloud Platform API Key ID
    ANTHROPIC_API_KEY: str = ""

    # Database Configuration - Individual components
    DB_HOST: str = "localhost:3306"
    DB_NAME: str = "chatbot_db"
    DB_USERNAME: str = "chatbot_user"
    DB_PASSWORD: str = ""
    
    # Computed DATABASE_URL property
    @property
    def DATABASE_URL(self) -> str:
        # Extract host and port from DB_HOST
        if '://' in self.DB_HOST:
            host_part = self.DB_HOST.split('://')[-1]
        else:
            host_part = self.DB_HOST
        return f"mysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{host_part}/{self.DB_NAME}"
    
    # MySQL 자격증명 (Docker용)
    MYSQL_ROOT_PASSWORD: str = ""
    MYSQL_DATABASE: str = "chatbot_db"
    MYSQL_USER: str = "chatbot_user"
    MYSQL_PASSWORD: str = ""

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
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024

    # Agent Configuration
    CONFIDENCE_THRESHOLD: float = 0.75
    MAX_AGENTS_PER_SESSION: int = 3
    ENABLE_DEBATE: bool = True

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1

    # Docker/Runtime Configuration
    PYTHONPATH: str = ""
    ENVIRONMENT: str = "development"
    
    # Admin API Keys
    ADMIN_API_KEY: str = ""
    USER_API_KEY: str = ""

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
        "api_key": settings.NAVER_API_KEY,
        "api_key_id": settings.NAVER_API_KEY_ID,
        "model": "HCX-003",
        "max_tokens": 2000,
        "temperature": 0.2
    },
    "anthropic": {
        "api_key": settings.ANTHROPIC_API_KEY,
        "model": "claude-3-5-sonnet-20240620",
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