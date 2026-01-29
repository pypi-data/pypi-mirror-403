"""Structured JSON Logging для GraphCrawler.

OBSERVABILITY v4.1: JSON-формат логів для easy parsing.

Features:
- JSON format для Elasticsearch/Splunk/etc
- Structured fields (timestamp, level, module, message)
- Extra context fields
- Correlation ID support
- Performance-friendly (lazy formatting)

Usage:
    >>> from graph_crawler.observability.structured_logging import (
    ...     setup_json_logging,
    ...     get_logger,
    ... )
    >>> 
    >>> # Setup JSON logging
    >>> setup_json_logging(level="INFO")
    >>> 
    >>> # Get logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Crawling started", extra={"url": "https://example.com", "depth": 2})
    
Output:
    {"timestamp": "2025-01-15T10:30:00.123Z", "level": "INFO", "module": "package_crawler",
     "message": "Crawling started", "url": "https://example.com", "depth": 2}
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """
    JSON formatter для structured logging.
    
    Formats log records as JSON для easy machine parsing.
    """
    
    # Standard fields always included
    STANDARD_FIELDS = {
        "timestamp", "level", "logger", "module", "funcName", 
        "lineno", "message", "correlation_id"
    }
    
    def __init__(
        self,
        include_traceback: bool = True,
        timestamp_format: str = "iso",
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize JSON formatter.
        
        Args:
            include_traceback: Include full traceback for exceptions
            timestamp_format: "iso" for ISO 8601, "unix" for Unix timestamp
            extra_fields: Extra fields to include in every log (e.g., service name)
        """
        super().__init__()
        self.include_traceback = include_traceback
        self.timestamp_format = timestamp_format
        self.extra_fields = extra_fields or {}
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Timestamp
        if self.timestamp_format == "iso":
            timestamp = datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat()
        else:
            timestamp = record.created
        
        # Base log data
        log_data = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add extra fields from config
        log_data.update(self.extra_fields)
        
        # Add extra fields from log call
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and key not in self.STANDARD_FIELDS:
                if not key.startswith("_"):
                    try:
                        # Test JSON serialization
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)
        
        # Add exception info
        if record.exc_info and self.include_traceback:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if self.include_traceback else None,
            }
        
        # Serialize to JSON
        try:
            # Try orjson for speed
            from graph_crawler.shared.utils.fast_json import dumps
            return dumps(log_data)
        except ImportError:
            return json.dumps(log_data, ensure_ascii=False, default=str)


class CorrelationIDFilter(logging.Filter):
    """
    Filter that adds correlation ID to log records.
    
    Useful for tracing requests across components.
    """
    
    _correlation_id: Optional[str] = None
    
    @classmethod
    def set_correlation_id(cls, correlation_id: str) -> None:
        """Set correlation ID for current context."""
        cls._correlation_id = correlation_id
    
    @classmethod
    def get_correlation_id(cls) -> Optional[str]:
        """Get current correlation ID."""
        return cls._correlation_id
    
    @classmethod
    def clear_correlation_id(cls) -> None:
        """Clear correlation ID."""
        cls._correlation_id = None
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to record."""
        record.correlation_id = self._correlation_id
        return True


def setup_json_logging(
    level: str = "INFO",
    stream: Any = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    include_traceback: bool = True,
) -> None:
    """
    Setup JSON structured logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        stream: Output stream (default: sys.stdout)
        extra_fields: Extra fields to include in every log
        include_traceback: Include full traceback for exceptions
        
    Example:
        >>> setup_json_logging(
        ...     level="INFO",
        ...     extra_fields={"service": "graphcrawler", "version": "4.1"}
        ... )
    """
    # Create formatter
    formatter = JSONFormatter(
        include_traceback=include_traceback,
        extra_fields=extra_fields or {"service": "graphcrawler"},
    )
    
    # Create handler
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIDFilter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers and add JSON handler
    root_logger.handlers = []
    root_logger.addHandler(handler)
    
    logging.info(
        "JSON structured logging initialized",
        extra={"log_level": level, "include_traceback": include_traceback}
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding temporary context to logs.
    
    Example:
        >>> with LogContext(request_id="123", user_id="456"):
        ...     logger.info("Processing request")  # Includes request_id and user_id
    """
    
    _context: Dict[str, Any] = {}
    
    def __init__(self, **kwargs):
        self.new_context = kwargs
        self.old_context = {}
    
    def __enter__(self):
        self.old_context = self._context.copy()
        self._context.update(self.new_context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context = self.old_context
        return False
    
    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """Get current context."""
        return cls._context.copy()


__all__ = [
    "JSONFormatter",
    "CorrelationIDFilter", 
    "setup_json_logging",
    "get_logger",
    "LogContext",
]
