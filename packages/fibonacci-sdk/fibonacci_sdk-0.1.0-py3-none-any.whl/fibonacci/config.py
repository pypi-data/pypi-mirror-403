"""
Fibonacci SDK Configuration

Manages API keys, base URLs, and SDK settings with enhanced security.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

from fibonacci.exceptions import ConfigurationError


class Config(BaseModel):
    """
    Fibonacci SDK configuration with security enhancements.
    
    Can be loaded from:
    - Environment variables
    - .env file
    - Direct instantiation
    - Config file (~/.fibonacci/config.yaml)
    - Secure keychain (most secure)
    
    Example:
        >>> config = Config(api_key="fib_...")
        >>> config = Config.from_env()
        >>> config = Config.from_file("~/.fibonacci/config.yaml")
    """
    
    api_key: str = Field(
        default="",
        description="Fibonacci API key (required for all operations)"
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
        description="Maximum number of retry attempts for failed requests"
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
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variables.
        
        Args:
            env_file: Path to .env file (optional)
        
        Returns:
            Config instance
        
        Environment variables:
            FIBONACCI_API_KEY: API key
            FIBONACCI_BASE_URL: Base URL (optional)
            FIBONACCI_TIMEOUT: Request timeout (optional)
            FIBONACCI_DEBUG: Enable debug mode (optional)
        """
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
    def from_file(cls, config_path: str) -> "Config":
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config file
        
        Returns:
            Config instance
        """
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
        
        Args:
            config_path: Path to save config file
        """
        import yaml
        
        path = Path(config_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
    
    def validate_ready(self) -> None:
        """
        Validate that config is ready for API calls.
        
        Raises:
            ConfigurationError: If API key is missing
        """
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
        
        # Show first 7 chars and last 3 chars
        prefix = self.api_key[:7]
        suffix = self.api_key[-3:]
        return f"{prefix}***...{suffix}"
    
    def __str__(self) -> str:
        """String representation with redacted API key."""
        return (
            f"Config(\n"
            f"  api_key='{self.get_redacted_api_key()}',\n"
            f"  base_url='{self.base_url}',\n"
            f"  timeout={self.timeout},\n"
            f"  debug={self.debug}\n"
            f")"
        )
    
    def __repr__(self) -> str:
        """Repr with redacted API key."""
        return self.__str__()


# Try to import keychain storage
try:
    from fibonacci.keychain_storage import get_api_key_secure
    KEYCHAIN_AVAILABLE = True
except ImportError:
    KEYCHAIN_AVAILABLE = False


def get_config_secure() -> Config:
    """
    Get configuration with secure credential loading.
    
    Priority:
    1. Keychain (most secure)
    2. Environment variables
    3. .env file
    
    Returns:
        Config instance with API key from most secure source
    
    Example:
        >>> from fibonacci import get_config_secure
        >>> config = get_config_secure()
        >>> # API key loaded from most secure source available
    """
    # Try keychain first
    if KEYCHAIN_AVAILABLE:
        try:
            api_key = get_api_key_secure()
            if api_key:
                config = Config.from_env()
                config.api_key = api_key
                return config
        except Exception:
            pass  # Fall through to env loading
    
    # Fall back to environment
    return Config.from_env()


# Global default config instance
_default_config: Optional[Config] = None


def get_default_config() -> Config:
    """
    Get the global default config.
    
    Loads from environment on first call.
    
    Returns:
        Config instance
    """
    global _default_config
    
    if _default_config is None:
        _default_config = Config.from_env()
    
    return _default_config


def set_default_config(config: Config) -> None:
    """
    Set the global default config.
    
    Args:
        config: Config instance to use as default
    """
    global _default_config
    _default_config = config


__all__ = [
    # Classes
    "Config",
    # Functions
    "get_config_secure",
    "get_default_config",
    "set_default_config",
    # Constants
    "KEYCHAIN_AVAILABLE",
]