"""Easy SGR - Simplified interface for SGR agents in LangChain style."""

from .core import AgentExecutor, ChatOpenAI, create_agent, SGRToolCallingAgent, tool

__all__ = [
    "tool",
    "ChatOpenAI",
    "create_agent",
    "AgentExecutor",
    "SGRToolCallingAgent",
]

__version__ = "0.1.0"
