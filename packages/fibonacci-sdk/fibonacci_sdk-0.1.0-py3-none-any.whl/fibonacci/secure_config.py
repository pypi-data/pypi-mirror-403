"""
Fibonacci SDK - Secure Configuration

Enhanced configuration with API key redaction and secure storage.
"""

import os
import re
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

from fibonacci.exceptions import ConfigurationError


class SecureConfig(BaseModel):
    """
    Secure configuration with API key redaction.
    
    Automatically redacts API keys in string representations.
    
    Example:
        >>> config = SecureConfig(api_key="fib_live_abc123xyz")
        >>> print(config)  # Shows: api_key='fib_***...xyz'
        >>> config.api_key  # Still returns full key for use
    """
    
    api_key: str = Field(
        default="",
        description="Fibonacci API key (automatically redacted in logs)"
    )
    
    base_url: str = Field(
        default="https://api.fibonacci.today",
        description="Fibonacci API base URL"
    )
    
    timeout: int = Field(
        default=300,
        description="Request timeout in seconds"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts"
    )
    
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug logging"
    )
    
    # Security settings
    log_requests: bool = Field(
        default=False,
        description="Log all API requests (keys will be redacted)"
    )
    
    log_responses: bool = Field(
        default=False,
        description="Log all API responses (sensitive data will be masked)"
    )
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if v and not v.startswith("fib_"):
            raise ConfigurationError(
                "Invalid API key format. API keys must start with 'fib_'"
            )
        return v
    
    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Ensure base URL doesn't end with slash."""
        return v.rstrip("/")
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "SecureConfig":
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        return cls(
            api_key=os.getenv("FIBONACCI_API_KEY", ""),
            base_url=os.getenv("FIBONACCI_BASE_URL", "https://api.fibonacci.today"),
            timeout=int(os.getenv("FIBONACCI_TIMEOUT", "300")),
            max_retries=int(os.getenv("FIBONACCI_MAX_RETRIES", "3")),
            verify_ssl=os.getenv("FIBONACCI_VERIFY_SSL", "true").lower() == "true",
            debug=os.getenv("FIBONACCI_DEBUG", "false").lower() == "true",
            log_requests=os.getenv("FIBONACCI_LOG_REQUESTS", "false").lower() == "true",
            log_responses=os.getenv("FIBONACCI_LOG_RESPONSES", "false").lower() == "true",
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> "SecureConfig":
        """Load configuration from YAML file."""
        import yaml
        
        path = Path(config_path).expanduser()
        
        if not path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")
        
        with open(path) as f:
            data = yaml.safe_load(f)
        
        return cls(**data)
    
    def save(self, config_path: str = "~/.fibonacci/config.yaml") -> None:
        """
        Save configuration to YAML file.
        
        WARNING: This saves the API key in plaintext!
        Consider using keychain storage instead.
        """
        import yaml
        
        path = Path(config_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
    
    def validate_ready(self) -> None:
        """Validate that config is ready for API calls."""
        if not self.api_key:
            raise ConfigurationError(
                "API key is required. Set FIBONACCI_API_KEY environment variable "
                "or provide api_key parameter."
            )
    
    def get_redacted_api_key(self) -> str:
        """
        Get redacted version of API key for logging.
        
        Returns:
            Redacted key like "fib_***...xyz"
        """
        if not self.api_key:
            return "<not set>"
        
        if len(self.api_key) <= 10:
            return "fib_***"
        
        # Show first 4 chars and last 3 chars
        prefix = self.api_key[:7]  # "fib_liv" or "fib_tes"
        suffix = self.api_key[-3:]
        return f"{prefix}***...{suffix}"
    
    def __str__(self) -> str:
        """String representation with redacted API key."""
        return (
            f"SecureConfig(\n"
            f"  api_key='{self.get_redacted_api_key()}',\n"
            f"  base_url='{self.base_url}',\n"
            f"  timeout={self.timeout},\n"
            f"  debug={self.debug}\n"
            f")"
        )
    
    def __repr__(self) -> str:
        """Repr with redacted API key."""
        return self.__str__()
    
    def model_dump_safe(self) -> dict:
        """
        Dump model with redacted API key.
        
        Use this for logging instead of model_dump().
        """
        data = self.model_dump()
        data["api_key"] = self.get_redacted_api_key()
        return data


def redact_api_key(text: str) -> str:
    """
    Redact API keys in text.
    
    Useful for sanitizing logs, error messages, etc.
    
    Args:
        text: Text that might contain API keys
    
    Returns:
        Text with API keys redacted
    
    Example:
        >>> log = "Using key: fib_live_abc123xyz"
        >>> redacted = redact_api_key(log)
        >>> print(redacted)
        >>> # Output: "Using key: fib_***...xyz"
    """
    # Pattern: fib_[live|test]_[alphanumeric]
    pattern = r'fib_(live|test)_[a-zA-Z0-9]+'
    
    def replace_key(match):
        key = match.group(0)
        if len(key) <= 10:
            return "fib_***"
        prefix = key[:7]
        suffix = key[-3:]
        return f"{prefix}***...{suffix}"
    
    return re.sub(pattern, replace_key, text)


def redact_sensitive_data(data: dict) -> dict:
    """
    Redact sensitive data from dictionary.
    
    Redacts common sensitive fields like:
    - api_key, apiKey, API_KEY
    - password, token, secret
    - authorization, auth
    
    Args:
        data: Dictionary that might contain sensitive data
    
    Returns:
        Dictionary with sensitive fields redacted
    
    Example:
        >>> response = {"api_key": "fib_live_xxx", "result": "data"}
        >>> safe = redact_sensitive_data(response)
        >>> print(safe)
        >>> # Output: {"api_key": "fib_***...xxx", "result": "data"}
    """
    sensitive_keys = {
        'api_key', 'apikey', 'api-key', 'apiKey', 'API_KEY',
        'password', 'passwd', 'pwd',
        'token', 'access_token', 'refresh_token',
        'secret', 'client_secret',
        'authorization', 'auth',
        'key', 'private_key',
    }
    
    redacted = {}
    for key, value in data.items():
        key_lower = key.lower().replace('_', '').replace('-', '')
        
        # Check if key is sensitive
        is_sensitive = any(sens in key_lower for sens in sensitive_keys)
        
        if is_sensitive and isinstance(value, str):
            # Redact the value
            if value.startswith("fib_"):
                redacted[key] = redact_api_key(value)
            elif len(value) > 8:
                redacted[key] = f"{value[:3]}***...{value[-2:]}"
            else:
                redacted[key] = "***"
        elif isinstance(value, dict):
            # Recursively redact nested dicts
            redacted[key] = redact_sensitive_data(value)
        elif isinstance(value, list):
            # Redact items in lists
            redacted[key] = [
                redact_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            redacted[key] = value
    
    return redacted


# Backward compatibility - SecureConfig is drop-in replacement for Config
Config = SecureConfig


# Global default config instance
_default_config: Optional[SecureConfig] = None


def get_default_config() -> SecureConfig:
    """Get the global default config."""
    global _default_config
    
    if _default_config is None:
        _default_config = SecureConfig.from_env()
    
    return _default_config


def set_default_config(config: SecureConfig) -> None:
    """Set the global default config."""
    global _default_config
    _default_config = config


__all__ = [
    # Classes
    "SecureConfig",
    "Config",  # Alias for backward compatibility
    # Functions
    "redact_api_key",
    "redact_sensitive_data",
    "get_default_config",
    "set_default_config",
]


