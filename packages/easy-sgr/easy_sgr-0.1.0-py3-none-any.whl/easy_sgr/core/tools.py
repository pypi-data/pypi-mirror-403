"""Tool decorator and utilities for creating SGR agent tools."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Callable, ClassVar, TypeVar

from pydantic import Field, create_model

from easy_sgr.sgr_agent_core.base_tool import BaseTool

if TYPE_CHECKING:
    from easy_sgr.sgr_agent_core.agent_definition import AgentConfig
    from easy_sgr.sgr_agent_core.models import AgentContext


F = TypeVar("F", bound=Callable)


def tool(func: F) -> type[BaseTool]:
    """Decorator to convert a function into a BaseTool class.
    
    The function docstring becomes the tool description.
    Function parameters with type hints become Pydantic fields.
    
    Example:
        @tool
        def add_numbers(a: int, b: int) -> int:
            '''Adds two numbers together.
            
            Args:
                a: First number
                b: Second number
            '''
            return a + b
    
    Args:
        func: Function to convert into a tool
        
    Returns:
        BaseTool subclass wrapping the function
    """
    # Get function signature
    sig = inspect.signature(func)
    func_name = func.__name__
    func_doc = inspect.getdoc(func) or f"Tool for {func_name}"
    
    # Extract parameters and create Pydantic fields
    fields = {}
    for param_name, param in sig.parameters.items():
        # Skip special parameters
        if param_name in ("self", "cls", "context", "config"):
            continue
            
        # Get type annotation
        annotation = param.annotation if param.annotation != inspect.Parameter.empty else str
        
        # Get default value
        default = ... if param.default == inspect.Parameter.empty else param.default
        
        # Create Field with description from docstring if available
        fields[param_name] = (annotation, Field(default=default, description=f"Parameter {param_name}"))
    
    # Create Pydantic model for the tool
    tool_model = create_model(
        f"{func_name.title().replace('_', '')}Tool",
        __base__=BaseTool,
        **fields
    )
    
    # Set class variables
    tool_model.tool_name = func_name
    tool_model.description = func_doc
    
    # Store reference to original function in closure
    original_func = func
    
    # Override __call__ to execute the original function
    async def __call__(self, context: AgentContext, config: AgentConfig, **kwargs) -> str:
        # Extract field values from the model instance
        field_values = {
            field_name: getattr(self, field_name)
            for field_name in fields.keys()
        }
        
        # Call the original function
        if inspect.iscoroutinefunction(original_func):
            result = await original_func(**field_values)
        else:
            result = original_func(**field_values)
        
        # Convert result to string
        if isinstance(result, str):
            return result
        return str(result)
    
    # Bind the new __call__ method
    tool_model.__call__ = __call__
    
    return tool_model
