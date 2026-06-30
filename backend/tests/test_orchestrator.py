import pytest
from typing import Any
from app.services.agents.base import BaseAgent
from app.services.agents.orchestrator import AIOrchestrator

class DummyAgent(BaseAgent):
    def __init__(self, name: str, is_valid: bool = True, should_fail: bool = False):
        self.name = name
        self._is_valid = is_valid
        self.should_fail = should_fail
        
    async def initialize(self):
        pass
        
    async def execute(self, input_data: Any, context: dict[str, Any]) -> Any:
        if self.should_fail:
            raise ValueError(f"Agent {self.name} failed execution intentionally.")
        context[f"executed_{self.name}"] = True
        return f"{input_data} -> {self.name}"
        
    async def validate(self, input_data: Any) -> bool:
        return self._is_valid
        
    def explain(self) -> str:
        return "Dummy explain"
        
    async def health(self) -> dict[str, Any]:
        return {"status": "healthy"}
        
    def version(self) -> str:
        return "1.0.0"
        
    def supported_inputs(self) -> list[str]:
        return ["input"]
        
    def supported_outputs(self) -> list[str]:
        return ["output"]

@pytest.mark.anyio
async def test_orchestrator_agent_registration():
    orchestrator = AIOrchestrator()
    agent_a = DummyAgent("agent_a")
    orchestrator.register_agent("agent_a", agent_a)
    
    assert orchestrator.get_agent("agent_a") == agent_a
    assert "agent_a" in orchestrator.list_agents()

@pytest.mark.anyio
async def test_orchestrator_execute_pipeline_success():
    orchestrator = AIOrchestrator()
    agent_a = DummyAgent("agent_a")
    agent_b = DummyAgent("agent_b")
    orchestrator.register_agent("agent_a", agent_a)
    orchestrator.register_agent("agent_b", agent_b)
    
    context = {}
    output, final_context, trace = await orchestrator.execute_pipeline(
        pipeline=["agent_a", "agent_b"],
        initial_input="start",
        context=context
    )
    
    assert output == "start -> agent_a -> agent_b"
    assert final_context["executed_agent_a"] is True
    assert final_context["executed_agent_b"] is True
    assert len(trace) == 2
    assert trace[0]["status"] == "SUCCESS"
    assert trace[1]["status"] == "SUCCESS"
    assert trace[0]["duration_sec"] >= 0.0
    assert trace[0]["memory_delta_mb"] >= 0.0

@pytest.mark.anyio
async def test_orchestrator_execute_pipeline_failure():
    orchestrator = AIOrchestrator()
    agent_a = DummyAgent("agent_a")
    agent_b = DummyAgent("agent_b", should_fail=True)
    orchestrator.register_agent("agent_a", agent_a)
    orchestrator.register_agent("agent_b", agent_b)
    
    context = {}
    with pytest.raises(ValueError, match="failed execution intentionally"):
        await orchestrator.execute_pipeline(
            pipeline=["agent_a", "agent_b"],
            initial_input="start",
            context=context
        )
