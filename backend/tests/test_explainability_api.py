import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_ranking_agent import seed_test_job_and_candidate

@pytest.mark.anyio
async def test_explainability_api_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Seed job and candidate in SQLite memory
    job_id, cand_id = await seed_test_job_and_candidate(db_session)
    await db_session.commit()

    # 2. Test GET /explain/{job_id} - should run explainability lazily
    res_explain_all = await client.get(f"/explain/{job_id}")
    assert res_explain_all.status_code == 200
    data_all = res_explain_all.json()
    assert data_all["success"] is True
    assert len(data_all["data"]) > 0
    cand_ids_returned = [e["candidate_id"] for e in data_all["data"]]
    assert cand_id in cand_ids_returned
    cand_pkg = next(e for e in data_all["data"] if e["candidate_id"] == cand_id)
    assert "overall_summary" in cand_pkg

    # 3. Test GET /candidate/{id}/explanation?job_id={job_id}
    res_explain = await client.get(f"/candidate/{cand_id}/explanation?job_id={job_id}")
    assert res_explain.status_code == 200
    data_exp = res_explain.json()
    assert data_exp["success"] is True
    assert data_exp["data"]["candidate_id"] == cand_id

    # 4. Test GET /candidate/{id}/strengths?job_id={job_id}
    res_strengths = await client.get(f"/candidate/{cand_id}/strengths?job_id={job_id}")
    assert res_strengths.status_code == 200
    data_st = res_strengths.json()
    assert data_st["success"] is True
    assert isinstance(data_st["data"], list)

    # 5. Test GET /candidate/{id}/weaknesses?job_id={job_id}
    res_weaknesses = await client.get(f"/candidate/{cand_id}/weaknesses?job_id={job_id}")
    assert res_weaknesses.status_code == 200
    data_wk = res_weaknesses.json()
    assert data_wk["success"] is True
    assert isinstance(data_wk["data"], list)

    # 6. Test GET /candidate/{id}/recommendation?job_id={job_id}
    res_rec = await client.get(f"/candidate/{cand_id}/recommendation?job_id={job_id}")
    assert res_rec.status_code == 200
    data_rec = res_rec.json()
    assert data_rec["success"] is True
    assert isinstance(data_rec["data"], list)
    assert len(data_rec["data"]) > 0

    # 7. Test POST /compare
    res_compare = await client.post("/compare", json={
        "job_id": job_id,
        "candidate_ids": [cand_id, cand_id]  # Compare against itself for test simplicity
    })
    assert res_compare.status_code == 200
    data_comp = res_compare.json()
    assert data_comp["success"] is True
    assert "comparison" in data_comp["data"]
    assert cand_id in data_comp["data"]["comparison"]

    # 8. Test GET /audit/{job_id}
    res_audit = await client.get(f"/audit/{job_id}")
    assert res_audit.status_code == 200
    data_aud = res_audit.json()
    assert data_aud["success"] is True
    assert len(data_aud["data"]) > 0
    audit_cand_ids = [a["candidate_id"] for a in data_aud["data"]]
    assert cand_id in audit_cand_ids
    cand_audit = next(a for a in data_aud["data"] if a["candidate_id"] == cand_id)
    assert "weights_applied" in cand_audit

    # 9. Test GET /candidate/{id}/report-pdf?job_id={job_id}
    res_pdf = await client.get(f"/candidate/{cand_id}/report-pdf?job_id={job_id}")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 0

@pytest.mark.anyio
async def test_get_explanation_not_found(client: AsyncClient):
    res = await client.get("/candidate/nonexistent_id/explanation?job_id=nonexistent_job")
    assert res.status_code in [404, 500]
