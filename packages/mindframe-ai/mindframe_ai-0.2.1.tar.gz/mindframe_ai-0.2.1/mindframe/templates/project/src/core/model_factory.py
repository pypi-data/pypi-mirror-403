from .gpt_client import GPTClient
from .claude_client import ClaudeClient
from typing import Optional, Union
from .base_llm import BaseLLM

class ModelFactory:
    """Model selection factory for easily switching between providers."""
    
    @staticmethod
    def get_model(provider: str, model_id: Optional[str] = None) -> BaseLLM:
        provider = provider.lower()
        
        if provider == "openai":
            return GPTClient(model=model_id or "gpt-4o")
        elif provider == "anthropic":
            return ClaudeClient(model=model_id or "claude-3-5-sonnet-20240620")
        
        raise ValueError(f"Unsupported provider: {provider}. Choice of 'openai' or 'anthropic'.")
