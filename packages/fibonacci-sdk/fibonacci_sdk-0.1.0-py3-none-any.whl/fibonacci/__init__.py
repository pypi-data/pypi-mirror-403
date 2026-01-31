"""
Fibonacci SDK - Python client for Fibonacci Workflow Automation Platform

Build and deploy AI-powered workflows programmatically with enterprise-grade security.

Example:
    >>> from fibonacci import Workflow, LLMNode, ToolNode
    >>> 
    >>> wf = Workflow(name="Sales Report")
    >>> 
    >>> read = ToolNode(
    ...     id="read_data",
    ...     tool="google_sheets_read",
    ...     params={"spreadsheet_id": "{{input.sheet_id}}"}
    ... )
    >>> 
    >>> analyze = LLMNode(
    ...     id="analyze",
    ...     instruction="Analyze this data: {{read_data}}",
    ...     dependencies=["read_data"]
    ... )
    >>> 
    >>> wf.add_nodes([read, analyze])
    >>> wf.deploy(api_key="your-key")
    >>> result = wf.run(input_data={"sheet_id": "abc123"})

YAML Support:
    >>> # Load workflow from YAML
    >>> wf = Workflow.from_yaml("workflow.yaml")
    >>> wf.deploy()
    >>> 
    >>> # Export workflow to YAML
    >>> wf.to_yaml("exported.yaml")

Security Features:
    >>> from fibonacci import (
    ...     save_api_key_secure,
    ...     enable_audit_logging,
    ...     check_security_status
    ... )
    >>> 
    >>> # Save API key to encrypted keychain
    >>> save_api_key_secure("fib_live_your_key")
    >>> 
    >>> # Enable comprehensive audit logging
    >>> enable_audit_logging()
    >>> 
    >>> # Check security status
    >>> status = check_security_status()
"""

from fibonacci.workflow import Workflow
from fibonacci.nodes import LLMNode, ToolNode, CriticNode, ConditionalNode
from fibonacci.client import FibonacciClient
from fibonacci.config import Config, get_config_secure
from fibonacci.exceptions import (
    FibonacciError,
    AuthenticationError,
    ValidationError,
    ExecutionError,
)
from fibonacci.memory import Memory

# Tool Discovery imports
from fibonacci.tools_discovery import (
    list_tools,
    get_tool_schema,
    search_tools,
    list_tool_categories,
    find_tool_for_task,
    print_tool_info,
)

# Security imports
from fibonacci.secure_config import (
    SecureConfig,
    redact_api_key,
    redact_sensitive_data,
)

# Audit logging imports
from fibonacci.audit_logging import (
    AuditLogger,
    enable_audit_logging,
    disable_audit_logging,
    get_audit_logger,
)

# YAML imports
from fibonacci.yaml_loader import (
    YAMLLoader,
    load_workflow_from_yaml,
)
from fibonacci.yaml_exporter import (
    YAMLExporter,
    export_workflow_to_yaml,
)

# Keychain storage imports (optional - graceful fallback)
try:
    from fibonacci.keychain_storage import (
        KeychainStorage,
        get_api_key_secure,
        save_api_key_secure,
        migrate_to_keychain,
        check_security_status,
    )
    _KEYCHAIN_AVAILABLE = True
except ImportError:
    _KEYCHAIN_AVAILABLE = False
    # Provide stub functions that explain keyring is not installed
    def _keyring_not_available(*args, **kwargs):
        raise ImportError(
            "Keyring not installed. Install with: pip install keyring\n"
            "Or install full security features: pip install fibonacci[security]"
        )
    
    KeychainStorage = _keyring_not_available
    get_api_key_secure = _keyring_not_available
    save_api_key_secure = _keyring_not_available
    migrate_to_keychain = _keyring_not_available
    check_security_status = lambda: {
        "keyring_available": False,
        "security_level": "low",
        "recommendation": "Install keyring: pip install keyring"
    }

__version__ = "0.1.0"
__all__ = [
    # Core
    "Workflow",
    "FibonacciClient",
    "Config",
    "get_config_secure",
    # Nodes
    "LLMNode",
    "ToolNode",
    "CriticNode",
    "ConditionalNode",
    # Exceptions
    "FibonacciError",
    "AuthenticationError",
    "ValidationError",
    "ExecutionError",
    # Utilities
    "Memory",
    # Tool Discovery
    "list_tools",
    "get_tool_schema",
    "search_tools",
    "list_tool_categories",
    "find_tool_for_task",
    "print_tool_info",
    # Security - Config & Redaction
    "SecureConfig",
    "redact_api_key",
    "redact_sensitive_data",
    # Security - Keychain Storage
    "KeychainStorage",
    "get_api_key_secure",
    "save_api_key_secure",
    "migrate_to_keychain",
    "check_security_status",
    # Security - Audit Logging
    "AuditLogger",
    "enable_audit_logging",
    "disable_audit_logging",
    "get_audit_logger",
    # YAML Support
    "YAMLLoader",
    "YAMLExporter",
    "load_workflow_from_yaml",
    "export_workflow_to_yaml",
]