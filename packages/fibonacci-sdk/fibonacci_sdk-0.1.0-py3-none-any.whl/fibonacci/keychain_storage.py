"""
Fibonacci SDK - Secure Keychain Storage

OS-level encrypted credential storage using system keychain.

Supports:
- macOS Keychain
- Windows Credential Manager  
- Linux Secret Service (via keyring)
"""

import os
import sys
from typing import Optional

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class KeychainStorage:
    """
    Secure credential storage using OS keychain.
    
    Stores API keys encrypted in system keychain instead of plaintext .env files.
    
    Example:
        >>> from fibonacci import KeychainStorage
        >>> 
        >>> # Save API key securely
        >>> keychain = KeychainStorage()
        >>> keychain.set_api_key("fib_live_abc123")
        >>> 
        >>> # Retrieve it later
        >>> api_key = keychain.get_api_key()
        >>> print(f"Retrieved: {api_key[:10]}...")
    """
    
    SERVICE_NAME = "fibonacci-sdk"
    API_KEY_ACCOUNT = "api_key"
    
    def __init__(self):
        """Initialize keychain storage."""
        if not KEYRING_AVAILABLE:
            raise ImportError(
                "keyring library not installed. Install with: pip install keyring"
            )
        
        self.backend = keyring.get_keyring()
    
    def set_api_key(self, api_key: str) -> None:
        """
        Store API key in system keychain.
        
        Args:
            api_key: Fibonacci API key (fib_live_xxx or fib_test_xxx)
        
        Raises:
            ValueError: If API key format is invalid
        
        Example:
            >>> keychain = KeychainStorage()
            >>> keychain.set_api_key("fib_live_abc123xyz")
        """
        if not api_key.startswith("fib_"):
            raise ValueError("Invalid API key format. Must start with 'fib_'")
        
        keyring.set_password(
            self.SERVICE_NAME,
            self.API_KEY_ACCOUNT,
            api_key
        )
    
    def get_api_key(self) -> Optional[str]:
        """
        Retrieve API key from system keychain.
        
        Returns:
            API key or None if not found
        
        Example:
            >>> keychain = KeychainStorage()
            >>> api_key = keychain.get_api_key()
            >>> if api_key:
            ...     print("Found API key!")
        """
        return keyring.get_password(
            self.SERVICE_NAME,
            self.API_KEY_ACCOUNT
        )
    
    def delete_api_key(self) -> None:
        """
        Delete API key from keychain.
        
        Example:
            >>> keychain = KeychainStorage()
            >>> keychain.delete_api_key()
        """
        try:
            keyring.delete_password(
                self.SERVICE_NAME,
                self.API_KEY_ACCOUNT
            )
        except keyring.errors.PasswordDeleteError:
            pass  # Already deleted or doesn't exist
    
    def is_available(self) -> bool:
        """
        Check if keychain storage is available.
        
        Returns:
            True if keychain is available and working
        """
        try:
            # Try to set and get a test value
            test_key = "test_key"
            test_value = "test_value"
            
            keyring.set_password(self.SERVICE_NAME, test_key, test_value)
            result = keyring.get_password(self.SERVICE_NAME, test_key)
            keyring.delete_password(self.SERVICE_NAME, test_key)
            
            return result == test_value
        except Exception:
            return False
    
    def get_backend_info(self) -> dict:
        """
        Get information about the keychain backend.
        
        Returns:
            Dictionary with backend details
        """
        return {
            "backend": str(self.backend),
            "platform": sys.platform,
            "available": self.is_available()
        }
    
    @staticmethod
    def is_keyring_installed() -> bool:
        """Check if keyring library is installed."""
        return KEYRING_AVAILABLE


def get_api_key_secure() -> Optional[str]:
    """
    Get API key from most secure source available.
    
    Priority:
    1. System keychain (most secure)
    2. Environment variable
    3. .env file
    
    Returns:
        API key or None if not found
    
    Example:
        >>> from fibonacci import get_api_key_secure
        >>> api_key = get_api_key_secure()
        >>> if api_key:
        ...     print("Found API key securely!")
    """
    # Try keychain first (most secure)
    if KEYRING_AVAILABLE:
        try:
            keychain = KeychainStorage()
            api_key = keychain.get_api_key()
            if api_key:
                return api_key
        except Exception:
            pass  # Fall through to env vars
    
    # Try environment variable
    api_key = os.getenv("FIBONACCI_API_KEY")
    if api_key:
        return api_key
    
    # Try .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("FIBONACCI_API_KEY")
        if api_key:
            return api_key
    except ImportError:
        pass
    
    return None


def save_api_key_secure(api_key: str) -> bool:
    """
    Save API key to most secure storage available.
    
    Args:
        api_key: Fibonacci API key
    
    Returns:
        True if saved successfully
    
    Example:
        >>> from fibonacci import save_api_key_secure
        >>> success = save_api_key_secure("fib_live_abc123")
        >>> if success:
        ...     print("API key saved securely!")
    """
    if not api_key.startswith("fib_"):
        raise ValueError("Invalid API key format")
    
    # Try keychain first
    if KEYRING_AVAILABLE:
        try:
            keychain = KeychainStorage()
            keychain.set_api_key(api_key)
            return True
        except Exception:
            pass  # Fall through to env file
    
    # Fall back to .env file (less secure)
    try:
        env_path = ".env"
        
        # Read existing .env
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
        
        # Update or add API key
        found = False
        for i, line in enumerate(lines):
            if line.startswith("FIBONACCI_API_KEY="):
                lines[i] = f"FIBONACCI_API_KEY={api_key}\n"
                found = True
                break
        
        if not found:
            lines.append(f"FIBONACCI_API_KEY={api_key}\n")
        
        # Write back
        with open(env_path, "w") as f:
            f.writelines(lines)
        
        return True
    except Exception:
        return False


def migrate_to_keychain() -> bool:
    """
    Migrate API key from .env file to secure keychain.
    
    Returns:
        True if migration successful
    
    Example:
        >>> from fibonacci import migrate_to_keychain
        >>> if migrate_to_keychain():
        ...     print("Migrated API key to keychain!")
        ...     print("You can now delete it from .env file")
    """
    if not KEYRING_AVAILABLE:
        print("⚠️  Keyring not available. Install with: pip install keyring")
        return False
    
    # Get API key from env
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("FIBONACCI_API_KEY")
    
    if not api_key:
        print("❌ No API key found in environment")
        return False
    
    # Save to keychain
    try:
        keychain = KeychainStorage()
        keychain.set_api_key(api_key)
        print("✅ API key migrated to secure keychain!")
        print("📝 You can now remove FIBONACCI_API_KEY from .env file")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def check_security_status() -> dict:
    """
    Check security status of credential storage.
    
    Returns:
        Dictionary with security information
    
    Example:
        >>> from fibonacci import check_security_status
        >>> status = check_security_status()
        >>> print(f"Security level: {status['security_level']}")
    """
    status = {
        "keyring_available": KEYRING_AVAILABLE,
        "keyring_working": False,
        "api_key_in_keychain": False,
        "api_key_in_env": False,
        "security_level": "unknown"
    }
    
    # Check keyring
    if KEYRING_AVAILABLE:
        try:
            keychain = KeychainStorage()
            status["keyring_working"] = keychain.is_available()
            status["api_key_in_keychain"] = keychain.get_api_key() is not None
        except Exception:
            pass
    
    # Check environment
    from dotenv import load_dotenv
    load_dotenv()
    status["api_key_in_env"] = os.getenv("FIBONACCI_API_KEY") is not None
    
    # Determine security level
    if status["api_key_in_keychain"]:
        status["security_level"] = "high"  # Encrypted in keychain
    elif status["api_key_in_env"]:
        status["security_level"] = "low"  # Plaintext in .env
    else:
        status["security_level"] = "none"  # No API key found
    
    return status


__all__ = [
    # Classes
    "KeychainStorage",
    # Functions
    "get_api_key_secure",
    "save_api_key_secure",
    "migrate_to_keychain",
    "check_security_status",
    # Constants
    "KEYRING_AVAILABLE",
]

