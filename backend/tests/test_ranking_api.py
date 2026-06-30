import pytest
from httpx import AsyncClient
from tests.test_ranking_agent import seed_test_job_and_candidate

@pytest.mark.anyio
async def test_ranking_api_flow(client: AsyncClient, db_session):
    # 1. Seed job and candidate
    job_id, cand_id = await seed_test_job_and_candidate(db_session)
    await db_session.commit()

    # 2. Test POST /ranking/run
    run_res = await client.post("/ranking/run", json={
        "job_id": job_id,
        "candidate_ids": [cand_id],
        "top_k_rerank": 0  # Skip rerank for API test speed
    })
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["success"] is True
    assert run_data["data"]["job_id"] == job_id
    assert len(run_data["data"]["rankings"]) == 1
    assert run_data["data"]["rankings"][0]["candidate_id"] == cand_id

    # 3. Test POST /ranking/rebuild
    rebuild_res = await client.post("/ranking/rebuild", json={
        "job_id": job_id,
        "candidate_ids": [cand_id],
        "top_k_rerank": 0
    })
    assert rebuild_res.status_code == 200
    assert rebuild_res.json()["success"] is True

    # 4. Test GET /ranking/{job_id}
    res_get = await client.get(f"/ranking/{job_id}")
    assert res_get.status_code == 200
    assert res_get.json()["success"] is True
    assert res_get.json()["data"]["job_id"] == job_id

    # 5. Test GET /ranking/{job_id}/top
    res_top = await client.get(f"/ranking/{job_id}/top?limit=5")
    assert res_top.status_code == 200
    assert res_top.json()["success"] is True
    assert len(res_top.json()["data"]) > 0

    # 6. Test GET /ranking/{job_id}/trace
    res_trace = await client.get(f"/ranking/{job_id}/trace")
    assert res_trace.status_code == 200
    assert res_trace.json()["success"] is True
    assert len(res_trace.json()["data"]) > 0

    # 7. Test GET /ranking/{job_id}/statistics
    res_stats = await client.get(f"/ranking/{job_id}/statistics")
    assert res_stats.status_code == 200
    assert res_stats.json()["success"] is True
    assert "ranking_latency_sec" in res_stats.json()["data"]

    # 8. Test POST /recommendations
    res_rec = await client.post("/recommendations", json={
        "job_id": job_id,
        "candidate_id": cand_id
    })
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert rec_data["success"] is True
    assert rec_data["data"]["candidate_id"] == cand_id
    assert "recommendation" in rec_data["data"]

    # 9. Test GET /ranking/{job_id}/export-csv
    res_csv = await client.get(f"/ranking/{job_id}/export-csv")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert len(res_csv.content) > 0

    # 10. Test GET /ranking/{job_id}/export-xlsx
    res_xlsx = await client.get(f"/ranking/{job_id}/export-xlsx")
    assert res_xlsx.status_code == 200
    assert "spreadsheetml.sheet" in res_xlsx.headers["content-type"]
    assert len(res_xlsx.content) > 0

@pytest.mark.anyio
async def test_get_ranking_not_found(client: AsyncClient):
    res = await client.get("/ranking/nonexistent_job_id")
    assert res.status_code == 404
    assert res.json()["success"] is False
