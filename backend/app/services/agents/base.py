from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    """
    Abstract interface for all AI agents in the TalentMind AI platform.
    Ensures consistent lifecycle management, explainability, metrics, and data validation.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initializes agent state, loading dependencies, custom config or local transformers/models.
        """
        pass

    @abstractmethod
    async def execute(self, input_data: Any, context: dict[str, Any]) -> Any:
        """
        Executes the main logical operation of the agent using a shared context.
        """
        pass

    @abstractmethod
    async def validate(self, input_data: Any) -> bool:
        """
        Validates whether the inputs conform to the formats expected by this agent.
        """
        pass

    @abstractmethod
    def explain(self) -> str:
        """
        Returns a human-readable explanation of how this agent operates or makes decisions.
        """
        pass

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """
        Returns diagnostic health information for this agent (e.g. model loaded status, latency statistics).
        """
        pass

    @abstractmethod
    def version(self) -> str:
        """
        Returns semantic version of the agent.
        """
        pass

    @abstractmethod
    def supported_inputs(self) -> list[str]:
        """
        Returns a list of input key identifiers that this agent supports.
        """
        pass

    @abstractmethod
    def supported_outputs(self) -> list[str]:
        """
        Returns a list of output key identifiers that this agent produces.
        """
        pass
