"""
Enhanced Fibonacci Client with Audit Logging

This module provides a wrapper around FibonacciClient that adds:
- Automatic audit logging for all API calls
- Request/response time tracking
- Automatic sensitive data redaction
- Security event logging
"""

import time
from typing import Any, Dict, Optional

from fibonacci.client import FibonacciClient as BaseClient
from fibonacci.audit_logging import get_audit_logger
from fibonacci.secure_config import SecureConfig, redact_sensitive_data


class SecureFibonacciClient(BaseClient):
    """
    Enhanced Fibonacci client with built-in audit logging and security.
    
    Drop-in replacement for FibonacciClient with added security features.
    
    Example:
        >>> from fibonacci import SecureFibonacciClient, SecureConfig
        >>> 
        >>> config = SecureConfig.from_env()
        >>> async with SecureFibonacciClient(config) as client:
        ...     workflows = await client.list_workflows()
        >>> # All API calls are automatically logged!
    """
    
    def __init__(self, config: Optional[SecureConfig] = None, enable_logging: bool = True):
        """
        Initialize secure client.
        
        Args:
            config: SecureConfig instance (uses default if not provided)
            enable_logging: Enable automatic audit logging
        """
        super().__init__(config)
        self.enable_logging = enable_logging
        self.audit_logger = get_audit_logger() if enable_logging else None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make HTTP request with audit logging.
        
        Automatically logs:
        - Request method and endpoint
        - Response status code
        - Request duration
        - Any errors
        """
        start_time = time.time()
        
        try:
            # Make the request
            response = await super()._request(method, endpoint, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful request
            if self.audit_logger:
                # Redact any sensitive data in kwargs
                safe_kwargs = redact_sensitive_data(kwargs) if kwargs else {}
                
                self.audit_logger.log_api_request(
                    method=method,
                    endpoint=endpoint,
                    status_code=200,  # Successful
                    duration_ms=round(duration_ms, 2),
                    request_params=safe_kwargs
                )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            if self.audit_logger:
                status_code = getattr(e, 'status_code', None)
                
                self.audit_logger.log_api_error(
                    endpoint=endpoint,
                    error=str(e),
                    status_code=status_code,
                    duration_ms=round(duration_ms, 2)
                )
                
                # Log auth failures specifically
                if status_code == 401:
                    self.audit_logger.log_auth_failure(
                        method="api_key",
                        reason="Invalid or expired API key"
                    )
            
            # Re-raise the exception
            raise
    
    async def create_workflow(self, definition: Dict[str, Any]) -> str:
        """Create workflow with logging."""
        workflow_id = await super().create_workflow(definition)
        
        if self.audit_logger:
            self.audit_logger._log_event(
                self.audit_logger.AuditEventType.WORKFLOW_CREATED,
                {
                    "workflow_id": workflow_id,
                    "workflow_name": definition.get("name", "Unknown")
                }
            )
        
        return workflow_id
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        tags: Optional[list[str]] = None,
    ):
        """Execute workflow with logging."""
        start_time = time.time()
        
        try:
            result = await super().execute_workflow(workflow_id, input_data, tags)
            
            # Log execution
            if self.audit_logger:
                duration = time.time() - start_time
                
                self.audit_logger.log_workflow_executed(
                    workflow_id=workflow_id,
                    run_id=result.id,
                    status=result.status,
                    duration_seconds=round(duration, 2),
                    cost=result.total_cost
                )
            
            return result
            
        except Exception as e:
            # Log failed execution
            if self.audit_logger:
                duration = time.time() - start_time
                
                self.audit_logger.log_workflow_executed(
                    workflow_id=workflow_id,
                    run_id="unknown",
                    status="failed",
                    duration_seconds=round(duration, 2),
                    error=str(e)
                )
            
            raise


# Make SecureFibonacciClient the default when security is enabled
def create_client(
    config: Optional[SecureConfig] = None,
    secure: bool = True
) -> BaseClient:
    """
    Create a Fibonacci client.
    
    Args:
        config: Configuration (uses default if not provided)
        secure: Use secure client with audit logging (recommended)
    
    Returns:
        Client instance
    
    Example:
        >>> from fibonacci import create_client
        >>> 
        >>> # Secure client (recommended)
        >>> client = create_client(secure=True)
        >>> 
        >>> # Basic client (no logging)
        >>> client = create_client(secure=False)
    """
    if secure:
        return SecureFibonacciClient(config)
    else:
        return BaseClient(config)
    


__all__ = [
    "SecureFibonacciClient",
    "create_client",
]


