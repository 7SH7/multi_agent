import os
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.session_manager import SessionManager
from core.enhanced_workflow import create_enhanced_workflow
from core.monitoring import get_system_monitor
from config.settings import APP_CONFIG, LLM_CONFIGS
from utils.validators import RequestValidator

# Global instances
_session_manager = None
_workflow_manager = None
_security_manager = None

security = HTTPBearer(auto_error=False)

class SecurityManager:
    def __init__(self):
        self.api_keys = {
            "admin": os.getenv("ADMIN_API_KEY", "admin-key-123"),
            "user": os.getenv("USER_API_KEY", "user-key-456")
        }
        self.rate_limits = {
            "admin": 1000,  # requests per hour
            "user": 100
        }
        self.request_counts = {}
    
    def validate_api_key(self, api_key: str) -> Optional[str]:
        for role, key in self.api_keys.items():
            if key == api_key:
                return role
        return None
    
    def check_rate_limit(self, api_key: str, role: str) -> bool:
        # Simple in-memory rate limiting (use Redis in production)
        import time
        current_time = int(time.time() / 3600)  # Current hour
        
        key = f"{api_key}:{current_time}"
        current_count = self.request_counts.get(key, 0)
        
        if current_count >= self.rate_limits.get(role, 100):
            return False
        
        self.request_counts[key] = current_count + 1
        return True

def get_security_manager() -> SecurityManager:
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager

def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

def get_workflow_manager():
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = create_enhanced_workflow()
    return _workflow_manager

def get_system_monitor():
    return get_system_monitor()

async def validate_request(request: Request) -> Dict[str, Any]:
    """Request validation"""
    validator = RequestValidator()
    
    # Check request size
    if hasattr(request, 'body'):
        body = await request.body()
        if len(body) > APP_CONFIG['max_request_size']:
            raise HTTPException(
                status_code=413,
                detail="Request too large"
            )
    
    # Basic request validation
    if request.method == "POST":
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            raise HTTPException(
                status_code=400,
                detail="Content-Type must be application/json"
            )
    
    return {"status": "valid"}

async def check_api_keys(
    request: Request,
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None)
) -> Optional[str]:
    """API Key validation"""
    
    # Skip API key check in development
    if APP_CONFIG.get('debug', False):
        return "admin"
    
    api_key = None
    
    # Check Authorization header
    if authorization:
        api_key = authorization.credentials
    # Check X-API-Key header
    elif x_api_key:
        api_key = x_api_key
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
    
    security_manager = get_security_manager()
    role = security_manager.validate_api_key(api_key)
    
    if not role:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Check rate limiting
    if not security_manager.check_rate_limit(api_key, role):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    return role

async def get_current_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get current session with validation"""
    session_data = await session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    return session_data

def verify_llm_keys():
    """Verify all required LLM API keys are present"""
    missing_keys = []
    
    for llm_name, config in LLM_CONFIGS.items():
        if config.get('enabled', True):
            api_key = config.get('api_key')
            if not api_key or api_key.startswith('your_'):
                missing_keys.append(llm_name)
    
    if missing_keys:
        print(f"⚠️  Warning: Missing API keys for: {', '.join(missing_keys)}")
        print("   Some agents may not work properly.")
    
    return len(missing_keys) == 0

# Initialize and verify on startup
verify_llm_keys()
