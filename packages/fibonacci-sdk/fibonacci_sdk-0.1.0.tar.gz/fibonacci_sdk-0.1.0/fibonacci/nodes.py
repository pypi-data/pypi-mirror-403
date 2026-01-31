"""
Fibonacci Workflow Nodes

Node types for building workflows programmatically.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Node(BaseModel):
    """
    Base class for workflow nodes.
    
    All node types inherit from this base class.
    """
    
    id: str = Field(
        ...,
        description="Unique node identifier (lowercase, underscores)",
        pattern=r"^[a-z][a-z0-9_]*$"
    )
    
    name: str = Field(
        ...,
        description="Human-readable node name"
    )
    
    type: str = Field(
        ...,
        description="Node type (llm, tool, critic, condition)"
    )
    
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of node IDs this node depends on"
    )
    
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Node configuration (model, tokens, retries, timeout, etc.)"
    )
    
    output_key: Optional[str] = Field(
        default=None,
        description="Optional key to store output"
    )
    
    condition: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional condition for conditional execution"
    )
    
    enable_retry: bool = Field(
        default=False,
        description="Enable retry on failure"
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts"
    )
    
    retry_delay: float = Field(
        default=1.0,
        description="Initial retry delay in seconds"
    )
    
    def depends_on(self, *node_ids: str) -> "Node":
        """
        Add dependencies to this node.
        
        Args:
            *node_ids: Node IDs this node depends on
        
        Returns:
            Self for chaining
        
        Example:
            >>> node = LLMNode(...).depends_on("read_doc", "fetch_data")
        """
        self.dependencies.extend(node_ids)
        return self
    
    def with_condition(
        self,
        left_value: str,
        operator: str,
        right_value: str
    ) -> "Node":
        """
        Add a condition to this node.
        
        Args:
            left_value: Left side of condition (can use template variables)
            operator: Comparison operator
            right_value: Right side of condition
        
        Returns:
            Self for chaining
        
        Example:
            >>> node.with_condition("{{sentiment}}", "contains", "positive")
        """
        self.condition = {
            "left_value": left_value,
            "operator": operator,
            "right_value": right_value
        }
        return self
    
    def with_retry(self, max_retries: int = 3, delay: float = 1.0) -> "Node":
        """
        Enable retry on failure.
        
        Args:
            max_retries: Maximum retry attempts
            delay: Initial delay between retries
        
        Returns:
            Self for chaining
        
        Example:
            >>> node.with_retry(max_retries=5, delay=2.0)
        """
        self.enable_retry = True
        self.max_retries = max_retries
        self.retry_delay = delay
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert node to dictionary for API.
        
        Returns:
            Node as dictionary
        """
        data = self.model_dump(exclude_none=True, exclude_unset=True)
        return data


class LLMNode(Node):
    """
    LLM node - calls Claude API with an instruction.
    
    Example:
        >>> analyze = LLMNode(
        ...     id="analyze_sentiment",
        ...     name="Analyze Sentiment",
        ...     instruction="Analyze the sentiment of: {{input.text}}"
        ... )
    """
    
    type: str = Field(default="llm", frozen=True)
    
    instruction: str = Field(
        ...,
        description="Instruction for Claude (can use template variables like {{input.field}} or {{node_id}})"
    )
    
    model: str = Field(
        default="claude-haiku-4-5",
        description="Claude model to use"
    )
    
    max_tokens: int = Field(
        default=2000,
        description="Maximum tokens in response"
    )
    
    temperature: float = Field(
        default=1.0,
        description="Temperature for generation",
        ge=0.0,
        le=1.0
    )
    
    def __init__(self, id: str, name: str, instruction: str, **kwargs: Any):
        """
        Create an LLM node.
        
        Args:
            id: Unique node ID
            name: Human-readable name
            instruction: Instruction for Claude
            **kwargs: Additional parameters (model, max_tokens, temperature)
        """
        super().__init__(
            id=id,
            name=name,
            type="llm",
            instruction=instruction,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert LLM node to dictionary for API.
        
        Groups model, max_tokens, temperature into a 'config' dict.
        
        Returns:
            Node as dictionary with config
        """
        data = self.model_dump(exclude_none=True, exclude_unset=True)
        
        # Build config dict from LLM-specific params
        config = {}
        
        # Move model settings to config
        if "model" in data:
            config["model"] = data.pop("model")
        if "max_tokens" in data:
            config["max_tokens"] = data.pop("max_tokens")
        if "temperature" in data:
            config["temperature"] = data.pop("temperature")
        
        # Merge with any existing config
        if data.get("config"):
            config.update(data["config"])
        
        # Add retry config if enabled
        if data.get("enable_retry"):
            if "max_retries" in data:
                config["max_retries"] = data.pop("max_retries")
            if "retry_delay" in data:
                config["retry_delay"] = data.pop("retry_delay")
            data.pop("enable_retry", None)
        
        # Set the config
        if config:
            data["config"] = config
        
        return data


class ToolNode(Node):
    """
    Tool node - executes a Fibonacci tool.
    
    Example:
        >>> read = ToolNode(
        ...     id="read_doc",
        ...     name="Read Google Doc",
        ...     tool="google_docs_read",
        ...     params={"document_id": "{{input.doc_id}}"}
        ... )
    """
    
    type: str = Field(default="tool", frozen=True)
    
    tool_name: str = Field(
        ...,
        description="Name of the tool to execute"
    )
    
    tool_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the tool (can use template variables like {{input.field}})"
    )
    
    timeout: int = Field(
        default=30,
        description="Tool execution timeout in seconds"
    )
    
    def __init__(
        self,
        id: str,
        name: str,
        tool: str,
        params: Dict[str, Any],
        **kwargs: Any
    ):
        """
        Create a tool node.
        
        Args:
            id: Unique node ID
            name: Human-readable name
            tool: Tool name
            params: Tool parameters
            **kwargs: Additional parameters (timeout, max_retries, etc.)
        """
        super().__init__(
            id=id,
            name=name,
            type="tool",
            tool_name=tool,
            tool_params=params,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool node to dictionary for API.
        
        Groups timeout, retries into a 'config' dict.
        
        Returns:
            Node as dictionary with config
        """
        data = self.model_dump(exclude_none=True, exclude_unset=True)
        
        # Build config dict
        config = {}
        
        # Move timeout to config
        if "timeout" in data:
            config["timeout"] = data.pop("timeout")
        
        # Merge with any existing config
        if data.get("config"):
            config.update(data["config"])
        
        # Add retry config if enabled
        if data.get("enable_retry"):
            if "max_retries" in data:
                config["max_retries"] = data.pop("max_retries")
            if "retry_delay" in data:
                config["retry_delay"] = data.pop("retry_delay")
            data.pop("enable_retry", None)
        
        # Set the config
        if config:
            data["config"] = config
        
        return data


class CriticNode(Node):
    """
    Critic node - evaluates output from another node.
    
    Example:
        >>> critic = CriticNode(
        ...     id="evaluate_report",
        ...     name="Evaluate Report Quality",
        ...     target_node="generate_report",
        ...     criteria=["clarity", "completeness", "accuracy"]
        ... )
    """
    
    type: str = Field(default="critic", frozen=True)
    
    evaluation_criteria: List[str] = Field(
        default_factory=lambda: ["quality", "correctness", "completeness"],
        description="Criteria to evaluate"
    )
    
    def __init__(
        self,
        id: str,
        name: str,
        target_node: str,
        criteria: Optional[List[str]] = None,
        **kwargs: Any
    ):
        """
        Create a critic node.
        
        Args:
            id: Unique node ID
            name: Human-readable name
            target_node: Node ID to evaluate
            criteria: Evaluation criteria
            **kwargs: Additional parameters
        """
        # Critic must depend on the target node
        dependencies = kwargs.pop("dependencies", [])
        if target_node not in dependencies:
            dependencies.append(target_node)
        
        super().__init__(
            id=id,
            name=name,
            type="critic",
            dependencies=dependencies,
            evaluation_criteria=criteria or ["quality", "correctness", "completeness"],
            **kwargs
        )


class ConditionalNode(Node):
    """
    Conditional node - branches workflow based on a condition.
    
    Example:
        >>> condition = ConditionalNode(
        ...     id="check_sentiment",
        ...     name="Check Sentiment Result",
        ...     left_value="{{sentiment}}",
        ...     operator="contains",
        ...     right_value="positive",
        ...     true_branch=["celebrate"],
        ...     false_branch=["investigate"]
        ... )
    """
    
    type: str = Field(default="condition", frozen=True)
    
    left_value: str = Field(
        ...,
        description="Left side of condition (can use template variables like {{node_id}})"
    )
    
    operator: str = Field(
        ...,
        description="Comparison operator"
    )
    
    right_value: str = Field(
        default="",
        description="Right side of condition"
    )
    
    true_branch: List[str] = Field(
        default_factory=list,
        description="Nodes to execute if condition is true"
    )
    
    false_branch: List[str] = Field(
        default_factory=list,
        description="Nodes to execute if condition is false"
    )
    
    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        """Validate operator is supported."""
        valid_operators = [
            "equals", "not_equals", "contains", "not_contains",
            "greater_than", "less_than", "starts_with", "ends_with",
            "is_empty", "is_not_empty"
        ]
        if v not in valid_operators:
            raise ValueError(f"Invalid operator: {v}. Must be one of {valid_operators}")
        return v
    
    def __init__(
        self,
        id: str,
        name: str,
        left_value: str,
        operator: str,
        right_value: str = "",
        true_branch: Optional[List[str]] = None,
        false_branch: Optional[List[str]] = None,
        **kwargs: Any
    ):
        """
        Create a conditional node.
        
        Args:
            id: Unique node ID
            name: Human-readable name
            left_value: Left side of condition
            operator: Comparison operator
            right_value: Right side of condition
            true_branch: Nodes to execute if true
            false_branch: Nodes to execute if false
            **kwargs: Additional parameters
        """
        super().__init__(
            id=id,
            name=name,
            type="condition",
            left_value=left_value,
            operator=operator,
            right_value=right_value,
            true_branch=true_branch or [],
            false_branch=false_branch or [],
            **kwargs
        )


# Type alias for any node type
AnyNode = LLMNode | ToolNode | CriticNode | ConditionalNode


__all__ = [
    # Base
    "Node",
    # Node Types
    "LLMNode",
    "ToolNode",
    "CriticNode",
    "ConditionalNode",
    # Type Alias
    "AnyNode",
]