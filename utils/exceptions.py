"""커스텀 예외 클래스들"""

from typing import Optional, Any

class ChatbotError(Exception):
    """챗봇 기본 예외"""
    def __init__(self, message: str, error_code: str = "CHATBOT_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class AgentError(ChatbotError):
    """Agent 관련 예외"""
    def __init__(self, message: str, agent_name: Optional[str] = None):
        self.agent_name = agent_name
        error_code = f"AGENT_ERROR_{agent_name.upper()}" if agent_name else "AGENT_ERROR"
        super().__init__(message, error_code)

class APIError(ChatbotError):
    """API 호출 관련 예외"""
    def __init__(self, message: str, api_name: Optional[str] = None, status_code: Optional[int] = None):
        self.api_name = api_name
        self.status_code = status_code
        error_code = f"API_ERROR_{api_name.upper()}" if api_name else "API_ERROR"
        super().__init__(message, error_code)

class RateLimitError(APIError):
    """API 호출 한도 초과 예외"""
    def __init__(self, message: str, api_name: Optional[str] = None, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message, api_name, 429)

class TimeoutError(APIError):
    """타임아웃 예외"""
    def __init__(self, message: str, timeout_duration: Optional[float] = None):
        self.timeout_duration = timeout_duration
        super().__init__(message, "TIMEOUT_ERROR")

class ValidationError(ChatbotError):
    """입력 검증 예외"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")

class SessionError(ChatbotError):
    """세션 관련 예외"""
    def __init__(self, message: str, session_id: Optional[str] = None):
        self.session_id = session_id
        super().__init__(message, "SESSION_ERROR")

class RAGError(ChatbotError):
    """RAG 검색 관련 예외"""
    def __init__(self, message: str, search_type: Optional[str] = None):
        self.search_type = search_type
        super().__init__(message, "RAG_ERROR")

class DatabaseError(ChatbotError):
    """데이터베이스 관련 예외"""
    def __init__(self, message: str, db_type: Optional[str] = None):
        self.db_type = db_type
        super().__init__(message, "DATABASE_ERROR")

class ConfigError(ChatbotError):
    """설정 관련 예외"""
    def __init__(self, message: str, config_key: Optional[str] = None):
        self.config_key = config_key
        super().__init__(message, "CONFIG_ERROR")

class WorkflowError(ChatbotError):
    """워크플로우 실행 예외"""
    def __init__(self, message: str, step: Optional[str] = None):
        self.step = step
        super().__init__(message, "WORKFLOW_ERROR")

# 예외 처리 유틸리티 함수들
def handle_api_error(e: Exception, api_name: str) -> APIError:
    """API 예외를 표준화"""
    if "rate limit" in str(e).lower():
        return RateLimitError(f"{api_name} API 호출 한도 초과", api_name)
    elif "timeout" in str(e).lower():
        return TimeoutError(f"{api_name} API 타임아웃")
    elif "unauthorized" in str(e).lower():
        return APIError(f"{api_name} API 인증 실패", api_name, 401)
    else:
        return APIError(f"{api_name} API 오류: {str(e)}", api_name)

def handle_validation_error(field: str, value: Any, rule: str) -> ValidationError:
    """검증 예외 생성"""
    return ValidationError(f"'{field}' 필드가 {rule} 규칙을 위반했습니다: {value}", field)