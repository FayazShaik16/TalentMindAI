import pytest
from httpx import AsyncClient

SAMPLE_JD = (
    "Job Title: Senior FastAPI Engineer\n"
    "We need a backend developer with 5+ years of experience in Python and FastAPI.\n"
    "You will lead system design and scale our cloud services on AWS."
)

@pytest.mark.anyio
async def test_jobs_api_flow(client: AsyncClient):
    # 1. Test POST /jobs/parse (Quick parse, does not save)
    parse_res = await client.post("/jobs/parse", json={"raw_text": SAMPLE_JD})
    assert parse_res.status_code == 200
    parse_data = parse_res.json()
    assert parse_data["success"] is True
    assert parse_data["data"]["profile"]["title"] == "Senior FastAPI Engineer"
    
    # 2. Test POST /jobs/analyze (Full pipeline run, persists to database)
    analyze_res = await client.post("/jobs/analyze", json={"raw_text": SAMPLE_JD, "id": "api_test_job_0"})
    assert analyze_res.status_code == 200
    analyze_data = analyze_res.json()
    assert analyze_data["success"] is True
    job_profile = analyze_data["data"]
    assert job_profile["id"] == "api_test_job_0"
    assert job_profile["title"] == "Senior FastAPI Engineer"
    assert job_profile["experience_required"] == 5.0
    
    # 3. Test GET /jobs/{id}
    get_res = await client.get("/jobs/api_test_job_0")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["success"] is True
    assert get_data["data"]["title"] == "Senior FastAPI Engineer"
    
    # 4. Test GET /jobs/{id}/intent
    intent_res = await client.get("/jobs/api_test_job_0/intent")
    assert intent_res.status_code == 200
    intent_data = intent_res.json()
    assert intent_data["success"] is True
    assert intent_data["data"]["title"] == "Senior FastAPI Engineer"
    assert "skills" in intent_data["data"]
    
    # 5. Test GET /jobs/{id}/graph
    graph_res = await client.get("/jobs/api_test_job_0/graph")
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert graph_data["success"] is True
    assert "nodes" in graph_data["data"]
    assert "edges" in graph_data["data"]
    
    # 6. Test GET /jobs/{id}/trace
    trace_res = await client.get("/jobs/api_test_job_0/trace")
    assert trace_res.status_code == 200
    trace_data = trace_res.json()
    assert trace_data["success"] is True
    assert len(trace_data["data"]) > 0
    assert trace_data["data"][0]["agent_name"] == "job_intelligence"

@pytest.mark.anyio
async def test_get_job_not_found(client: AsyncClient):
    get_res = await client.get("/jobs/nonexistent_job_id")
    assert get_res.status_code == 404
    get_data = get_res.json()
    assert get_data["success"] is False
    assert "not found" in get_data["error"]["message"].lower()
