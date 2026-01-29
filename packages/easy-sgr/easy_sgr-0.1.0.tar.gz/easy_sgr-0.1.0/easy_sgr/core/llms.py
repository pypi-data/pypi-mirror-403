"""LLM wrappers for SGR agents."""

from __future__ import annotations

from typing import Any

from easy_sgr.sgr_agent_core.agent_definition import LLMConfig


class ChatOpenAI:
    """OpenAI Chat model wrapper compatible with SGR agents.
    
    Example:
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            api_key="your-api-key"
        )
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.4,
        max_tokens: int = 8000,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        proxy: str | None = None,
        **kwargs: Any,
    ):
        """Initialize ChatOpenAI.
        
        Args:
            model: Model name to use
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            api_key: OpenAI API key
            base_url: API base URL
            proxy: Proxy URL (e.g., socks5://127.0.0.1:1081)
            **kwargs: Additional parameters
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.base_url = base_url
        self.proxy = proxy
        self.extra_params = kwargs
    
    def to_llm_config(self) -> LLMConfig:
        """Convert to SGR LLMConfig.
        
        Returns:
            LLMConfig instance
        """
        return LLMConfig(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            proxy=self.proxy,
            **self.extra_params,
        )
