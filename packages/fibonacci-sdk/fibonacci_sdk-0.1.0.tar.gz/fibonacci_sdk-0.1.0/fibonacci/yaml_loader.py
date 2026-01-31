"""
Fibonacci YAML Loader

Load workflow definitions from YAML files.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from fibonacci.workflow import Workflow
from fibonacci.nodes import LLMNode, ToolNode, CriticNode, ConditionalNode
from fibonacci.exceptions import ValidationError


class YAMLLoader:
    """
    Load workflows from YAML files.
    
    Example:
        >>> loader = YAMLLoader()
        >>> wf = loader.load("workflow.yaml")
        >>> wf.deploy()
    """
    
    @staticmethod
    def load(file_path: Union[str, Path]) -> Workflow:
        """
        Load workflow from YAML file.
        
        Args:
            file_path: Path to YAML file
        
        Returns:
            Workflow object
        
        Raises:
            ValidationError: If YAML is invalid
            FileNotFoundError: If file doesn't exist
        
        Example:
            >>> from fibonacci import YAMLLoader
            >>> wf = YAMLLoader.load("my_workflow.yaml")
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {file_path}")
        
        # Load YAML
        with open(path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValidationError(f"Invalid YAML: {e}")
        
        # Validate structure
        YAMLLoader._validate_structure(data)
        
        # Create workflow
        wf = Workflow(
            name=data.get('name', path.stem),
            description=data.get('description', ''),
            version=data.get('version', 1),
            is_active=data.get('is_active', True),
            tags=data.get('tags', [])
        )
        
        # Add nodes
        nodes_data = data.get('nodes', [])
        for node_data in nodes_data:
            node = YAMLLoader._create_node(node_data)
            wf.add_node(node)
        
        return wf
    
    @staticmethod
    def _validate_structure(data: Dict[str, Any]) -> None:
        """Validate YAML structure."""
        if not isinstance(data, dict):
            raise ValidationError("YAML must be a dictionary")
        
        # Check required fields
        if 'nodes' not in data:
            raise ValidationError("YAML must contain 'nodes' field")
        
        if not isinstance(data['nodes'], list):
            raise ValidationError("'nodes' must be a list")
        
        if len(data['nodes']) == 0:
            raise ValidationError("Workflow must have at least one node")
        
        # Validate each node
        for i, node in enumerate(data['nodes']):
            if not isinstance(node, dict):
                raise ValidationError(f"Node {i} must be a dictionary")
            
            if 'id' not in node:
                raise ValidationError(f"Node {i} missing required field 'id'")
            
            if 'type' not in node:
                raise ValidationError(f"Node {i} missing required field 'type'")
    
    @staticmethod
    def _create_node(node_data: Dict[str, Any]):
        """Create node from YAML data."""
        node_type = node_data.get('type')
        node_id = node_data.get('id')
        name = node_data.get('name', node_id)
        dependencies = node_data.get('dependencies', [])
        
        # Get config if present
        config = node_data.get('config', {})
        
        # Extract common config fields
        max_retries = config.get('max_retries')
        retry_delay = config.get('retry_delay')
        enable_retry = max_retries is not None
        
        if node_type == 'llm':
            return YAMLLoader._create_llm_node(node_data, node_id, name, dependencies, config, enable_retry, max_retries, retry_delay)
        
        elif node_type == 'tool':
            return YAMLLoader._create_tool_node(node_data, node_id, name, dependencies, config, enable_retry, max_retries, retry_delay)
        
        elif node_type == 'critic':
            return YAMLLoader._create_critic_node(node_data, node_id, name, dependencies)
        
        elif node_type == 'condition':
            return YAMLLoader._create_conditional_node(node_data, node_id, name, dependencies)
        
        else:
            raise ValidationError(f"Unknown node type: {node_type}")
    
    @staticmethod
    def _create_llm_node(node_data, node_id, name, dependencies, config, enable_retry, max_retries, retry_delay):
        """Create LLM node from YAML."""
        instruction = node_data.get('instruction')
        if not instruction:
            raise ValidationError(f"LLM node '{node_id}' missing 'instruction'")
        
        node = LLMNode(
            id=node_id,
            name=name,
            instruction=instruction,
            model=config.get('model', 'claude-haiku-4-5'),
            max_tokens=config.get('max_tokens', 2000),
            temperature=config.get('temperature', 1.0),
        )
        
        node.dependencies = dependencies
        
        if enable_retry:
            node.enable_retry = True
            if max_retries:
                node.max_retries = max_retries
            if retry_delay:
                node.retry_delay = retry_delay
        
        return node
    
    @staticmethod
    def _create_tool_node(node_data, node_id, name, dependencies, config, enable_retry, max_retries, retry_delay):
        """Create Tool node from YAML."""
        tool_name = node_data.get('tool_name')
        if not tool_name:
            raise ValidationError(f"Tool node '{node_id}' missing 'tool_name'")
        
        tool_params = node_data.get('tool_params', {})
        
        node = ToolNode(
            id=node_id,
            name=name,
            tool=tool_name,
            params=tool_params,
            timeout=config.get('timeout', 30),
        )
        
        node.dependencies = dependencies
        
        if enable_retry:
            node.enable_retry = True
            if max_retries:
                node.max_retries = max_retries
            if retry_delay:
                node.retry_delay = retry_delay
        
        return node
    
    @staticmethod
    def _create_critic_node(node_data, node_id, name, dependencies):
        """Create Critic node from YAML."""
        evaluation_criteria = node_data.get('evaluation_criteria', ['quality', 'correctness', 'completeness'])
        
        # Critic needs at least one dependency (the node to evaluate)
        if not dependencies:
            raise ValidationError(f"Critic node '{node_id}' must have at least one dependency")
        
        target_node = dependencies[0]  # First dependency is the target
        
        node = CriticNode(
            id=node_id,
            name=name,
            target_node=target_node,
            criteria=evaluation_criteria,
        )
        
        return node
    
    @staticmethod
    def _create_conditional_node(node_data, node_id, name, dependencies):
        """Create Conditional node from YAML."""
        left_value = node_data.get('left_value')
        operator = node_data.get('operator')
        right_value = node_data.get('right_value', '')
        
        if not left_value:
            raise ValidationError(f"Conditional node '{node_id}' missing 'left_value'")
        if not operator:
            raise ValidationError(f"Conditional node '{node_id}' missing 'operator'")
        
        true_branch = node_data.get('true_branch', [])
        false_branch = node_data.get('false_branch', [])
        
        node = ConditionalNode(
            id=node_id,
            name=name,
            left_value=left_value,
            operator=operator,
            right_value=right_value,
            true_branch=true_branch,
            false_branch=false_branch,
        )
        
        node.dependencies = dependencies
        
        return node


def load_workflow_from_yaml(file_path: Union[str, Path]) -> Workflow:
    """
    Convenience function to load workflow from YAML.
    
    Args:
        file_path: Path to YAML file
    
    Returns:
        Workflow object
    
    Example:
        >>> from fibonacci import load_workflow_from_yaml
        >>> wf = load_workflow_from_yaml("workflow.yaml")
        >>> wf.deploy()
    """
    return YAMLLoader.load(file_path)

__all__ = [
    "YAMLLoader",
    "load_workflow_from_yaml",
]


