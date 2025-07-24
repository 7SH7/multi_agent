import re
import html
import bleach
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


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