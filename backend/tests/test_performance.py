import pytest
import time
from app.services.agents.job_agent import job_agent
from app.services.intent_parser import intent_parser
from app.services.hidden_requirements import hidden_detector

SAMPLE_JD = (
    "Job Title: Senior Software Architect\n"
    "Location: Remote\n"
    "We need an Architect with 10+ years of experience.\n"
    "You will design scalable cloud platforms using AWS, Python, Kubernetes, and Docker.\n"
    "Mentorship of other engineers is required."
)

@pytest.mark.anyio
async def test_performance_latencies():
    # 1. Warm up model loading and caching
    await job_agent.initialize()
    context = {"job_id": "perf_warmup"}
    await job_agent.execute(SAMPLE_JD, context)

    # 2. Measure subsequent run execution times
    start_time = time.perf_counter()
    iterations = 5
    for i in range(iterations):
        iter_context = {"job_id": f"perf_iter_{i}"}
        res = await job_agent.execute(SAMPLE_JD, iter_context)
        
        # Verify trace has duration
        assert len(res["trace"]) > 0
        
    duration = time.perf_counter() - start_time
    avg_duration = duration / iterations
    
    print(f"\nAverage Job Intelligence Agent latency: {avg_duration * 1000:.2f} ms")
    
    # Assert average latency is under 500ms once models are warmed up and weights are loaded
    assert avg_duration < 0.50, f"Average latency was {avg_duration * 1000:.2f}ms, which is above the 500ms threshold."
