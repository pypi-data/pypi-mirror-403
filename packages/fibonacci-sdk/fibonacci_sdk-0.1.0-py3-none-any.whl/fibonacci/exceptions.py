"""
Fibonacci SDK Exceptions

Custom exception classes for better error handling.
"""


class FibonacciError(Exception):
    """Base exception for all Fibonacci SDK errors."""
    
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(FibonacciError):
    """Raised when API key is invalid or missing."""
    
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message)


class ValidationError(FibonacciError):
    """Raised when workflow validation fails."""
    
    def __init__(self, message: str, errors: list[str] | None = None):
        self.errors = errors or []
        details = {"validation_errors": self.errors}
        super().__init__(message, details)


class ExecutionError(FibonacciError):
    """Raised when workflow execution fails."""
    
    def __init__(self, message: str, run_id: str | None = None, node_id: str | None = None):
        self.run_id = run_id
        self.node_id = node_id
        details = {}
        if run_id:
            details["run_id"] = run_id
        if node_id:
            details["node_id"] = node_id
        super().__init__(message, details)


class APIError(FibonacciError):
    """Raised when API request fails."""
    
    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        self.status_code = status_code
        self.response = response or {}
        details = {"status_code": status_code, "response": self.response}
        super().__init__(message, details)


class ConfigurationError(FibonacciError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str):
        super().__init__(message)


class DeploymentError(FibonacciError):
    """Raised when workflow deployment fails."""
    
    def __init__(self, message: str, workflow_name: str | None = None):
        self.workflow_name = workflow_name
        details = {"workflow_name": workflow_name} if workflow_name else {}
        super().__init__(message, details)



__all__ = [
    "FibonacciError",
    "AuthenticationError",
    "ValidationError",
    "ExecutionError",
    "APIError",
    "ConfigurationError",
    "DeploymentError",
]


