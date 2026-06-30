import pytest
from httpx import AsyncClient
from tests.test_candidate_api import seed_api_candidate

@pytest.mark.anyio
async def test_evidence_api_flow(client: AsyncClient, db_session):
    # 1. Seed candidate
    cand_id = await seed_api_candidate(client, db_session)

    # 2. Test POST /evidence/verify
    verify_res = await client.post("/evidence/verify", json={"candidate_id": cand_id})
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["success"] is True
    assert verify_data["data"]["candidate_id"] == cand_id
    assert "skill_verification" in verify_data["data"]

    # 3. Test GET /candidate/{id}/evidence
    res_ev = await client.get(f"/candidate/{cand_id}/evidence")
    assert res_ev.status_code == 200
    assert res_ev.json()["success"] is True
    assert res_ev.json()["data"]["candidate_id"] == cand_id

    # 4. Test GET /candidate/{id}/timeline
    res_time = await client.get(f"/candidate/{cand_id}/timeline")
    assert res_time.status_code == 200
    assert res_time.json()["success"] is True
    assert "chronological_tech_timeline" in res_time.json()["data"]

    # 5. Test GET /candidate/{id}/potential
    res_pot = await client.get(f"/candidate/{cand_id}/potential")
    assert res_pot.status_code == 200
    assert res_pot.json()["success"] is True
    assert "potentials" in res_pot.json()["data"]

    # 6. Test GET /candidate/{id}/risk
    res_risk = await client.get(f"/candidate/{cand_id}/risk")
    assert res_risk.status_code == 200
    assert res_risk.json()["success"] is True
    assert "risk_level" in res_risk.json()["data"]

    # 7. Test GET /candidate/{id}/verification
    res_ver = await client.get(f"/candidate/{cand_id}/verification")
    assert res_ver.status_code == 200
    assert res_ver.json()["success"] is True

    # 8. Test GET /candidate/{id}/evidence-graph
    res_eg = await client.get(f"/candidate/{cand_id}/evidence-graph")
    assert res_eg.status_code == 200
    assert res_eg.json()["success"] is True
    assert "nodes" in res_eg.json()["data"]

@pytest.mark.anyio
async def test_get_evidence_not_found(client: AsyncClient):
    res = await client.get("/candidate/nonexistent_cand_id/evidence")
    assert res.status_code == 404
    assert res.json()["success"] is False
