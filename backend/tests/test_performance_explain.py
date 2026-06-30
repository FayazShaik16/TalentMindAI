import pytest
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.explainability_agent import explainability_agent
from tests.test_ranking_agent import seed_test_job_and_candidate

@pytest.mark.anyio
async def test_performance_explain_latencies(db_session: AsyncSession):
    # 1. Seed job and candidate
    job_id, cand_id = await seed_test_job_and_candidate(db_session)
    await db_session.commit()

    # 2. Warm up agent
    await explainability_agent.initialize()
    context = {
        "db": db_session,
        "candidate_ids": [cand_id]
    }
    await explainability_agent.execute(job_id, context)

    # 3. Benchmark iterations
    start_time = time.perf_counter()
    iterations = 5
    for _ in range(iterations):
        iter_context = {
            "db": db_session,
            "candidate_ids": [cand_id]
        }
        res = await explainability_agent.execute(job_id, iter_context)
        assert len(res["explanations"]) > 0
        assert len(res["trace"]) > 0

    duration = time.perf_counter() - start_time
    avg_duration = duration / iterations

    print(f"\nAverage Candidate Explainability Agent latency: {avg_duration * 1000:.2f} ms")

    # Assert average latency is under 1.0 seconds for explainability calculations
    assert avg_duration < 1.0, f"Average latency was {avg_duration * 1000:.2f}ms, which is above the 1s threshold."
