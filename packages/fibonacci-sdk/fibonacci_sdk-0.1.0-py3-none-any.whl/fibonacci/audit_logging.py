"""
Fibonacci SDK - Audit Logging

Comprehensive audit logging for security and compliance.

Logs:
- All API requests/responses
- Authentication attempts
- Workflow executions
- Configuration changes
- Security events
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from enum import Enum

from fibonacci.secure_config import redact_api_key, redact_sensitive_data


class AuditEventType(Enum):
    """Types of audit events."""
    
    # Authentication
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    API_KEY_CREATED = "api_key_created"
    API_KEY_DELETED = "api_key_deleted"
    
    # API Operations
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    API_ERROR = "api_error"
    
    # Workflow Operations
    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_UPDATED = "workflow_updated"
    WORKFLOW_DELETED = "workflow_deleted"
    WORKFLOW_EXECUTED = "workflow_executed"
    
    # Configuration
    CONFIG_LOADED = "config_loaded"
    CONFIG_CHANGED = "config_changed"
    
    # Security
    SECURITY_VIOLATION = "security_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"


class AuditLogger:
    """
    Audit logger for security events.
    
    Logs are written to both file and structured JSON format.
    
    Example:
        >>> from fibonacci import AuditLogger
        >>> 
        >>> logger = AuditLogger()
        >>> logger.log_api_request(
        ...     method="POST",
        ...     endpoint="/workflows",
        ...     status_code=201
        ... )
    """
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        log_level: int = logging.INFO
    ):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Directory for log files (default: ~/.fibonacci/logs)
            log_level: Logging level
        """
        # Setup log directory
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".fibonacci" / "logs"
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup loggers
        self.audit_log = self._setup_logger(
            "fibonacci.audit",
            self.log_dir / "audit.log",
            log_level
        )
        
        self.security_log = self._setup_logger(
            "fibonacci.security",
            self.log_dir / "security.log",
            logging.WARNING
        )
    
    def _setup_logger(
        self,
        name: str,
        log_file: Path,
        level: int
    ) -> logging.Logger:
        """Setup a logger with file and console handlers."""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # File handler (JSON format)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(message)s'  # Just the JSON message
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler (only for security events)
        if "security" in name:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            console_formatter = logging.Formatter(
                '🔒 SECURITY: %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _log_event(
        self,
        event_type: AuditEventType,
        data: Dict[str, Any],
        is_security_event: bool = False
    ) -> None:
        """Log an audit event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            **data
        }
        
        # Redact sensitive data
        event = redact_sensitive_data(event)
        
        # Log to appropriate logger
        log_message = json.dumps(event)
        
        if is_security_event:
            self.security_log.warning(log_message)
        else:
            self.audit_log.info(log_message)
    
    def log_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> None:
        """
        Log API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            **kwargs: Additional context
        """
        self._log_event(
            AuditEventType.API_REQUEST,
            {
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "duration_ms": duration_ms,
                **kwargs
            }
        )
    
    def log_api_response(
        self,
        endpoint: str,
        status_code: int,
        response_size: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log API response."""
        self._log_event(
            AuditEventType.API_RESPONSE,
            {
                "endpoint": endpoint,
                "status_code": status_code,
                "response_size": response_size,
                **kwargs
            }
        )
    
    def log_api_error(
        self,
        endpoint: str,
        error: str,
        status_code: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log API error."""
        self._log_event(
            AuditEventType.API_ERROR,
            {
                "endpoint": endpoint,
                "error": error,
                "status_code": status_code,
                **kwargs
            },
            is_security_event=(status_code in [401, 403])
        )
    
    def log_auth_success(
        self,
        method: str,  # "jwt", "api_key", etc.
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log successful authentication."""
        self._log_event(
            AuditEventType.AUTH_SUCCESS,
            {
                "method": method,
                "user_id": user_id,
                **kwargs
            }
        )
    
    def log_auth_failure(
        self,
        method: str,
        reason: str,
        **kwargs
    ) -> None:
        """Log failed authentication attempt."""
        self._log_event(
            AuditEventType.AUTH_FAILURE,
            {
                "method": method,
                "reason": reason,
                **kwargs
            },
            is_security_event=True
        )
    
    def log_workflow_executed(
        self,
        workflow_id: str,
        run_id: str,
        status: str,
        duration_seconds: Optional[float] = None,
        cost: Optional[float] = None,
        **kwargs
    ) -> None:
        """Log workflow execution."""
        self._log_event(
            AuditEventType.WORKFLOW_EXECUTED,
            {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "status": status,
                "duration_seconds": duration_seconds,
                "cost": cost,
                **kwargs
            }
        )
    
    def log_security_violation(
        self,
        violation_type: str,
        description: str,
        **kwargs
    ) -> None:
        """Log security violation."""
        self._log_event(
            AuditEventType.SECURITY_VIOLATION,
            {
                "violation_type": violation_type,
                "description": description,
                **kwargs
            },
            is_security_event=True
        )
    
    def log_rate_limit_exceeded(
        self,
        endpoint: str,
        limit: int,
        **kwargs
    ) -> None:
        """Log rate limit exceeded."""
        self._log_event(
            AuditEventType.RATE_LIMIT_EXCEEDED,
            {
                "endpoint": endpoint,
                "limit": limit,
                **kwargs
            },
            is_security_event=True
        )
    
    def get_recent_events(
        self,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100
    ) -> list:
        """
        Get recent audit events.
        
        Args:
            event_type: Filter by event type
            limit: Maximum number of events
        
        Returns:
            List of audit events
        """
        events = []
        log_file = self.log_dir / "audit.log"
        
        if not log_file.exists():
            return events
        
        try:
            with open(log_file, "r") as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # Filter by type if specified
                        if event_type and event.get("event_type") != event_type.value:
                            continue
                        
                        events.append(event)
                        
                        if len(events) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        return list(reversed(events))  # Most recent first


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    
    return _audit_logger


def enable_audit_logging(log_dir: Optional[str] = None) -> AuditLogger:
    """
    Enable audit logging.
    
    Args:
        log_dir: Directory for log files
    
    Returns:
        Configured audit logger
    
    Example:
        >>> from fibonacci import enable_audit_logging
        >>> logger = enable_audit_logging()
        >>> # All API calls will now be logged
    """
    global _audit_logger
    _audit_logger = AuditLogger(log_dir=log_dir)
    return _audit_logger


def disable_audit_logging() -> None:
    """Disable audit logging."""
    global _audit_logger
    _audit_logger = None


__all__ = [
    # Enums
    "AuditEventType",
    # Classes
    "AuditLogger",
    # Functions
    "get_audit_logger",
    "enable_audit_logging",
    "disable_audit_logging",
]


