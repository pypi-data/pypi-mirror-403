"""
Fibonacci YAML Exporter

Export workflows to YAML format.
"""

from pathlib import Path
from typing import Union

import yaml

from fibonacci.workflow import Workflow


class YAMLExporter:
    """
    Export workflows to YAML files.
    
    Example:
        >>> exporter = YAMLExporter()
        >>> exporter.export(wf, "workflow.yaml")
    """
    
    @staticmethod
    def export(workflow: Workflow, file_path: Union[str, Path]) -> None:
        """
        Export workflow to YAML file.
        
        Args:
            workflow: Workflow to export
            file_path: Path to save YAML file
        
        Example:
            >>> from fibonacci import YAMLExporter
            >>> wf = Workflow(name="Test")
            >>> YAMLExporter.export(wf, "test.yaml")
        """
        path = Path(file_path)
        
        # Create parent directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build YAML structure
        yaml_data = {
            'name': workflow.name,
            'description': workflow.description,
            'version': workflow.version,
            'is_active': workflow.is_active,
        }
        
        # Add tags if present
        if workflow.tags:
            yaml_data['tags'] = workflow.tags
        
        # Add nodes
        nodes_data = []
        for node in workflow.nodes:
            node_dict = YAMLExporter._node_to_yaml(node)
            nodes_data.append(node_dict)
        
        yaml_data['nodes'] = nodes_data
        
        # Write to file with nice formatting
        with open(path, 'w') as f:
            yaml.dump(
                yaml_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
                allow_unicode=True
            )
    
    @staticmethod
    def _node_to_yaml(node) -> dict:
        """Convert node to YAML-friendly dictionary."""
        node_dict = {
            'id': node.id,
            'type': node.type,
            'name': node.name,
        }
        
        # Add dependencies if present
        if node.dependencies:
            node_dict['dependencies'] = node.dependencies
        
        # Type-specific fields
        if node.type == 'llm':
            node_dict['instruction'] = node.instruction
            
            # Add config
            config = {}
            if hasattr(node, 'model'):
                config['model'] = node.model
            if hasattr(node, 'max_tokens'):
                config['max_tokens'] = node.max_tokens
            if hasattr(node, 'temperature'):
                config['temperature'] = node.temperature
            
            # Add retry config if enabled
            if node.enable_retry:
                config['max_retries'] = node.max_retries
                config['retry_delay'] = node.retry_delay
            
            if config:
                node_dict['config'] = config
        
        elif node.type == 'tool':
            node_dict['tool_name'] = node.tool_name
            node_dict['tool_params'] = node.tool_params
            
            # Add config
            config = {}
            if hasattr(node, 'timeout'):
                config['timeout'] = node.timeout
            
            # Add retry config if enabled
            if node.enable_retry:
                config['max_retries'] = node.max_retries
                config['retry_delay'] = node.retry_delay
            
            if config:
                node_dict['config'] = config
        
        elif node.type == 'critic':
            if hasattr(node, 'evaluation_criteria'):
                node_dict['evaluation_criteria'] = node.evaluation_criteria
        
        elif node.type == 'condition':
            node_dict['left_value'] = node.left_value
            node_dict['operator'] = node.operator
            node_dict['right_value'] = node.right_value
            
            if node.true_branch:
                node_dict['true_branch'] = node.true_branch
            if node.false_branch:
                node_dict['false_branch'] = node.false_branch
        
        return node_dict
    
    @staticmethod
    def to_yaml_string(workflow: Workflow) -> str:
        """
        Convert workflow to YAML string.
        
        Args:
            workflow: Workflow to convert
        
        Returns:
            YAML string
        
        Example:
            >>> yaml_str = YAMLExporter.to_yaml_string(wf)
            >>> print(yaml_str)
        """
        yaml_data = {
            'name': workflow.name,
            'description': workflow.description,
            'version': workflow.version,
            'is_active': workflow.is_active,
        }
        
        if workflow.tags:
            yaml_data['tags'] = workflow.tags
        
        nodes_data = []
        for node in workflow.nodes:
            node_dict = YAMLExporter._node_to_yaml(node)
            nodes_data.append(node_dict)
        
        yaml_data['nodes'] = nodes_data
        
        return yaml.dump(
            yaml_data,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
            allow_unicode=True
        )


def export_workflow_to_yaml(workflow: Workflow, file_path: Union[str, Path]) -> None:
    """
    Convenience function to export workflow to YAML.
    
    Args:
        workflow: Workflow to export
        file_path: Path to save YAML file
    
    Example:
        >>> from fibonacci import export_workflow_to_yaml
        >>> export_workflow_to_yaml(wf, "my_workflow.yaml")
    """
    YAMLExporter.export(workflow, file_path)


    __all__ = [
    "YAMLExporter",
    "export_workflow_to_yaml",
]
    

    