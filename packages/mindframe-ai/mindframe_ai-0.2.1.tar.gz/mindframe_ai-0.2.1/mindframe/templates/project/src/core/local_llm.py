from .base_llm import BaseLLM

class LocalLLM(BaseLLM):
    """Local/self-hosted models"""
    def generate(self, prompt: str):
        # TODO: Implement local model call
        return "Local LLM response"
