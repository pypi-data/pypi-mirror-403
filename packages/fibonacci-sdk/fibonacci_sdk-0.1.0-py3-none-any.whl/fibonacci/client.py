"""
Fibonacci API Client

HTTP client for communicating with Fibonacci platform.
"""

import asyncio
from typing import Any, Dict, Optional, List
from uuid import UUID

import httpx
from pydantic import BaseModel

from fibonacci.config import Config, get_default_config
from fibonacci.exceptions import APIError, AuthenticationError


class WorkflowRunStatus(BaseModel):
    """Status of a workflow run."""
    
    id: str
    workflow_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    total_cost: Optional[float] = None
    nodes_executed: int = 0


class WorkflowStats(BaseModel):
    """Statistics for a specific workflow."""
    
    workflow_id: str
    workflow_name: str
    total_runs: int
    completed_runs: int
    failed_runs: int
    running_now: int
    success_rate: float
    avg_duration_seconds: float
    total_cost: float
    avg_cost: float
    last_run_at: Optional[str] = None
    last_run_status: Optional[str] = None


class FibonacciClient:
    """
    HTTP client for Fibonacci API.
    
    Handles authentication, request/retry logic, and API communication.
    
    Example:
        >>> client = FibonacciClient(api_key="fib_...")
        >>> workflow_id = await client.create_workflow(definition)
        >>> run = await client.execute_workflow(workflow_id, input_data)
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Fibonacci API client.
        
        Args:
            config: Configuration (uses default if not provided)
        """
        self.config = config or get_default_config()
        self.config.validate_ready()
        
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self) -> "FibonacciClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "fibonacci-sdk/0.1.0",
            },
        )
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get HTTP client (create if needed)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "fibonacci-sdk/0.1.0",
                },
            )
        return self._client
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
        
        Returns:
            Response JSON
        
        Raises:
            AuthenticationError: If API key is invalid
            APIError: If request fails
        """
        client = self._get_client()
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                response = await client.request(method, endpoint, **kwargs)
                
                # Handle authentication errors
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                
                # Handle other errors
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    raise APIError(
                        f"API request failed: {error_data.get('detail', response.text)}",
                        status_code=response.status_code,
                        response=error_data,
                    )
                
                return response.json()
                
            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        raise APIError(f"Request failed after {self.config.max_retries} attempts: {last_error}")
    
    # ========================================================================
    # WORKFLOW CRUD OPERATIONS
    # ========================================================================
    
    async def create_workflow(self, definition: Dict[str, Any]) -> str:
        """
        Create a new workflow.
        
        Args:
            definition: Workflow definition
        
        Returns:
            Workflow ID
        """
        response = await self._request(
            "POST",
            "/api/v1/workflows",
            json=definition,
        )
        return response["id"]
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow by ID.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Workflow data
        """
        return await self._request(
            "GET",
            f"/api/v1/workflows/{workflow_id}",
        )
    
    async def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a workflow.
        
        Args:
            workflow_id: Workflow ID
            updates: Fields to update (name, description, definition, is_active)
        
        Returns:
            Updated workflow data
        
        Example:
            >>> await client.update_workflow(
            ...     workflow_id="abc-123",
            ...     updates={"name": "New Name", "is_active": False}
            ... )
        """
        return await self._request(
            "PATCH",
            f"/api/v1/workflows/{workflow_id}",
            json=updates,
        )
    
    async def delete_workflow(self, workflow_id: str) -> None:
        """
        Delete a workflow.
        
        Args:
            workflow_id: Workflow ID
        """
        await self._request(
            "DELETE",
            f"/api/v1/workflows/{workflow_id}",
        )
    
    async def list_workflows(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
    ) -> list[Dict[str, Any]]:
        """
        List workflows.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            is_active: Filter by active status
        
        Returns:
            List of workflows
        """
        params = {"skip": skip, "limit": limit}
        if is_active is not None:
            params["is_active"] = is_active
        
        return await self._request(
            "GET",
            "/api/v1/workflows",
            params=params,
        )
    
    # ========================================================================
    # WORKFLOW STATISTICS
    # ========================================================================
    
    async def get_workflow_stats(self, workflow_id: str) -> WorkflowStats:
        """
        Get statistics for a specific workflow.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Workflow statistics
        
        Example:
            >>> stats = await client.get_workflow_stats("abc-123")
            >>> print(f"Success rate: {stats.success_rate}%")
            >>> print(f"Total cost: ${stats.total_cost:.2f}")
        """
        response = await self._request(
            "GET",
            f"/api/v1/workflows/{workflow_id}/stats",
        )
        return WorkflowStats(**response)
    
    # ========================================================================
    # WORKFLOW EXECUTION
    # ========================================================================
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        tags: Optional[list[str]] = None,
    ) -> WorkflowRunStatus:
        """
        Execute a workflow.
        
        Args:
            workflow_id: Workflow ID
            input_data: Input data for workflow
            tags: Optional tags for run
        
        Returns:
            Workflow run status
        """
        payload = {"input_data": input_data}
        if tags:
            payload["tags"] = tags
        
        response = await self._request(
            "POST",
            f"/api/v1/workflows/{workflow_id}/execute",
            json=payload,
        )
        
        return WorkflowRunStatus(**response)
    
    async def get_run_status(self, run_id: str) -> WorkflowRunStatus:
        """
        Get workflow run status.
        
        Args:
            run_id: Run ID
        
        Returns:
            Run status
        """
        response = await self._request(
            "GET",
            f"/api/v1/runs/{run_id}",
        )
        return WorkflowRunStatus(**response)
    
    async def wait_for_completion(
        self,
        run_id: str,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
    ) -> WorkflowRunStatus:
        """
        Wait for workflow run to complete.
        
        Args:
            run_id: Run ID
            poll_interval: Seconds between status checks
            timeout: Maximum time to wait
        
        Returns:
            Final run status
        
        Raises:
            TimeoutError: If workflow doesn't complete in time
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status = await self.get_run_status(run_id)
            
            if status.status in ["completed", "failed"]:
                return status
            
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Workflow run {run_id} timed out after {timeout}s")
            
            await asyncio.sleep(poll_interval)
    
    # ========================================================================
    # TOOL DISCOVERY
    # ========================================================================
    
    async def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available tools."""
        params = {}
        if category:
            params["category"] = category
        return await self._request("GET", "/api/v1/tools", params=params)

    async def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get tool schema."""
        return await self._request("GET", f"/api/v1/tools/{tool_name}")

    async def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """Search for tools."""
        return await self._request("GET", f"/api/v1/tools/search/{query}")

    async def list_tool_categories(self) -> List[Dict[str, Any]]:
        """List tool categories."""
        return await self._request("GET", "/api/v1/tools/categories")
    
    # ========================================================================
    # CLIENT MANAGEMENT
    # ========================================================================
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


__all__ = [
    # Client
    "FibonacciClient",
    # Response Models
    "WorkflowRunStatus",
    "WorkflowStats",
]