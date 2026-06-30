from abc import ABC, abstractmethod
from typing import Any

class BaseLLMProvider(ABC):
    """
    Abstract interface wrapping text and structured LLM inference calls.
    """
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> str:
        """
        Generate raw text response from the language model.
        """
        pass

    @abstractmethod
    async def generate_json(self, prompt: str, schema: type | None = None, **kwargs: Any) -> dict[str, Any]:
        """
        Generate structured JSON output validated against an optional schema.
        """
        pass
