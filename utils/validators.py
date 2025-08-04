import re
import html
import bleach
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    sanitized_data: Dict[str, Any]
    warnings: List[str]


class InputSanitizer:
    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        if not isinstance(text, str):
            return ""

        # HTML 태그 제거
        clean_text = bleach.clean(text, tags=[], strip=True)

        # HTML 엔티티 디코딩
        clean_text = html.unescape(clean_text)

        # 길이 제한
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + "..."

        # 연속된 공백 정리
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        return clean_text

    @staticmethod
    def sanitize_session_id(session_id: str) -> str:
        if not isinstance(session_id, str):
            return ""

        # 영숫자, 하이픈, 언더스코어만 허용
        clean_id = re.sub(r'[^a-zA-Z0-9\-_]', '', session_id)

        # 길이 제한 (최대 50자)
        return clean_id[:50]

    @staticmethod
    def sanitize_issue_code(issue_code: str) -> str:
        if not isinstance(issue_code, str):
            return ""

        # 대문자, 숫자, 하이픈만 허용
        clean_code = re.sub(r'[^A-Z0-9\-]', '', issue_code.upper())

        return clean_code[:100]


class SecurityValidator:
    SUSPICIOUS_PATTERNS = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
        r'import\s+os',
        r'__import__',
        r'subprocess',
        r'system\s*\(',
    ]

    SQL_INJECTION_PATTERNS = [
        r'union\s+select',
        r'drop\s+table',
        r'delete\s+from',
        r'insert\s+into',
        r'update\s+.*set',
        r'--\s*$',
        r'/\*.*?\*/',
    ]

    @classmethod
    def check_xss(cls, text: str) -> List[str]:
        issues = []
        text_lower = text.lower()

        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                issues.append(f"잠재적 XSS 패턴 감지: {pattern}")

        return issues

    @classmethod
    def check_sql_injection(cls, text: str) -> List[str]:
        issues = []
        text_lower = text.lower()

        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                issues.append(f"잠재적 SQL 인젝션 패턴 감지: {pattern}")

        return issues

    @classmethod
    def validate_input_security(cls, text: str) -> List[str]:
        all_issues = []
        all_issues.extend(cls.check_xss(text))
        all_issues.extend(cls.check_sql_injection(text))
        return all_issues


class RequestValidator:
    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.security_validator = SecurityValidator()

    def validate_chat_request(self, data: Dict[str, Any]) -> ValidationResult:
        errors = []
        warnings = []
        sanitized_data = {}

        # 사용자 메시지 검증
        user_message = data.get('user_message', '')
        if not user_message or not user_message.strip():
            errors.append("사용자 메시지가 비어있습니다")
        elif len(user_message) > 5000:
            errors.append("사용자 메시지가 너무 깁니다 (최대 5000자)")
        else:
            # 보안 검증
            security_issues = self.security_validator.validate_input_security(user_message)
            if security_issues:
                errors.extend(security_issues)
            else:
                sanitized_data['user_message'] = self.sanitizer.sanitize_text(user_message, 5000)

        # 세션 ID 검증 (선택적)
        session_id = data.get('session_id')
        if session_id:
            if not isinstance(session_id, str):
                errors.append("세션 ID는 문자열이어야 합니다")
            elif not re.match(r'^[a-zA-Z0-9\-_]+$', session_id):
                errors.append("세션 ID 형식이 올바르지 않습니다")
            else:
                sanitized_data['session_id'] = self.sanitizer.sanitize_session_id(session_id)

        # 이슈 코드 검증 (선택적)
        issue_code = data.get('issue_code')
        if issue_code:
            if not isinstance(issue_code, str):
                errors.append("이슈 코드는 문자열이어야 합니다")
            elif not re.match(r'^[A-Z0-9\-]+$', issue_code.upper()):
                warnings.append("이슈 코드 형식이 표준과 다를 수 있습니다")
            sanitized_data['issue_code'] = self.sanitizer.sanitize_issue_code(issue_code)

        # 사용자 ID 검증 (선택적)
        user_id = data.get('user_id')
        if user_id:
            if not isinstance(user_id, str):
                errors.append("사용자 ID는 문자열이어야 합니다")
            elif len(user_id) > 100:
                errors.append("사용자 ID가 너무 깁니다")
            else:
                sanitized_data['user_id'] = self.sanitizer.sanitize_text(user_id, 100)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_data=sanitized_data,
            warnings=warnings
        )

    def validate_session_id(self, session_id: str) -> ValidationResult:
        errors = []
        warnings = []

        if not session_id:
            errors.append("세션 ID가 필요합니다")
        elif not isinstance(session_id, str):
            errors.append("세션 ID는 문자열이어야 합니다")
        elif len(session_id) > 50:
            errors.append("세션 ID가 너무 깁니다")
        elif not re.match(r'^[a-zA-Z0-9\-_]+$', session_id):
            errors.append("올바르지 않은 세션 ID 형식입니다")

        sanitized_data = {
            'session_id': self.sanitizer.sanitize_session_id(session_id) if session_id else ''
        }

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_data=sanitized_data,
            warnings=warnings
        )

    def validate_issue_code(self, issue_code: str) -> ValidationResult:
        errors = []
        warnings = []

        if not issue_code:
            errors.append("이슈 코드가 없습니다")
        elif not isinstance(issue_code, str):
            errors.append("이슈 코드는 문자열이어야 합니다")
        else:
            # ASBP-XXX-XXX-YYYYMMDDNNN 형식 검사
            pattern = r'^ASBP-[A-Z]+-[A-Z]+-\d{11}$'
            if not re.match(pattern, issue_code.upper()):
                warnings.append(f"이슈 코드가 표준 형식과 다릅니다: {pattern}")

        sanitized_data = {
            'issue_code': self.sanitizer.sanitize_issue_code(issue_code) if issue_code else ''
        }

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_data=sanitized_data,
            warnings=warnings
        )


class DataValidator:
    @staticmethod
    def validate_agent_response(response_data: Dict[str, Any]) -> ValidationResult:
        errors = []
        warnings = []
        sanitized_data = {}

        required_fields = ['agent_name', 'response', 'confidence']

        for field in required_fields:
            if field not in response_data:
                errors.append(f"필수 필드 누락: {field}")

        # agent_name 검증
        agent_name = response_data.get('agent_name')
        if agent_name:
            if agent_name not in ['gpt', 'gemini', 'clova', 'claude']:
                warnings.append(f"알 수 없는 agent: {agent_name}")
            sanitized_data['agent_name'] = agent_name

        # confidence 검증
        confidence = response_data.get('confidence')
        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                errors.append("신뢰도는 숫자여야 합니다")
            elif not 0 <= confidence <= 1:
                errors.append("신뢰도는 0과 1 사이여야 합니다")
            else:
                sanitized_data['confidence'] = float(confidence)

        # response 검증
        response = response_data.get('response')
        if response:
            if len(response) > 10000:
                warnings.append("응답이 매우 깁니다")
            sanitizer = InputSanitizer()
            sanitized_data['response'] = sanitizer.sanitize_text(response, 10000)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_data=sanitized_data,
            warnings=warnings
        )


class ConfigValidator:
    """환경 설정 및 API 키 검증 클래스"""
    
    REQUIRED_API_KEYS = [
        "OPENAI_API_KEY",
        "GOOGLE_AI_API_KEY", 
        "ANTHROPIC_API_KEY",
        "NAVER_API_KEY",
        "NAVER_API_KEY_ID"
    ]
    
    REQUIRED_DB_CONFIGS = [
        "DB_HOST",
        "DB_NAME", 
        "DB_USERNAME",
        "DB_PASSWORD"
    ]
    
    REQUIRED_SERVICE_CONFIGS = [
        "REDIS_HOST",
        "CHROMA_HOST",
        "ELASTICSEARCH_HOST"
    ]
    
    @classmethod
    def validate_startup_config(cls, settings) -> ValidationResult:
        """시작시 필수 설정 검증 (오류 대신 경고 로깅)"""
        warnings = []
        sanitized_data = {}
        
        # API 키 검증 -> 경고로 처리
        api_key_warnings = cls._validate_api_keys(settings)
        warnings.extend(api_key_warnings)
        
        # 데이터베이스 설정 검증 -> 경고로 처리
        db_warnings = cls._validate_database_config(settings)
        warnings.extend(db_warnings)
        
        # 외부 서비스 설정 검증
        service_warnings = cls._validate_service_configs(settings)
        warnings.extend(service_warnings)
        
        # 로그 레벨 검증
        log_warnings = cls._validate_log_config(settings)
        warnings.extend(log_warnings)
        
        # 이제 항상 is_valid=True를 반환하여 서버 시작을 막지 않음
        return ValidationResult(
            is_valid=True,
            errors=[], # 오류를 발생시키지 않음
            sanitized_data=sanitized_data,
            warnings=warnings
        )
    
    @classmethod
    def _validate_api_keys(cls, settings) -> List[str]:
        """API 키 검증 (경고용 메시지 반환)"""
        warnings = []
        missing_keys = []
        invalid_keys = []
        
        for key in cls.REQUIRED_API_KEYS:
            value = getattr(settings, key, "")
            if not value or value.strip() == "":
                missing_keys.append(key)
            else:
                # API 키 형식 검증
                if not cls._is_valid_api_key_format(key, value):
                    invalid_keys.append(key)
        
        if missing_keys:
            warnings.append(f"필수 API 키가 누락되었습니다: {', '.join(missing_keys)}. 해당 Agent는 작동하지 않을 수 있습니다.")
            
        if invalid_keys:
            warnings.append(f"API 키 형식이 올바르지 않습니다: {', '.join(invalid_keys)}. 해당 Agent는 작동하지 않을 수 있습니다.")
            
        return warnings
    
    @classmethod
    def _validate_database_config(cls, settings) -> List[str]:
        """데이터베이스 설정 검증 (경고용 메시지 반환)"""
        warnings = []
        missing_configs = []
        
        for config in cls.REQUIRED_DB_CONFIGS:
            value = getattr(settings, config, "")
            if not value or value.strip() == "":
                missing_configs.append(config)
        
        if missing_configs:
            warnings.append(f"필수 데이터베이스 설정이 누락되었습니다: {', '.join(missing_configs)}. DB 관련 기능이 제한될 수 있습니다.")
            
        # DATABASE_URL 생성 테스트
        try:
            db_url = settings.DATABASE_URL
            if not db_url or "mysql://" not in db_url:
                warnings.append("DATABASE_URL 생성에 실패했습니다. DB 설정을 확인하세요.")
        except Exception as e:
            warnings.append(f"DATABASE_URL 검증 오류: {str(e)}")
            
        return warnings
    
    @classmethod
    def _validate_service_configs(cls, settings) -> List[str]:
        """외부 서비스 설정 검증"""
        warnings = []
        
        for config in cls.REQUIRED_SERVICE_CONFIGS:
            value = getattr(settings, config, "")
            if not value or value.strip() == "":
                warnings.append(f"외부 서비스 설정이 누락되었습니다: {config}. 관련 기능이 제한될 수 있습니다.")
            elif value == "localhost" and getattr(settings, "ENVIRONMENT", "") == "production":
                warnings.append(f"운영 환경에서 localhost 사용 중: {config}")
                
        return warnings
    
    @classmethod
    def _validate_log_config(cls, settings) -> List[str]:
        """로그 설정 검증"""
        warnings = []
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = getattr(settings, "LOG_LEVEL", "INFO").upper()
        
        if log_level not in valid_log_levels:
            warnings.append(f"올바르지 않은 로그 레벨: {log_level}. 기본값 INFO 사용")
            
        return warnings
    
    @classmethod
    def _is_valid_api_key_format(cls, key_name: str, key_value: str) -> bool:
        """API 키 형식 검증"""
        key_value = key_value.strip()
        
        # 최소 길이 검증
        if len(key_value) < 10:
            return False
            
        # 특정 API 키별 형식 검증
        if key_name == "OPENAI_API_KEY":
            return key_value.startswith("sk-") and len(key_value) > 20
        elif key_name == "GOOGLE_AI_API_KEY":
            return len(key_value) > 30  # Google API 키는 일반적으로 길다
        elif key_name == "ANTHROPIC_API_KEY":
            return key_value.startswith("sk-ant-") and len(key_value) > 30
        elif key_name in ["NAVER_API_KEY", "NAVER_API_KEY_ID"]:
            return len(key_value) > 10  # Naver API 키는 다양한 형식
            
        return True  # 기본적으로 유효하다고 간주
    
    @classmethod
    def validate_runtime_dependencies(cls) -> ValidationResult:
        """런타임 의존성 검증 (오류 대신 경고 로깅)"""
        warnings = []
        
        # 필수 라이브러리 import 테스트
        try:
            import anthropic
        except ImportError:
            warnings.append("anthropic 라이브러리가 없어 Claude Agent 사용이 불가합니다.")
        try:
            import openai
        except ImportError:
            warnings.append("openai 라이브러리가 없어 GPT Agent 사용이 불가합니다.")
        try:
            import google.generativeai
        except ImportError:
            warnings.append("google.generativeai 라이브러리가 없어 Gemini Agent 사용이 불가합니다.")
        try:
            import redis
        except ImportError:
            warnings.append("redis 라이브러리가 없어 세션 관리에 제약이 있을 수 있습니다.")
        try:
            import elasticsearch
        except ImportError:
            warnings.append("elasticsearch 라이브러리가 없어 RAG 검색에 제약이 있을 수 있습니다.")
        try:
            import chromadb
        except ImportError:
            warnings.append("chromadb 라이브러리가 없어 RAG 검색에 제약이 있을 수 있습니다.")

        # 환경 변수 존재 확인
        import os
        if not os.path.exists(".env"):
            warnings.append(".env 파일이 존재하지 않습니다. 환경 변수가 시스템에서 로드됩니다.")
        
        return ValidationResult(
            is_valid=True, # 항상 True
            errors=[],
            sanitized_data={},
            warnings=warnings
        )
    
    @classmethod
    def get_health_check_status(cls, settings) -> Dict[str, Any]:
        """설정 상태 건강 체크"""
        status = {
            "config_valid": True,
            "api_keys_present": 0,
            "missing_keys": [],
            "service_configs": {},
            "warnings": []
        }
        
        # API 키 상태 체크
        total_keys = len(cls.REQUIRED_API_KEYS)
        present_keys = 0
        
        for key in cls.REQUIRED_API_KEYS:
            value = getattr(settings, key, "")
            if value and value.strip():
                present_keys += 1
            else:
                status["missing_keys"].append(key)
        
        status["api_keys_present"] = present_keys
        status["api_keys_total"] = total_keys
        
        # 서비스 설정 상태
        for config in cls.REQUIRED_SERVICE_CONFIGS:
            value = getattr(settings, config, "")
            status["service_configs"][config] = bool(value and value.strip())
        
        # 전체 유효성
        if present_keys < total_keys:
            status["config_valid"] = False
            status["warnings"].append(f"API 키 {total_keys - present_keys}개 누락")
        
        return status