"""Agent creation and execution utilities."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from easy_sgr.sgr_agent_core.agent_definition import AgentDefinition
from easy_sgr.sgr_agent_core.agent_factory import AgentFactory
from easy_sgr.sgr_agent_core.agents.sgr_agent import SGRAgent
from easy_sgr.sgr_agent_core.agents.sgr_tool_calling_agent import SGRToolCallingAgent
from easy_sgr.sgr_agent_core.base_agent import BaseAgent
from easy_sgr.sgr_agent_core.base_tool import BaseTool
from easy_sgr.sgr_agent_core.models import AgentStatesEnum
from easy_sgr.sgr_agent_core.tools import FinalAnswerTool

from .llms import ChatOpenAI

if TYPE_CHECKING:
    from easy_sgr.sgr_agent_core.agent_definition import AgentConfig
    from easy_sgr.sgr_agent_core.models import AgentContext


def _create_custom_final_answer_tool(output_schema: type[BaseModel]) -> type[BaseTool]:
    """Create a custom FinalAnswerTool based on the provided Pydantic schema."""
    from pydantic import create_model

    class CustomFinalAnswerToolBase(BaseTool):
        """Custom FinalAnswerTool with user-defined schema."""
        
        tool_name = "finalanswertool"
        description = "Finalize a task and complete agent execution with structured output."

        async def __call__(self, context: "AgentContext", config: "AgentConfig", **_) -> str:
            from easy_sgr.sgr_agent_core.models import AgentStatesEnum
            context.state = AgentStatesEnum.COMPLETED
            context.execution_result = self.model_dump_json(indent=2)
            return context.execution_result

    fields = {}
    for field_name, field_info in output_schema.model_fields.items():
        default = field_info.default if field_info.default is not ... else ...
        fields[field_name] = (field_info.annotation, default)

    CustomFinalAnswerTool = create_model(
        "CustomFinalAnswerTool",
        __base__=CustomFinalAnswerToolBase,
        **fields
    )
    
    CustomFinalAnswerTool.tool_name = "finalanswertool"
    CustomFinalAnswerTool.description = f"Finalize task with structured output matching {output_schema.__name__} schema."
    
    return CustomFinalAnswerTool


def create_agent(
    llm: ChatOpenAI,
    tools: list,
    messages: list[dict[str, str]] | None = None,
    agent_name: str = "custom_agent",
    base_class: type[BaseAgent] = SGRAgent,
    output_schema: type[BaseModel] | None = None,
    **kwargs: Any,
) -> AgentDefinition:
    """Create an SGR agent with LangChain-like interface.
    
    Example:
        agent = create_agent(
            llm=ChatOpenAI(model="gpt-4", temperature=0),
            tools=[add_numbers, multiply_numbers],
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
            ]
        )
    
    Args:
        llm: ChatOpenAI instance
        tools: List of tool classes or decorated functions
        messages: Initial messages (system prompts, etc.)
        agent_name: Name for the agent
        base_class: Base agent class to use. Use SGRToolCallingAgent for OpenRouter /
            providers that don't support structured output (response_format).
        output_schema: Optional Pydantic BaseModel schema for structured output.
            If provided, agent will return result matching this schema.
        **kwargs: Additional agent configuration
        
    Returns:
        AgentDefinition ready to be executed
    """
    # Convert tools to list of classes
    tool_classes = []
    for tool_item in tools:
        # If it's already a BaseTool class, use it directly
        if isinstance(tool_item, type):
            tool_classes.append(tool_item)
        else:
            raise ValueError(f"Invalid tool type: {type(tool_item)}. Expected BaseTool class. Got: {tool_item}")

    # Use custom FinalAnswerTool if output_schema is provided
    final_answer_tool = FinalAnswerTool
    if output_schema is not None:
        final_answer_tool = _create_custom_final_answer_tool(output_schema)
    
    # Ensure agent can complete: add FinalAnswerTool if not already in toolkit
    has_final_answer = any(
        hasattr(tool, "tool_name") and tool.tool_name == "finalanswertool"
        for tool in tool_classes
    )
    if not has_final_answer:
        tool_classes.append(final_answer_tool)

    # Create agent definition
    # Ensure prompts are configured if not provided
    if "prompts" not in kwargs:
        from easy_sgr.sgr_agent_core.agent_definition import PromptsConfig
        kwargs["prompts"] = PromptsConfig()
    
    agent_def = AgentDefinition(
        name=agent_name,
        base_class=base_class,
        tools=tool_classes,
        llm=llm.to_llm_config(),
        **kwargs,
    )
    
    # Store initial messages in the definition if provided
    if messages:
        agent_def._initial_messages = messages
    
    # Store output schema if provided
    if output_schema is not None:
        agent_def._output_schema = output_schema
    
    agent_executor = AgentExecutor(agent=agent_def, verbose=True)
    return agent_executor


class AgentExecutor:
    """Executor for running agents with a simple interface.
    
    Example:
        executor = AgentExecutor(agent=agent, verbose=True)
        result = await executor.invoke({"input": "What is 10 + 5?"})
        print(result['output'])
    """
    
    def __init__(
        self,
        agent: AgentDefinition,
        verbose: bool = False,
    ):
        """Initialize AgentExecutor.
        
        Args:
            agent: Agent definition to execute
            verbose: Whether to print verbose output
        """
        self.agent_def = agent
        self.verbose = verbose
        self._agent_instance: BaseAgent | None = None
    
    async def ainvoke(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent with given input.
        
        Args:
            input_data: Dictionary with 'input' key containing user query
            
        Returns:
            Dictionary with 'output' key containing agent result
        """
        # Extract user input
        user_input = input_data.get("input", "")
        
        # Prepare messages
        messages: list[ChatCompletionMessageParam] = []
        
        # Add initial messages if available
        if hasattr(self.agent_def, "_initial_messages"):
            messages.extend(self.agent_def._initial_messages)
        
        # Add user input
        messages.append({"role": "user", "content": user_input})
        
        # Create agent instance
        import asyncio
        try:
            # Add timeout to prevent hanging
            self._agent_instance = await asyncio.wait_for(
                AgentFactory.create(
                    agent_def=self.agent_def,
                    task_messages=messages,
                ),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            raise RuntimeError("Agent creation timed out. Check MCP server connections.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
        
        # Execute agent
        import asyncio
        try:
            # Add timeout for agent execution
            result = await asyncio.wait_for(
                self._agent_instance.execute(),
                timeout=120.0  # 2 minute timeout for agent execution
            )
        except asyncio.TimeoutError:
            raise RuntimeError("Agent execution timed out. Check LLM API connection.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise
        
        # Parse result into schema if output_schema is provided
        if hasattr(self.agent_def, "_output_schema") and self.agent_def._output_schema is not None:
            try:
                if isinstance(result, str):
                    parsed_result = self.agent_def._output_schema.model_validate_json(result)
                else:
                    parsed_result = self.agent_def._output_schema.model_validate(result)
                result = parsed_result
            except Exception as e:
                # If parsing fails, return original result
                pass
        
        return {
            "output": result,
            "agent_id": self._agent_instance.id,
        }
    
    def invoke(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent synchronously (blocking). Use from sync code.

        Use ainvoke() with await when inside async code.
        """
        import asyncio
        return asyncio.run(self.ainvoke(input_data))

    async def stream(self, input_data: dict[str, Any]):
        """Stream agent execution results.
        
        Args:
            input_data: Dictionary with 'input' key containing user query
            
        Yields:
            Chunks of agent output
        """
        # Extract user input
        user_input = input_data.get("input", "")
        
        # Prepare messages
        messages: list[ChatCompletionMessageParam] = []
        
        # Add initial messages if available
        if hasattr(self.agent_def, "_initial_messages"):
            messages.extend(self.agent_def._initial_messages)
        
        # Add user input
        messages.append({"role": "user", "content": user_input})
        
        # Create agent instance
        self._agent_instance = await AgentFactory.create(
            agent_def=self.agent_def,
            task_messages=messages,
        )
        
        # Stream execution
        if hasattr(self._agent_instance, "streaming_generator"):
            # Start execution in background
            import asyncio
            execution_task = asyncio.create_task(self._agent_instance.execute())
            
            # Stream chunks
            async for chunk in self._agent_instance.streaming_generator.stream():
                yield chunk
            
            # Wait for execution to complete
            await execution_task
        else:
            # Fallback to regular execution
            result = await self._agent_instance.execute()
            yield result
