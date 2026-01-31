"""
Fibonacci SDK - Memory Client

Client for interacting with memory storage.
"""

import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID

from fibonacci.client import FibonacciClient
from fibonacci.config import Config, get_default_config


class Memory:
    """
    Memory client for persistent storage.
    
    Supports multiple scopes:
    - workflow: Scoped to a specific workflow
    - user: Scoped to a user
    - organization: Scoped to entire organization
    - global: System-wide (admin only)
    
    Examples:
        # Workflow memory
        memory = Memory(scope="workflow", workflow_id=workflow.workflow_id)
        memory.set("last_output", result)
        last = memory.get("last_output")
        
        # User preferences
        memory = Memory(scope="user", user_id="user-123")
        memory.set("preferences", {"theme": "dark"})
        
        # Conversation history
        memory = Memory(scope="workflow", workflow_id=wf.workflow_id)
        history = memory.get("conversation", default=[])
        history.append({"user": "hello", "bot": "hi!"})
        memory.set("conversation", history)
    """
    
    def __init__(
        self,
        scope: str = "workflow",
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        config: Optional[Config] = None
    ):
        """
        Initialize memory client.
        
        Args:
            scope: Memory scope (workflow, user, organization, global)
            workflow_id: Workflow ID (for workflow scope)
            user_id: User ID (for user scope)
            organization_id: Organization ID (for org scope)
            config: SDK configuration
        """
        self.scope = scope
        self.workflow_id = workflow_id
        self.user_id = user_id
        self.organization_id = organization_id
        self.config = config or get_default_config()
        self._client: Optional[FibonacciClient] = None
    
    def _get_client(self) -> FibonacciClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = FibonacciClient(self.config)
        return self._client
    
    async def get_async(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        Get a memory value (async).
        
        Args:
            key: Memory key
            default: Default value if not found
        
        Returns:
            Memory value or default
        """
        params = {
            "scope": self.scope,
        }
        
        if self.workflow_id:
            params["workflow_id"] = str(self.workflow_id)
        if self.user_id:
            params["user_id"] = str(self.user_id)
        if self.organization_id:
            params["organization_id"] = str(self.organization_id)
        
        try:
            # Create fresh client for each request
            async with FibonacciClient(self.config) as client:
                response = await client._request(
                    "GET",
                    f"/api/v1/memory/{key}",
                    params=params
                )
                return response.get("value", default)
        except Exception as e:
            print(f"Debug - Get error: {e}")
            return default
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a memory value (sync wrapper).
        
        Args:
            key: Memory key
            default: Default value if not found
        
        Returns:
            Memory value or default
        """
        return asyncio.run(self.get_async(key, default))
    
    async def set_async(
        self,
        key: str,
        value: Any,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        expires_in_hours: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Set a memory value (async).
        
        Args:
            key: Memory key
            value: Value to store (must be JSON-serializable)
            description: Optional description
            expires_in_days: Expiration in days
            expires_in_hours: Expiration in hours
            tags: Optional tags
        
        Returns:
            Memory object
        """
        payload = {
            "key": key,
            "value": value,
            "scope": self.scope,
        }
        
        if self.workflow_id:
            payload["workflow_id"] = self.workflow_id
        if self.user_id:
            payload["user_id"] = self.user_id
        if self.organization_id:
            payload["organization_id"] = self.organization_id
        if description:
            payload["description"] = description
        if expires_in_days:
            payload["expires_in_days"] = expires_in_days
        if expires_in_hours:
            payload["expires_in_hours"] = expires_in_hours
        if tags:
            payload["tags"] = tags
        
        async with FibonacciClient(self.config) as client:
            response = await client._request(
                "POST",
                "/api/v1/memory",
                json=payload
            )
            return response
    
    def set(
        self,
        key: str,
        value: Any,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        expires_in_hours: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Set a memory value (sync wrapper).
        
        Args:
            key: Memory key
            value: Value to store
            description: Optional description
            expires_in_days: Expiration in days
            expires_in_hours: Expiration in hours
            tags: Optional tags
        
        Returns:
            Memory object
        """
        return asyncio.run(
            self.set_async(key, value, description, expires_in_days, expires_in_hours, tags)
        )
    
    async def delete_async(self, key: str, hard_delete: bool = False) -> bool:
        """Delete a memory (async)."""
        params = {
            "scope": self.scope,
            "hard_delete": hard_delete
        }
        
        if self.workflow_id:
            params["workflow_id"] = str(self.workflow_id)
        if self.user_id:
            params["user_id"] = str(self.user_id)
        if self.organization_id:
            params["organization_id"] = str(self.organization_id)
        
        try:
            async with FibonacciClient(self.config) as client:
                await client._request(
                    "DELETE",
                    f"/api/v1/memory/{key}",
                    params=params
                )
                return True
        except Exception:
            return False
    
    def delete(self, key: str, hard_delete: bool = False) -> bool:
        """Delete a memory (sync wrapper)."""
        return asyncio.run(self.delete_async(key, hard_delete))
    
    async def list_async(
        self,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List memories (async)."""
        payload = {
            "scope": self.scope,
            "limit": limit
        }
        
        if self.workflow_id:
            payload["workflow_id"] = self.workflow_id
        if self.user_id:
            payload["user_id"] = self.user_id
        if self.organization_id:
            payload["organization_id"] = self.organization_id
        if prefix:
            payload["prefix"] = prefix
        if tags:
            payload["tags"] = tags
        
        async with FibonacciClient(self.config) as client:
            response = await client._request(
                "POST",
                "/api/v1/memory/list",
                json=payload
            )
            return response
    
    def list(
        self,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List memories (sync wrapper).
        
        Args:
            prefix: Filter by key prefix
            tags: Filter by tags
            limit: Maximum results
        
        Returns:
            List of memory objects
        """
        return asyncio.run(self.list_async(prefix, tags, limit))
    
    async def search_async(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search memories (async)."""
        payload = {
            "query": query,
            "scope": self.scope,
            "limit": limit
        }
        
        if self.workflow_id:
            payload["workflow_id"] = self.workflow_id
        if self.user_id:
            payload["user_id"] = self.user_id
        if self.organization_id:
            payload["organization_id"] = self.organization_id
        
        async with FibonacciClient(self.config) as client:
            response = await client._request(
                "POST",
                "/api/v1/memory/search",
                json=payload
            )
            return response
    
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search memories (sync wrapper).
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching memories
        """
        return asyncio.run(self.search_async(query, limit))
    
    def remember(self, key: str, value: Any, **kwargs):
        """
        Alias for set() - more intuitive naming.
        
        Example:
            memory.remember("last_conversation", chat_history)
        """
        return self.set(key, value, **kwargs)
    
    def recall(self, key: str, default: Any = None) -> Any:
        """
        Alias for get() - more intuitive naming.
        
        Example:
            history = memory.recall("last_conversation", default=[])
        """
        return self.get(key, default)
    
    def forget(self, key: str) -> bool:
        """
        Alias for delete() - more intuitive naming.
        
        Example:
            memory.forget("temporary_data")
        """
        return self.delete(key)
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, *args):
        """Context manager cleanup."""
        if self._client:
            asyncio.run(self._client.close())
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Memory(scope='{self.scope}')>"
    
__all__ = [
    "Memory",
]
