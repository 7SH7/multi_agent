"""Utility modules for the chatbot system."""

from .llm_clients import (
    OpenAIClient,
    GeminiClient,
    ClovaClient,
    AnthropicClient,
    LLMResponse,
    LLMError,
    get_llm_client
)

from .rag_engines import (
    ChromaEngine,
    ElasticsearchEngine,
    RAGResult,
    HybridRAGEngine
)

from .validators import (
    RequestValidator,
    InputSanitizer,
    SecurityValidator,
    ValidationError
)

from .database import (
    DatabaseManager,
    get_database_connection,
    execute_query,
    get_equipment_data,
    save_chat_session
)

from .logging_config import (
    setup_logging,
    get_logger,
    log_performance,
    LogLevel
)

__all__ = [
    # LLM Clients
    'OpenAIClient',
    'GeminiClient',
    'ClovaClient',
    'AnthropicClient',
    'LLMResponse',
    'LLMError',
    'get_llm_client',

    # RAG Engines
    'ChromaEngine',
    'ElasticsearchEngine',
    'RAGResult',
    'HybridRAGEngine',

    # Validators
    'RequestValidator',
    'InputSanitizer',
    'SecurityValidator',
    'ValidationError',

    # Database (실제 DB 연결/쿼리용)
    'DatabaseManager',
    'get_database_connection',
    'execute_query',
    'get_equipment_data',
    'save_chat_session',

    # Logging
    'setup_logging',
    'get_logger',
    'log_performance',
    'LogLevel'
]
