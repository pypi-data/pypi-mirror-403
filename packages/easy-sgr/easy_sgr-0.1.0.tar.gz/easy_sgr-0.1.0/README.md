# Easy SGR

A simplified interface for building SGR (Schema-Guided Reasoning) agents in a LangChain-like style.

## Features

- 🎯 **Simple API** in the spirit of LangChain
- 🛠️ **`@tool` decorator** — turn functions into tools
- 🤖 **ChatOpenAI** — LLM wrapper (OpenAI, OpenRouter, etc.)
- ⚡ **Sync and async** — `invoke()` (no await) and `ainvoke()` (with await)
- 📐 **Structured output** — Pydantic schema via `output_schema`
- 🔧 **Flexible agent configuration**

## Installation

```bash
pip install -e .
```

Or from PyPI (after publishing):

```bash
pip install easy-sgr
```

## Quick start

### 1. Tools

The `@tool` decorator turns a function into an SGR tool:

```python
from easy_sgr import tool

@tool
def add_numbers(a: int, b: int) -> int:
    """Adds two numbers together.

    Args:
        a: First number
        b: Second number
    """
    return a + b

@tool
async def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny"
```

### 2. LLM

```python
from easy_sgr import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",
)
```

### 3. Agent and run

```python
from easy_sgr import create_agent

tools = [add_numbers, get_weather]
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
]

agent = create_agent(llm=llm, tools=tools, messages=messages)

# Sync (no await)
result = agent.invoke({"input": "What is 10 + 5?"})
print(result["output"])

# Async (inside async code)
result = await agent.ainvoke({"input": "What is 10 + 5?"})
print(result["output"])
```

## Full example

```python
import os
from dotenv import load_dotenv
from easy_sgr import tool, ChatOpenAI, create_agent

load_dotenv()

@tool
def add_numbers(a: int, b: int) -> int:
    """Adds two numbers together."""
    return a + b

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

agent = create_agent(
    llm=llm,
    tools=[add_numbers],
    messages=[{"role": "system", "content": "You are a helpful assistant."}],
)

result = agent.invoke({"input": "What is 10 + 5?"})
print(result["output"])
```

## Structured output (`output_schema`)

Pass a Pydantic model as `output_schema` — the agent will return an instance of it:

```python
from pydantic import BaseModel, Field
from easy_sgr import create_agent, tool, ChatOpenAI

class MathResult(BaseModel):
    sum_result: int = Field(description="Result of addition")
    product_result: int = Field(description="Result of multiplication")
    summary: str = Field(description="Brief summary")

@tool
def add_numbers(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

@tool
def multiply_numbers(a: int, b: int) -> int:
    """Multiplies two numbers."""
    return a * b

agent = create_agent(
    llm=llm,
    tools=[add_numbers, multiply_numbers],
    messages=[{"role": "system", "content": "..."}],
    output_schema=MathResult,
)

result = agent.invoke({"input": "Calculate 10 + 5 and 10 * 5, then summarize."})
output = result["output"]  # MathResult
print(output.sum_result, output.product_result, output.summary)
```

## Examples

See the [`examples/`](examples/) folder:

- `example.py` — basic usage with `invoke`
- `example_structured.py` — structured output via `output_schema`