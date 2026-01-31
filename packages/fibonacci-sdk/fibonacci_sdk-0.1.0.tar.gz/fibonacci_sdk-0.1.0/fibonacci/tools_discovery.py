"""
Fibonacci SDK - Tool Discovery

Convenience functions for discovering and exploring available tools.
"""

import asyncio
from typing import Any, Dict, List, Optional

from fibonacci.client import FibonacciClient
from fibonacci.config import Config, get_default_config


def list_tools(api_key: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all available tools (sync).
    
    Args:
        api_key: Optional API key (uses config default if not provided)
        category: Optional category filter (e.g., "search", "analysis")
    
    Returns:
        List of tools with metadata
    
    Example:
        >>> from fibonacci import list_tools
        >>> 
        >>> # List all tools
        >>> tools = list_tools(api_key="fib_live_xxx")
        >>> for tool in tools:
        ...     print(f"{tool['name']}: {tool['description']}")
        ...     print(f"  Category: {tool['category']}")
        ...     print(f"  Cost: ${tool['cost_per_use']:.4f}")
        >>> 
        >>> # Filter by category
        >>> search_tools = list_tools(category="search")
    """
    config = get_default_config()
    if api_key:
        # Create new config with provided API key
        config = Config(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            verify_ssl=config.verify_ssl,
            debug=config.debug
        )
    
    async def _list():
        async with FibonacciClient(config) as client:
            return await client.list_tools(category=category)
    
    return asyncio.run(_list())


def get_tool_schema(tool_name: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get detailed schema for a specific tool (sync).
    
    Args:
        tool_name: Name of the tool (e.g., "web_search")
        api_key: Optional API key
    
    Returns:
        Tool schema including input parameters, examples, and configuration
    
    Example:
        >>> from fibonacci import get_tool_schema
        >>> 
        >>> schema = get_tool_schema("web_search")
        >>> 
        >>> # View input parameters
        >>> print("Parameters:")
        >>> for param, info in schema["input_schema"]["properties"].items():
        ...     print(f"  - {param}: {info['type']}")
        ...     print(f"    {info['description']}")
        >>> 
        >>> # View examples
        >>> if "examples" in schema:
        ...     for example in schema["examples"]:
        ...         print(f"Example: {example['description']}")
        ...         print(f"  Params: {example['params']}")
    """
    config = get_default_config()
    if api_key:
        config = Config(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            verify_ssl=config.verify_ssl,
            debug=config.debug
        )
    
    async def _get():
        async with FibonacciClient(config) as client:
            return await client.get_tool_schema(tool_name)
    
    return asyncio.run(_get())


def search_tools(query: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for tools by name or description (sync).
    
    Args:
        query: Search query (e.g., "google", "analyze", "sheet")
        api_key: Optional API key
    
    Returns:
        List of matching tools sorted by relevance
    
    Example:
        >>> from fibonacci import search_tools
        >>> 
        >>> # Search for Google-related tools
        >>> tools = search_tools("google")
        >>> for tool in tools:
        ...     print(f"{tool['name']} (relevance: {tool['relevance']:.1f})")
        ...     print(f"  {tool['description']}")
        >>> 
        >>> # Use the best match
        >>> best_tool = tools[0]
        >>> print(f"Best match: {best_tool['name']}")
    """
    config = get_default_config()
    if api_key:
        config = Config(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            verify_ssl=config.verify_ssl,
            debug=config.debug
        )
    
    async def _search():
        async with FibonacciClient(config) as client:
            return await client.search_tools(query)
    
    return asyncio.run(_search())


def list_tool_categories(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all tool categories with counts (sync).
    
    Args:
        api_key: Optional API key
    
    Returns:
        List of categories with tool counts
    
    Example:
        >>> from fibonacci import list_tool_categories
        >>> 
        >>> categories = list_tool_categories()
        >>> for cat in categories:
        ...     print(f"{cat['name']}: {cat['count']} tools")
        ...     print(f"  Examples: {', '.join(cat['tools'][:3])}")
    """
    config = get_default_config()
    if api_key:
        config = Config(
            api_key=api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            verify_ssl=config.verify_ssl,
            debug=config.debug
        )
    
    async def _list_categories():
        async with FibonacciClient(config) as client:
            return await client.list_tool_categories()
    
    return asyncio.run(_list_categories())


# Utility function to help developers discover tools dynamically
def find_tool_for_task(task_description: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Find the best tool for a given task description.
    
    Uses search to find relevant tools and returns the highest-ranked match.
    
    Args:
        task_description: Natural language description of the task
        api_key: Optional API key
    
    Returns:
        Tool name or None if no match found
    
    Example:
        >>> from fibonacci import find_tool_for_task
        >>> 
        >>> tool = find_tool_for_task("I need to search the web")
        >>> print(f"Best tool: {tool}")
        >>> # Output: "web_search"
        >>> 
        >>> tool = find_tool_for_task("analyze sentiment of text")
        >>> print(f"Best tool: {tool}")
        >>> # Output: "text_analysis"
    """
    results = search_tools(task_description, api_key=api_key)
    
    if results and len(results) > 0:
        # Return the highest relevance tool
        return results[0]['name']
    
    return None


def print_tool_info(tool_name: str, api_key: Optional[str] = None) -> None:
    """
    Print formatted information about a tool.
    
    Useful for exploring tools in interactive Python sessions.
    
    Args:
        tool_name: Name of the tool
        api_key: Optional API key
    
    Example:
        >>> from fibonacci import print_tool_info
        >>> 
        >>> print_tool_info("web_search")
        >>> # Prints formatted tool information
    """
    schema = get_tool_schema(tool_name, api_key=api_key)
    
    print("=" * 70)
    print(f"🔧 {schema['name']}")
    print("=" * 70)
    print(f"Category: {schema['category']}")
    print(f"Description: {schema['description']}")
    print(f"Cost per use: ${schema['cost_per_use']:.4f}")
    print()
    
    # Input parameters
    print("📥 Input Parameters:")
    input_schema = schema.get('input_schema', {})
    properties = input_schema.get('properties', {})
    required = input_schema.get('required', [])
    
    for param_name, param_info in properties.items():
        is_required = "required" if param_name in required else "optional"
        param_type = param_info.get('type', 'unknown')
        description = param_info.get('description', 'No description')
        
        print(f"  • {param_name} ({param_type}) - {is_required}")
        print(f"    {description}")
        
        if 'default' in param_info:
            print(f"    Default: {param_info['default']}")
        print()
    
    # Examples
    if 'examples' in schema and schema['examples']:
        print("📖 Examples:")
        for i, example in enumerate(schema['examples'], 1):
            print(f"  {i}. {example.get('description', 'Example')}")
            print(f"     Params: {example.get('params', {})}")
            if 'expected_output' in example:
                print(f"     Output: {example['expected_output']}")
            print()
    
    # Configuration
    if 'config_schema' in schema and schema['config_schema']:
        print("⚙️  Configuration Options:")
        config_props = schema['config_schema'].get('properties', {})
        for config_name, config_info in config_props.items():
            print(f"  • {config_name}: {config_info.get('description', 'No description')}")
            if 'default' in config_info:
                print(f"    Default: {config_info['default']}")
    
    print("=" * 70)


__all__ = [
    "list_tools",
    "get_tool_schema",
    "search_tools",
    "list_tool_categories",
    "find_tool_for_task",
    "print_tool_info",
]


