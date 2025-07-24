import logging
import sys
from datetime import datetime
from typing import Optional
from enum import Enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup logging configuration"""

    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(console_formatter)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        format='%(message)s'
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def log_performance(operation: str, duration: float, **kwargs):
    """Log performance metrics"""
    logger = get_logger("performance")
    logger.info(f"{operation} completed in {duration:.2f}s", extra=kwargs)


# Initialize logging on import
setup_logging()
