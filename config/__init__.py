"""Configuration modules and settings."""

from .issue_loader import ISSUE_DATABASE, ISSUE_CATEGORIES, SEVERITY_LEVELS

from .equipment_thresholds import (
    EQUIPMENT_THRESHOLDS,
    EQUIPMENT_ROOT_CAUSES,
    EQUIPMENT_TRANSLATIONS,
    PROBLEM_TYPE_TRANSLATIONS
)

__all__ = [
    # Settings
    'settings',
    'DATABASE_URL',
    'REDIS_CONFIG',
    'LLM_CONFIGS',
    'CHROMADB_CONFIG',
    'ELASTICSEARCH_CONFIG',
    'APP_CONFIG',  # 추가

    # Equipment Configuration
    'EQUIPMENT_THRESHOLDS',
    'EQUIPMENT_ROOT_CAUSES',
    'EQUIPMENT_TRANSLATIONS',
    'PROBLEM_TYPE_TRANSLATIONS',

    # Issue Database
    'ISSUE_DATABASE',
    'ISSUE_CATEGORIES',
    'SEVERITY_LEVELS',
]
