"""
Decorators for Lyzr SDK

Provides @tool decorator for registering local functions as agent tools.
"""

from typing import Callable, Dict, Any, Optional
import inspect

# Global registry for decorated tools
_TOOL_REGISTRY: Dict[str, 'Tool'] = {}


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
):
    """
    Decorator to register a function as a local tool

    Automatically infers name, description, and parameters from the function
    if not explicitly provided.

    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        parameters: JSON schema for parameters (defaults to inferred from type hints)

    Returns:
        Decorated function (unchanged)

    Examples:
        # Minimal - everything inferred automatically!
        @tool()
        def read_file(file_path: str) -> str:
            '''Read a file from local filesystem'''
            with open(file_path) as f:
                return f.read()

        # Name: "read_file" (from function name)
        # Description: "Read a file from local filesystem" (from docstring)
        # Parameters: {"file_path": {"type": "string"}} (from type hints)

        # Explicit - override any inferred value
        @tool(
            name="custom_reader",
            description="Advanced file reader with special handling"
        )
        def read_file(file_path: str) -> str:
            with open(file_path) as f:
                return f.read()

        # Hybrid - provide only what you need
        @tool(description="Read file with caching")
        def read_file(file_path: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        from lyzr.tools import Tool

        # Infer tool name (default to function name)
        tool_name = name or func.__name__

        # Infer description (default to docstring or generic message)
        if description:
            tool_description = description
        elif func.__doc__:
            tool_description = func.__doc__.strip()
        else:
            tool_description = f"Execute {func.__name__}"

        # Infer parameters from function signature if not provided
        if parameters is None:
            tool_parameters = infer_parameters_from_function(func)
        else:
            tool_parameters = parameters

        # Create Tool instance
        tool_instance = Tool(
            name=tool_name,
            description=tool_description,
            parameters=tool_parameters,
            function=func
        )

        # Register in global registry
        _TOOL_REGISTRY[tool_name] = tool_instance

        # Return original function (decorator doesn't modify behavior)
        return func

    return decorator


def infer_parameters_from_function(func: Callable) -> Dict[str, Any]:
    """
    Infer JSON schema parameters from function signature

    Uses Python type hints to build parameter schema automatically.

    Args:
        func: Function to analyze

    Returns:
        Dict: JSON schema for function parameters

    Example:
        def my_func(name: str, age: int, active: bool = True):
            pass

        schema = infer_parameters_from_function(my_func)
        # Returns:
        # {
        #     "type": "object",
        #     "properties": {
        #         "name": {"type": "string"},
        #         "age": {"type": "integer"},
        #         "active": {"type": "boolean"}
        #     },
        #     "required": ["name", "age"]
        # }
    """
    sig = inspect.signature(func)
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        # Skip self and cls
        if param_name in ('self', 'cls'):
            continue

        # Infer type from annotation
        param_type = _infer_json_type(param.annotation)
        properties[param_name] = {"type": param_type}

        # Check if required (no default value)
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required
    }


def _infer_json_type(annotation) -> str:
    """
    Infer JSON schema type from Python type annotation

    Args:
        annotation: Python type annotation

    Returns:
        str: JSON schema type (string, integer, number, boolean, array, object)
    """
    # No annotation
    if annotation == inspect.Parameter.empty:
        return "string"

    # Direct type mapping
    if annotation == str:
        return "string"
    elif annotation == int:
        return "integer"
    elif annotation == float:
        return "number"
    elif annotation == bool:
        return "boolean"
    elif annotation == list:
        return "array"
    elif annotation == dict:
        return "object"

    # Handle typing module types
    annotation_str = str(annotation)

    if "list" in annotation_str.lower() or "List" in annotation_str:
        return "array"
    elif "dict" in annotation_str.lower() or "Dict" in annotation_str:
        return "object"

    # Default to string for unknown types
    return "string"


def get_registered_tools() -> Dict[str, 'Tool']:
    """
    Get all tools registered with @tool decorator

    Returns:
        Dict[str, Tool]: Dictionary mapping tool names to Tool instances

    Example:
        @tool()
        def my_tool(): pass

        tools = get_registered_tools()
        print(tools.keys())  # ['my_tool']
    """
    return _TOOL_REGISTRY.copy()


def clear_tools():
    """
    Clear all registered tools from global registry

    Useful for testing or resetting state.

    Example:
        clear_tools()
        assert len(get_registered_tools()) == 0
    """
    _TOOL_REGISTRY.clear()
