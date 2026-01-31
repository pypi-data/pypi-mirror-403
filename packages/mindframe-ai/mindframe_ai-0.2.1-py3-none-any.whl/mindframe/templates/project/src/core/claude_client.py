import os
from .base_llm import BaseLLM
import anthropic

class ClaudeClient(BaseLLM):
    """Anthropic Claude integration."""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20240620"):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return message.content[0].text

    def stream(self, prompt: str, **kwargs):
        return self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        )
