from abc import ABC, abstractmethod

class BaseLLM(ABC):
    """Common interface for all LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response for a given prompt."""
        pass
    
    @abstractmethod
    def stream(self, prompt: str, **kwargs):
        """Stream the generation response."""
        pass
