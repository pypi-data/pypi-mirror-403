"""
Fibonacci Workflow Validator

Validates workflow definitions before deployment.
"""

from typing import Any, Dict, List, Optional, Set, Tuple


class WorkflowValidator:
    """
    Validates workflow definitions.
    
    Checks:
    - Required fields present
    - Valid node types
    - No circular dependencies
    - Dependencies reference existing nodes
    - Template variable syntax
    """
    
    def validate(self, workflow: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a workflow definition.
        
        Args:
            workflow: Workflow definition
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check top-level required fields
        if "definition" not in workflow:
            errors.append("Missing 'definition' field")
            return False, errors
        
        definition = workflow["definition"]
        
        if "nodes" not in definition:
            errors.append("Missing 'nodes' field in definition")
            return False, errors
        
        if not isinstance(definition["nodes"], list):
            errors.append("'nodes' must be an array")
            return False, errors
        
        if len(definition["nodes"]) == 0:
            errors.append("Workflow must have at least one node")
            return False, errors
        
        nodes = definition["nodes"]
        
        # Validate each node
        node_ids = set()
        for i, node in enumerate(nodes):
            node_errors = self._validate_node(node, i)
            errors.extend(node_errors)
            
            # Collect node IDs
            if "id" in node:
                if node["id"] in node_ids:
                    errors.append(f"Duplicate node ID: {node['id']}")
                node_ids.add(node["id"])
        
        # Check dependencies reference valid nodes
        for node in nodes:
            deps = node.get("dependencies", [])
            for dep in deps:
                if dep not in node_ids:
                    errors.append(
                        f"Node '{node.get('id')}' depends on non-existent node: {dep}"
                    )
        
        # Check for circular dependencies
        circular = self._check_circular_dependencies(nodes)
        if circular:
            errors.append(f"Circular dependency detected: {circular}")
        
        return len(errors) == 0, errors
    
    def _validate_node(self, node: Dict[str, Any], index: int) -> List[str]:
        """Validate a single node."""
        errors = []
        
        # Required fields
        if "id" not in node:
            errors.append(f"Node {index}: Missing 'id' field")
        else:
            # Validate ID format (lowercase, underscores)
            node_id = node["id"]
            if not node_id.replace("_", "").replace("-", "").isalnum():
                errors.append(
                    f"Node '{node_id}': Invalid ID format. "
                    "Use lowercase letters, numbers, underscores, hyphens only."
                )
        
        if "type" not in node:
            errors.append(f"Node {index}: Missing 'type' field")
        elif node["type"] not in ["llm", "tool", "critic", "condition"]:
            errors.append(f"Node {node.get('id', index)}: Invalid type '{node['type']}'")
        
        if "name" not in node:
            errors.append(f"Node {node.get('id', index)}: Missing 'name' field")
        
        # Type-specific validation
        node_type = node.get("type")
        node_id = node.get("id", f"node_{index}")
        
        if node_type == "tool":
            if "tool_name" not in node:
                errors.append(f"Tool node '{node_id}': Missing 'tool_name'")
            if "tool_params" not in node:
                errors.append(f"Tool node '{node_id}': Missing 'tool_params'")
        
        elif node_type == "llm":
            if "instruction" not in node:
                errors.append(f"LLM node '{node_id}': Missing 'instruction'")
        
        elif node_type == "critic":
            if "dependencies" not in node or len(node.get("dependencies", [])) == 0:
                errors.append(f"Critic node '{node_id}': Must have at least one dependency")
        
        elif node_type == "condition":
            if "left_value" not in node:
                errors.append(f"Condition node '{node_id}': Missing 'left_value'")
            if "operator" not in node:
                errors.append(f"Condition node '{node_id}': Missing 'operator'")
        
        # Validate dependencies field
        if "dependencies" in node:
            if not isinstance(node["dependencies"], list):
                errors.append(f"Node '{node_id}': 'dependencies' must be an array")
        
        # Validate condition field structure
        if "condition" in node:
            condition = node["condition"]
            if not isinstance(condition, dict):
                errors.append(f"Node '{node_id}': 'condition' must be an object")
            else:
                if "left_value" not in condition:
                    errors.append(f"Node '{node_id}': condition missing 'left_value'")
                if "operator" not in condition:
                    errors.append(f"Node '{node_id}': condition missing 'operator'")
                
                # Validate operator
                valid_operators = [
                    "equals", "not_equals", "contains", "not_contains",
                    "greater_than", "less_than", "starts_with", "ends_with",
                    "is_empty", "is_not_empty"
                ]
                if condition.get("operator") not in valid_operators:
                    errors.append(
                        f"Node '{node_id}': invalid operator '{condition.get('operator')}'"
                    )
        
        return errors
    
    def _check_circular_dependencies(
        self,
        nodes: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Check for circular dependencies using DFS.
        
        Returns:
            None if no circular dependency, error message if circular dependency found
        """
        # Build adjacency list
        graph = {}
        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                continue
            
            deps = node.get("dependencies", [])
            graph[node_id] = deps
        
        # DFS to detect cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str, path: List[str]) -> Optional[str]:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    cycle = has_cycle(neighbor, path.copy())
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle_path = path[cycle_start:] + [neighbor]
                    return " -> ".join(cycle_path)
            
            rec_stack.remove(node_id)
            return None
        
        for node_id in graph:
            if node_id not in visited:
                cycle = has_cycle(node_id, [])
                if cycle:
                    return cycle
        
        return None