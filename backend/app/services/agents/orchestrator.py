import time
import os
import psutil
from typing import Any, Dict, List, Optional
from app.core.logging.logging import logger
from app.services.agents.base import BaseAgent

class AIOrchestrator:
    """
    AI Orchestrator layer responsible for:
    - Registering pluggable AI agents
    - Sequencing agent execution
    - Managing shared execution context
    - Capturing execution metrics (time, memory usage delta)
    - Handling failures and compiling detailed AI Trace records
    """
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        """
        Register a pluggable agent with the orchestrator.
        """
        self._agents[name] = agent
        logger.info("agent_registered", agent_name=name, version=agent.version())

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Retrieve a registered agent by name.
        """
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """
        List all registered agent names.
        """
        return list(self._agents.keys())

    async def execute_agent(self, name: str, input_data: Any, context: Dict[str, Any]) -> Any:
        """
        Execute a single agent by name with the given input and context.
        """
        agent = self.get_agent(name)
        if not agent:
            raise ValueError(f"Agent '{name}' is not registered with the orchestrator.")

        # Initialize agent if needed (optional hook, can be run beforehand or lazily)
        # For safety, initialize is called once or lazily
        # Here we just run execute directly since initialize is handled in lifecycle startup.

        # Validate input
        if not await agent.validate(input_data):
            raise ValueError(f"Validation failed for agent '{name}' with the provided input.")

        # Execute and return
        return await agent.execute(input_data, context)

    async def execute_pipeline(
        self,
        pipeline: List[str],
        initial_input: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[Any, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Executes a sequence of agents.
        
        Args:
            pipeline: List of agent names in execution order.
            initial_input: The starting input for the first agent.
            context: Shared state between agents.
            
        Returns:
            Tuple of:
            - final_output: The output of the last executed agent.
            - context: The updated shared context.
            - trace: A list of dicts detailing each agent's execution performance and state.
        """
        if context is None:
            context = {}

        trace: List[Dict[str, Any]] = []
        current_input = initial_input
        pid = os.getpid()
        process = psutil.Process(pid)

        logger.info("pipeline_execution_start", pipeline=pipeline)

        for agent_name in pipeline:
            agent = self.get_agent(agent_name)
            if not agent:
                err_msg = f"Agent '{agent_name}' in pipeline is not registered."
                logger.error("pipeline_execution_failed", error=err_msg)
                raise ValueError(err_msg)

            # Record baseline performance parameters
            start_time = time.perf_counter()
            start_mem = process.memory_info().rss / (1024 * 1024)  # MB

            step_trace = {
                "agent_name": agent_name,
                "version": agent.version(),
                "timestamp": time.time(),
                "status": "PENDING",
                "error": None,
                "duration_sec": 0.0,
                "memory_delta_mb": 0.0,
            }

            try:
                # Execution
                current_output = await agent.execute(current_input, context)
                
                # Update status
                step_trace["status"] = "SUCCESS"
                
                # Chain output to input for next agent if needed
                current_input = current_output
                
            except Exception as e:
                step_trace["status"] = "FAILED"
                step_trace["error"] = str(e)
                logger.exception("agent_execution_exception", agent_name=agent_name, error=str(e))
                
                # Compile metrics before raising
                end_time = time.perf_counter()
                end_mem = process.memory_info().rss / (1024 * 1024)
                step_trace["duration_sec"] = round(end_time - start_time, 4)
                step_trace["memory_delta_mb"] = round(end_mem - start_mem, 2)
                trace.append(step_trace)
                
                raise e
            finally:
                end_time = time.perf_counter()
                end_mem = process.memory_info().rss / (1024 * 1024)
                step_trace["duration_sec"] = round(end_time - start_time, 4)
                step_trace["memory_delta_mb"] = round(end_mem - start_mem, 2)
                trace.append(step_trace)

        logger.info("pipeline_execution_complete", pipeline=pipeline, duration_sec=sum(t["duration_sec"] for t in trace))
        return current_input, context, trace

orchestrator = AIOrchestrator()
