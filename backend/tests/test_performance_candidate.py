import pytest
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.candidate_agent import candidate_agent
from tests.test_candidate_agent import seed_test_candidate

@pytest.mark.anyio
async def test_performance_candidate_latencies(db_session: AsyncSession):
    # 1. Seed candidate
    candidate_id = await seed_test_candidate(db_session)

    # 2. Warm up agent
    await candidate_agent.initialize()
    context = {"db": db_session, "candidate_id": candidate_id}
    await candidate_agent.execute(candidate_id, context)

    # 3. Benchmark iterations
    start_time = time.perf_counter()
    iterations = 5
    for i in range(iterations):
        iter_context = {"db": db_session, "candidate_id": candidate_id}
        res = await candidate_agent.execute(candidate_id, iter_context)
        assert len(res["trace"]) > 0

    duration = time.perf_counter() - start_time
    avg_duration = duration / iterations

    print(f"\nAverage Candidate Intelligence Agent latency: {avg_duration * 1000:.2f} ms")

    # Assert average latency is under 500ms once warmed up (running rule-based local logic)
    assert avg_duration < 0.50, f"Average latency was {avg_duration * 1000:.2f}ms, which is above the 500ms threshold."
