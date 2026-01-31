"""
Fibonacci SDK - Constants

Centralized constants used throughout the SDK.
All magic strings, default values, and configuration constants live here.
"""

from typing import Final

# =============================================================================
# VERSION
# =============================================================================

SDK_VERSION: Final[str] = "0.1.0"
SDK_NAME: Final[str] = "fibonacci-sdk"

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Default API URL (production)
DEFAULT_API_URL: Final[str] = "https://api.fibonacci.today"

# API version
API_VERSION: Final[str] = "v1"

# User agent for HTTP requests
USER_AGENT: Final[str] = f"{SDK_NAME}/{SDK_VERSION}"

# =============================================================================
# REQUEST DEFAULTS
# =============================================================================

# Default timeout for API requests (seconds)
DEFAULT_TIMEOUT: Final[int] = 300

# Default maximum retry attempts
DEFAULT_MAX_RETRIES: Final[int] = 3

# Default retry delay (seconds) - used for exponential backoff base
DEFAULT_RETRY_DELAY: Final[float] = 1.0

# Default polling interval for workflow completion (seconds)
DEFAULT_POLL_INTERVAL: Final[float] = 2.0

# Default workflow execution timeout (seconds)
DEFAULT_EXECUTION_TIMEOUT: Final[float] = 300.0

# =============================================================================
# MODEL DEFAULTS
# =============================================================================

# Default Claude model for LLM nodes
DEFAULT_MODEL: Final[str] = "claude-haiku-4-5"

# Available Claude models
AVAILABLE_MODELS: Final[tuple[str, ...]] = (
    "claude-haiku-4-5",
    "claude-sonnet-4-5",
    "claude-opus-4-5",
    "claude-sonnet-4-5-20250929",
)

# Default max tokens for LLM responses
DEFAULT_MAX_TOKENS: Final[int] = 2000

# Default temperature for LLM generation
DEFAULT_TEMPERATURE: Final[float] = 1.0

# Temperature bounds
MIN_TEMPERATURE: Final[float] = 0.0
MAX_TEMPERATURE: Final[float] = 1.0

# =============================================================================
# NODE TYPES
# =============================================================================

NODE_TYPE_LLM: Final[str] = "llm"
NODE_TYPE_TOOL: Final[str] = "tool"
NODE_TYPE_CRITIC: Final[str] = "critic"
NODE_TYPE_CONDITION: Final[str] = "condition"

VALID_NODE_TYPES: Final[tuple[str, ...]] = (
    NODE_TYPE_LLM,
    NODE_TYPE_TOOL,
    NODE_TYPE_CRITIC,
    NODE_TYPE_CONDITION,
)

# =============================================================================
# CONDITION OPERATORS
# =============================================================================

OPERATOR_EQUALS: Final[str] = "equals"
OPERATOR_NOT_EQUALS: Final[str] = "not_equals"
OPERATOR_CONTAINS: Final[str] = "contains"
OPERATOR_NOT_CONTAINS: Final[str] = "not_contains"
OPERATOR_GREATER_THAN: Final[str] = "greater_than"
OPERATOR_LESS_THAN: Final[str] = "less_than"
OPERATOR_STARTS_WITH: Final[str] = "starts_with"
OPERATOR_ENDS_WITH: Final[str] = "ends_with"
OPERATOR_IS_EMPTY: Final[str] = "is_empty"
OPERATOR_IS_NOT_EMPTY: Final[str] = "is_not_empty"

VALID_OPERATORS: Final[tuple[str, ...]] = (
    OPERATOR_EQUALS,
    OPERATOR_NOT_EQUALS,
    OPERATOR_CONTAINS,
    OPERATOR_NOT_CONTAINS,
    OPERATOR_GREATER_THAN,
    OPERATOR_LESS_THAN,
    OPERATOR_STARTS_WITH,
    OPERATOR_ENDS_WITH,
    OPERATOR_IS_EMPTY,
    OPERATOR_IS_NOT_EMPTY,
)

# =============================================================================
# WORKFLOW STATUS
# =============================================================================

STATUS_PENDING: Final[str] = "pending"
STATUS_RUNNING: Final[str] = "running"
STATUS_COMPLETED: Final[str] = "completed"
STATUS_FAILED: Final[str] = "failed"
STATUS_CANCELLED: Final[str] = "cancelled"

TERMINAL_STATUSES: Final[tuple[str, ...]] = (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_CANCELLED,
)

# =============================================================================
# MEMORY SCOPES
# =============================================================================

SCOPE_WORKFLOW: Final[str] = "workflow"
SCOPE_USER: Final[str] = "user"
SCOPE_ORGANIZATION: Final[str] = "organization"
SCOPE_GLOBAL: Final[str] = "global"

VALID_MEMORY_SCOPES: Final[tuple[str, ...]] = (
    SCOPE_WORKFLOW,
    SCOPE_USER,
    SCOPE_ORGANIZATION,
    SCOPE_GLOBAL,
)

# =============================================================================
# TOOL CATEGORIES
# =============================================================================

CATEGORY_SEARCH: Final[str] = "search"
CATEGORY_ANALYSIS: Final[str] = "analysis"
CATEGORY_COMMUNICATION: Final[str] = "communication"
CATEGORY_DATA: Final[str] = "data"
CATEGORY_PRODUCTIVITY: Final[str] = "productivity"
CATEGORY_DEVELOPMENT: Final[str] = "development"
CATEGORY_GENERAL: Final[str] = "general"

# =============================================================================
# API KEY CONFIGURATION
# =============================================================================

# API key prefix for validation
API_KEY_PREFIX: Final[str] = "fib_"
API_KEY_LIVE_PREFIX: Final[str] = "fib_live_"
API_KEY_TEST_PREFIX: Final[str] = "fib_test_"

# =============================================================================
# KEYCHAIN CONFIGURATION
# =============================================================================

# Service name for keychain storage
KEYCHAIN_SERVICE_NAME: Final[str] = "fibonacci-sdk"

# Account name for API key in keychain
KEYCHAIN_API_KEY_ACCOUNT: Final[str] = "api_key"

# =============================================================================
# AUDIT LOGGING
# =============================================================================

# Default log directory (relative to home)
DEFAULT_LOG_DIR: Final[str] = ".fibonacci/logs"

# Log file names
AUDIT_LOG_FILE: Final[str] = "audit.log"
SECURITY_LOG_FILE: Final[str] = "security.log"

# =============================================================================
# HTTP HEADERS
# =============================================================================

HEADER_AUTHORIZATION: Final[str] = "Authorization"
HEADER_CONTENT_TYPE: Final[str] = "Content-Type"
HEADER_USER_AGENT: Final[str] = "User-Agent"

CONTENT_TYPE_JSON: Final[str] = "application/json"

# =============================================================================
# ERROR MESSAGES
# =============================================================================

ERROR_API_KEY_MISSING: Final[str] = (
    "API key is required. Set FIBONACCI_API_KEY environment variable "
    "or provide api_key parameter."
)

ERROR_API_KEY_INVALID_FORMAT: Final[str] = (
    "Invalid API key format. API keys must start with 'fib_'"
)

ERROR_WORKFLOW_NOT_DEPLOYED: Final[str] = (
    "No workflow ID. Deploy workflow first or provide workflow_id parameter."
)

ERROR_TOOL_NOT_FOUND: Final[str] = "Tool '{tool_name}' not found in registry"

# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

ENV_API_KEY: Final[str] = "FIBONACCI_API_KEY"
ENV_BASE_URL: Final[str] = "FIBONACCI_BASE_URL"
ENV_TIMEOUT: Final[str] = "FIBONACCI_TIMEOUT"
ENV_MAX_RETRIES: Final[str] = "FIBONACCI_MAX_RETRIES"
ENV_VERIFY_SSL: Final[str] = "FIBONACCI_VERIFY_SSL"
ENV_DEBUG: Final[str] = "FIBONACCI_DEBUG"
ENV_LOG_REQUESTS: Final[str] = "FIBONACCI_LOG_REQUESTS"
ENV_LOG_RESPONSES: Final[str] = "FIBONACCI_LOG_RESPONSES"

# =============================================================================
# FILE EXTENSIONS
# =============================================================================

YAML_EXTENSIONS: Final[tuple[str, ...]] = (".yaml", ".yml")
CONFIG_FILE_NAME: Final[str] = "config.yaml"
DEFAULT_CONFIG_PATH: Final[str] = "~/.fibonacci/config.yaml"

# =============================================================================
# CRITIC DEFAULTS
# =============================================================================

DEFAULT_EVALUATION_CRITERIA: Final[tuple[str, ...]] = (
    "quality",
    "correctness",
    "completeness",
)

# =============================================================================
# TOOL NODE DEFAULTS
# =============================================================================

DEFAULT_TOOL_TIMEOUT: Final[int] = 30

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Version
    "SDK_VERSION",
    "SDK_NAME",
    # API Configuration
    "DEFAULT_API_URL",
    "API_VERSION",
    "USER_AGENT",
    # Request Defaults
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_RETRY_DELAY",
    "DEFAULT_POLL_INTERVAL",
    "DEFAULT_EXECUTION_TIMEOUT",
    # Model Defaults
    "DEFAULT_MODEL",
    "AVAILABLE_MODELS",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_TEMPERATURE",
    "MIN_TEMPERATURE",
    "MAX_TEMPERATURE",
    # Node Types
    "NODE_TYPE_LLM",
    "NODE_TYPE_TOOL",
    "NODE_TYPE_CRITIC",
    "NODE_TYPE_CONDITION",
    "VALID_NODE_TYPES",
    # Condition Operators
    "OPERATOR_EQUALS",
    "OPERATOR_NOT_EQUALS",
    "OPERATOR_CONTAINS",
    "OPERATOR_NOT_CONTAINS",
    "OPERATOR_GREATER_THAN",
    "OPERATOR_LESS_THAN",
    "OPERATOR_STARTS_WITH",
    "OPERATOR_ENDS_WITH",
    "OPERATOR_IS_EMPTY",
    "OPERATOR_IS_NOT_EMPTY",
    "VALID_OPERATORS",
    # Workflow Status
    "STATUS_PENDING",
    "STATUS_RUNNING",
    "STATUS_COMPLETED",
    "STATUS_FAILED",
    "STATUS_CANCELLED",
    "TERMINAL_STATUSES",
    # Memory Scopes
    "SCOPE_WORKFLOW",
    "SCOPE_USER",
    "SCOPE_ORGANIZATION",
    "SCOPE_GLOBAL",
    "VALID_MEMORY_SCOPES",
    # Tool Categories
    "CATEGORY_SEARCH",
    "CATEGORY_ANALYSIS",
    "CATEGORY_COMMUNICATION",
    "CATEGORY_DATA",
    "CATEGORY_PRODUCTIVITY",
    "CATEGORY_DEVELOPMENT",
    "CATEGORY_GENERAL",
    # API Key
    "API_KEY_PREFIX",
    "API_KEY_LIVE_PREFIX",
    "API_KEY_TEST_PREFIX",
    # Keychain
    "KEYCHAIN_SERVICE_NAME",
    "KEYCHAIN_API_KEY_ACCOUNT",
    # Audit Logging
    "DEFAULT_LOG_DIR",
    "AUDIT_LOG_FILE",
    "SECURITY_LOG_FILE",
    # HTTP
    "HEADER_AUTHORIZATION",
    "HEADER_CONTENT_TYPE",
    "HEADER_USER_AGENT",
    "CONTENT_TYPE_JSON",
    # Error Messages
    "ERROR_API_KEY_MISSING",
    "ERROR_API_KEY_INVALID_FORMAT",
    "ERROR_WORKFLOW_NOT_DEPLOYED",
    "ERROR_TOOL_NOT_FOUND",
    # Environment Variables
    "ENV_API_KEY",
    "ENV_BASE_URL",
    "ENV_TIMEOUT",
    "ENV_MAX_RETRIES",
    "ENV_VERIFY_SSL",
    "ENV_DEBUG",
    "ENV_LOG_REQUESTS",
    "ENV_LOG_RESPONSES",
    # File Extensions
    "YAML_EXTENSIONS",
    "CONFIG_FILE_NAME",
    "DEFAULT_CONFIG_PATH",
    # Critic
    "DEFAULT_EVALUATION_CRITERIA",
    # Tool Node
    "DEFAULT_TOOL_TIMEOUT",
]