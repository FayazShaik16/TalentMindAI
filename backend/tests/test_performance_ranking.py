import pytest
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.ranking_agent import ranking_agent
from tests.test_ranking_agent import seed_test_job_and_candidate

@pytest.mark.anyio
async def test_performance_ranking_latencies(db_session: AsyncSession):
    # 1. Seed job and candidate
    job_id, cand_id = await seed_test_job_and_candidate(db_session)
    await db_session.commit()

    # 2. Warm up agent
    await ranking_agent.initialize()
    context = {
        "db": db_session,
        "candidate_ids": [cand_id],
        "top_k_rerank": 0  # Skip rerank for performance warm up baseline
    }
    await ranking_agent.execute(job_id, context)

    # 3. Benchmark iterations
    start_time = time.perf_counter()
    iterations = 3
    for _ in range(iterations):
        iter_context = {
            "db": db_session,
            "candidate_ids": [cand_id],
            "top_k_rerank": 0
        }
        res = await ranking_agent.execute(job_id, iter_context)
        assert len(res["rankings"]) > 0
        assert len(res["trace"]) > 0

    duration = time.perf_counter() - start_time
    avg_duration = duration / iterations

    print(f"\nAverage Candidate Ranking Agent latency: {avg_duration * 1000:.2f} ms")

    # Assert average latency is under 1.5 seconds (since embedding/scoring runs on CPU fallback)
    assert avg_duration < 1.50, f"Average latency was {avg_duration * 1000:.2f}ms, which is above the 1.5s threshold."
