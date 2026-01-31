"""
Fibonacci Workflow Builder

Programmatically build and deploy workflows.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fibonacci.client import FibonacciClient, WorkflowRunStatus, WorkflowStats
from fibonacci.config import Config, get_default_config
from fibonacci.exceptions import ValidationError, DeploymentError, ExecutionError
from fibonacci.nodes import Node, AnyNode
from fibonacci.validators import WorkflowValidator


class Workflow:
    """
    Workflow builder for creating and deploying workflows programmatically.
    
    Example:
        >>> from fibonacci import Workflow, LLMNode, ToolNode
        >>> 
        >>> wf = Workflow(
        ...     name="Sales Report Generator",
        ...     description="Automated sales reporting"
        ... )
        >>> 
        >>> # Add nodes
        >>> read = ToolNode(
        ...     id="read_data",
        ...     name="Read Sales Data",
        ...     tool="google_sheets_read",
        ...     params={"spreadsheet_id": "{{input.sheet_id}}"}
        ... )
        >>> 
        >>> analyze = LLMNode(
        ...     id="analyze",
        ...     name="Analyze Data",
        ...     instruction="Analyze this sales data: {{read_data}}",
        ...     dependencies=["read_data"]
        ... )
        >>> 
        >>> wf.add_nodes([read, analyze])
        >>> 
        >>> # Deploy to Fibonacci platform
        >>> wf.deploy(api_key="fib_...")
        >>> 
        >>> # Execute
        >>> result = wf.run(input_data={"sheet_id": "abc123"})
        >>> print(result.output_data)
        >>> 
        >>> # Get statistics
        >>> stats = wf.get_stats()
        >>> print(f"Success rate: {stats.success_rate}%")
        >>> 
        >>> # Update workflow
        >>> wf.update(name="Updated Sales Report")
        >>> 
        >>> # Deactivate
        >>> wf.deactivate()
        >>> 
        >>> # Export to YAML
        >>> wf.to_yaml("workflow.yaml")
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        version: int = 1,
        is_active: bool = True,
        tags: Optional[List[str]] = None,
        config: Optional[Config] = None,
    ):
        """
        Create a new workflow.
        
        Args:
            name: Workflow name
            description: Workflow description
            version: Workflow version
            is_active: Whether workflow is active
            tags: Optional tags
            config: SDK configuration (uses default if not provided)
        """
        self.name = name
        self.description = description
        self.version = version
        self.is_active = is_active
        self.tags = tags or []
        self.config = config or get_default_config()
        
        self._nodes: List[Node] = []
        self._workflow_id: Optional[str] = None
        self._validator = WorkflowValidator()
    
    def add_node(self, node: AnyNode) -> "Workflow":
        """
        Add a single node to the workflow.
        
        Args:
            node: Node to add
        
        Returns:
            Self for chaining
        
        Example:
            >>> wf.add_node(read).add_node(analyze)
        """
        self._nodes.append(node)
        return self
    
    def add_nodes(self, nodes: List[AnyNode]) -> "Workflow":
        """
        Add multiple nodes to the workflow.
        
        Args:
            nodes: List of nodes to add
        
        Returns:
            Self for chaining
        
        Example:
            >>> wf.add_nodes([read, analyze, send])
        """
        self._nodes.extend(nodes)
        return self
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Get a node by ID.
        
        Args:
            node_id: Node ID
        
        Returns:
            Node or None if not found
        """
        for node in self._nodes:
            if node.id == node_id:
                return node
        return None
    
    def remove_node(self, node_id: str) -> "Workflow":
        """
        Remove a node by ID.
        
        Args:
            node_id: Node ID to remove
        
        Returns:
            Self for chaining
        """
        self._nodes = [n for n in self._nodes if n.id != node_id]
        return self
    
    def validate(self) -> None:
        """
        Validate the workflow.
        
        Raises:
            ValidationError: If workflow is invalid
        """
        definition = self.to_dict()
        is_valid, errors = self._validator.validate(definition)
        
        if not is_valid:
            raise ValidationError(
                "Workflow validation failed",
                errors=errors
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert workflow to dictionary for API.
        
        Returns:
            Workflow definition as dictionary
        """
        # Build edges from dependencies
        edges = []
        for node in self._nodes:
            for dep in node.dependencies:
                edges.append({"from": dep, "to": node.id})
        
        workflow_dict = {
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "definition": {
                "name": self.name,
                "version": self.version,
                "nodes": [node.to_dict() for node in self._nodes],
                "edges": edges,
            }
        }
        
        # Only include tags if not empty
        if self.tags:
            workflow_dict["tags"] = self.tags
        
        return workflow_dict
    
    # ========================================================================
    # YAML SUPPORT (NEW)
    # ========================================================================
    
    @classmethod
    def from_yaml(cls, file_path: Union[str, Path], config: Optional[Config] = None) -> "Workflow":
        """
        Load workflow from YAML file.
        
        Args:
            file_path: Path to YAML file
            config: SDK configuration (optional)
        
        Returns:
            Workflow instance
        
        Example:
            >>> wf = Workflow.from_yaml("workflow.yaml")
            >>> wf.deploy()
            >>> 
            >>> # Or with custom config
            >>> config = Config(api_key="fib_live_xxx")
            >>> wf = Workflow.from_yaml("workflow.yaml", config=config)
        """
        from fibonacci.yaml_loader import YAMLLoader
        
        wf = YAMLLoader.load(file_path)
        
        # Override config if provided
        if config:
            wf.config = config
        
        return wf
    
    def to_yaml(self, file_path: Union[str, Path]) -> None:
        """
        Export workflow to YAML file.
        
        Args:
            file_path: Path to save YAML file
        
        Example:
            >>> wf = Workflow(name="Test")
            >>> wf.add_node(LLMNode(...))
            >>> wf.to_yaml("exported_workflow.yaml")
        """
        from fibonacci.yaml_exporter import YAMLExporter
        
        YAMLExporter.export(self, file_path)
    
    def to_yaml_string(self) -> str:
        """
        Convert workflow to YAML string.
        
        Returns:
            YAML string
        
        Example:
            >>> wf = Workflow(name="Test")
            >>> wf.add_node(LLMNode(...))
            >>> yaml_str = wf.to_yaml_string()
            >>> print(yaml_str)
        """
        from fibonacci.yaml_exporter import YAMLExporter
        
        return YAMLExporter.to_yaml_string(self)
    
    # ========================================================================
    # DEPLOYMENT
    # ========================================================================
    
    async def deploy_async(
        self,
        api_key: Optional[str] = None,
        validate: bool = True
    ) -> str:
        """
        Deploy workflow to Fibonacci platform (async).
        
        Args:
            api_key: API key (uses config default if not provided)
            validate: Whether to validate before deploying
        
        Returns:
            Workflow ID
        
        Raises:
            ValidationError: If validation fails
            DeploymentError: If deployment fails
        """
        # Validate if requested
        if validate:
            self.validate()
        
        # Update config with API key if provided
        config = self.config
        if api_key:
            config = Config(**config.model_dump())
            config.api_key = api_key
        
        # Deploy via API
        async with FibonacciClient(config) as client:
            try:
                workflow_data = self.to_dict()
                workflow_id = await client.create_workflow(workflow_data)
                self._workflow_id = workflow_id
                return workflow_id
            except Exception as e:
                raise DeploymentError(
                    f"Failed to deploy workflow: {e}",
                    workflow_name=self.name
                )
    
    def deploy(
        self,
        api_key: Optional[str] = None,
        validate: bool = True
    ) -> str:
        """
        Deploy workflow to Fibonacci platform (sync wrapper).
        
        Args:
            api_key: API key (uses config default if not provided)
            validate: Whether to validate before deploying
        
        Returns:
            Workflow ID
        """
        return asyncio.run(self.deploy_async(api_key, validate))
    
    # ========================================================================
    # WORKFLOW MANAGEMENT
    # ========================================================================
    
    async def update_async(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update workflow on platform (async).
        
        Args:
            name: New name (optional)
            description: New description (optional)
            is_active: New active status (optional)
            workflow_id: Workflow ID (uses last deployed if not provided)
        
        Returns:
            Updated workflow data
        
        Raises:
            ExecutionError: If workflow not deployed or update fails
        
        Example:
            >>> await wf.update_async(name="New Name", is_active=False)
        """
        wf_id = workflow_id or self._workflow_id
        
        if not wf_id:
            raise ExecutionError(
                "No workflow ID. Deploy workflow first or provide workflow_id parameter."
            )
        
        # Build updates dictionary
        updates = {}
        if name is not None:
            updates["name"] = name
            self.name = name
        if description is not None:
            updates["description"] = description
            self.description = description
        if is_active is not None:
            updates["is_active"] = is_active
            self.is_active = is_active
        
        if not updates:
            raise ValueError("No updates provided")
        
        async with FibonacciClient(self.config) as client:
            try:
                return await client.update_workflow(wf_id, updates)
            except Exception as e:
                raise ExecutionError(f"Failed to update workflow: {e}")
    
    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update workflow on platform (sync wrapper).
        
        Args:
            name: New name (optional)
            description: New description (optional)
            is_active: New active status (optional)
            workflow_id: Workflow ID (uses last deployed if not provided)
        
        Returns:
            Updated workflow data
        
        Example:
            >>> wf.update(name="Production Pipeline", is_active=True)
        """
        return asyncio.run(
            self.update_async(name, description, is_active, workflow_id)
        )
    
    async def delete_async(self, workflow_id: Optional[str] = None) -> None:
        """
        Delete workflow from platform (async).
        
        Args:
            workflow_id: Workflow ID (uses last deployed if not provided)
        
        Raises:
            ExecutionError: If workflow not deployed or delete fails
        
        Example:
            >>> await wf.delete_async()
        """
        wf_id = workflow_id or self._workflow_id
        
        if not wf_id:
            raise ExecutionError(
                "No workflow ID. Deploy workflow first or provide workflow_id parameter."
            )
        
        async with FibonacciClient(self.config) as client:
            try:
                await client.delete_workflow(wf_id)
                self._workflow_id = None  # Clear local ID
            except Exception as e:
                raise ExecutionError(f"Failed to delete workflow: {e}")
    
    def delete(self, workflow_id: Optional[str] = None) -> None:
        """
        Delete workflow from platform (sync wrapper).
        
        Args:
            workflow_id: Workflow ID (uses last deployed if not provided)
        
        Example:
            >>> wf.delete()
        """
        asyncio.run(self.delete_async(workflow_id))
    
    async def get_stats_async(
        self,
        workflow_id: Optional[str] = None
    ) -> WorkflowStats:
        """
        Get workflow statistics (async).
        
        Args:
            workflow_id: Workflow ID (uses last deployed if not provided)
        
        Returns:
            Workflow statistics
        
        Raises:
            ExecutionError: If workflow not deployed or stats fetch fails
        
        Example:
            >>> stats = await wf.get_stats_async()
            >>> print(f"Success rate: {stats.success_rate}%")
        """
        wf_id = workflow_id or self._workflow_id
        
        if not wf_id:
            raise ExecutionError(
                "No workflow ID. Deploy workflow first or provide workflow_id parameter."
            )
        
        async with FibonacciClient(self.config) as client:
            try:
                return await client.get_workflow_stats(wf_id)
            except Exception as e:
                raise ExecutionError(f"Failed to get workflow stats: {e}")
    
    def get_stats(self, workflow_id: Optional[str] = None) -> WorkflowStats:
        """
        Get workflow statistics (sync wrapper).
        
        Args:
            workflow_id: Workflow ID (uses last deployed if not provided)
        
        Returns:
            Workflow statistics
        
        Example:
            >>> stats = wf.get_stats()
            >>> print(f"Total runs: {stats.total_runs}")
            >>> print(f"Success rate: {stats.success_rate}%")
            >>> print(f"Average cost: ${stats.avg_cost:.4f}")
        """
        return asyncio.run(self.get_stats_async(workflow_id))
    
    def activate(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Activate workflow.
        
        Args:
            workflow_id: Workflow ID (uses last deployed if not provided)
        
        Returns:
            Updated workflow data
        
        Example:
            >>> wf.activate()
        """
        return self.update(is_active=True, workflow_id=workflow_id)
    
    def deactivate(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Deactivate workflow.
        
        Args:
            workflow_id: Workflow ID (uses last deployed if not provided)
        
        Returns:
            Updated workflow data
        
        Example:
            >>> wf.deactivate()
        """
        return self.update(is_active=False, workflow_id=workflow_id)
    
    # ========================================================================
    # EXECUTION
    # ========================================================================
    
    async def run_async(
        self,
        input_data: Dict[str, Any],
        workflow_id: Optional[str] = None,
        wait: bool = True,
        timeout: float = 300.0,
    ) -> WorkflowRunStatus:
        """
        Execute the workflow (async).
        
        Args:
            input_data: Input data for workflow
            workflow_id: Workflow ID (uses last deployed if not provided)
            wait: Whether to wait for completion
            timeout: Maximum time to wait for completion
        
        Returns:
            Workflow run status
        
        Raises:
            ExecutionError: If execution fails
        """
        wf_id = workflow_id or self._workflow_id
        
        if not wf_id:
            raise ExecutionError(
                "No workflow ID. Deploy workflow first or provide workflow_id parameter."
            )
        
        async with FibonacciClient(self.config) as client:
            try:
                # Start execution
                run_status = await client.execute_workflow(wf_id, input_data)
                
                # Wait for completion if requested
                if wait:
                    run_status = await client.wait_for_completion(
                        run_status.id,
                        timeout=timeout
                    )
                    
                    # Check if failed
                    if run_status.status == "failed":
                        raise ExecutionError(
                            f"Workflow execution failed: {run_status.error_message}",
                            run_id=run_status.id,
                        )
                
                return run_status
                
            except Exception as e:
                if isinstance(e, ExecutionError):
                    raise
                raise ExecutionError(f"Failed to execute workflow: {e}")
    
    def run(
        self,
        input_data: Dict[str, Any],
        workflow_id: Optional[str] = None,
        wait: bool = True,
        timeout: float = 300.0,
    ) -> WorkflowRunStatus:
        """
        Execute the workflow (sync wrapper).
        
        Args:
            input_data: Input data for workflow
            workflow_id: Workflow ID (uses last deployed if not provided)
            wait: Whether to wait for completion
            timeout: Maximum time to wait for completion
        
        Returns:
            Workflow run status
        """
        return asyncio.run(
            self.run_async(input_data, workflow_id, wait, timeout)
        )
    
    async def get_status_async(self, run_id: str) -> WorkflowRunStatus:
        """
        Get workflow run status (async).
        
        Args:
            run_id: Run ID
        
        Returns:
            Run status
        """
        async with FibonacciClient(self.config) as client:
            return await client.get_run_status(run_id)
    
    def get_status(self, run_id: str) -> WorkflowRunStatus:
        """
        Get workflow run status (sync wrapper).
        
        Args:
            run_id: Run ID
        
        Returns:
            Run status
        """
        return asyncio.run(self.get_status_async(run_id))
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def workflow_id(self) -> Optional[str]:
        """Get the deployed workflow ID."""
        return self._workflow_id
    
    @property
    def nodes(self) -> List[Node]:
        """Get list of nodes."""
        return self._nodes.copy()
    
    @property
    def node_count(self) -> int:
        """Get number of nodes."""
        return len(self._nodes)
    
    def __repr__(self) -> str:
        """String representation."""
        deployed = f" (deployed: {self._workflow_id})" if self._workflow_id else ""
        return f"<Workflow '{self.name}' with {self.node_count} nodes{deployed}>"
    

__all__ = [
    "Workflow",
]


