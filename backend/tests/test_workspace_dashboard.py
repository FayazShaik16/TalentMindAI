import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_ranking_agent import seed_test_job_and_candidate
from app.database.repositories.workspace import WorkspaceRepository
from app.services.analytics.analytics import AnalyticsEngine
from app.services.analytics.monitoring import MonitoringService
from app.services.analytics.session_manager import SessionManager

@pytest.mark.anyio
async def test_workspace_repository_crud(db_session: AsyncSession):
    repo = WorkspaceRepository(db_session)
    recruiter_id = "test-recruiter-99"

    # 1. Create or get workspace
    ws = await repo.get_or_create_workspace(recruiter_id)
    assert ws.recruiter_id == recruiter_id
    assert isinstance(ws.preferences, dict)

    # 2. Update preferences
    ws.preferences = {"weights": {"semantic": 0.5}}
    ws.saved_candidates = ["cand_01"]
    ws.saved_jobs = ["job_01"]
    await repo.save_workspace(ws)
    await db_session.commit()

    ws_check = await repo.get_workspace(recruiter_id)
    assert ws_check.preferences["weights"]["semantic"] == 0.5
    assert "cand_01" in ws_check.saved_candidates

    # 3. Log recruiter activities
    act = await repo.log_activity(recruiter_id, "EXPORT", {"job_id": "job_01"}, duration_ms=120)
    await db_session.commit()
    assert act.id is not None
    assert act.action_type == "EXPORT"
    assert act.duration_ms == 120

    # 4. List activities
    history = await repo.get_activities(recruiter_id)
    assert len(history) >= 1
    assert history[0].action_type == "EXPORT"

@pytest.mark.anyio
async def test_session_versioning(db_session: AsyncSession):
    # Seed job & candidate
    job_id, cand_id = await seed_test_job_and_candidate(db_session)
    await db_session.commit()

    sm = SessionManager(db_session)
    rankings_mock = [
        {"candidate_id": cand_id, "overall_score": 85.0, "rank": 1, "recommendation": "Strong Hire"}
    ]

    existing = await sm.repo.get_all_sessions_for_job(job_id)
    initial_version = len(existing)

    # Create next session
    sess_v1 = await sm.create_or_update_session(job_id, rankings_mock)
    await db_session.commit()
    assert sess_v1.ranking_version == initial_version + 1
    assert sess_v1.session_id == f"{job_id}_v{initial_version + 1}"
    assert len(sess_v1.candidate_snapshot) == 1
    assert sess_v1.candidate_snapshot[0]["candidate_id"] == cand_id

    # Create subsequent session
    rankings_v2 = [
        {"candidate_id": cand_id, "overall_score": 90.0, "rank": 1, "recommendation": "Strong Hire"}
    ]
    sess_v2 = await sm.create_or_update_session(job_id, rankings_v2)
    await db_session.commit()
    assert sess_v2.ranking_version == initial_version + 2
    assert sess_v2.session_id == f"{job_id}_v{initial_version + 2}"
    assert sess_v2.candidate_snapshot[0]["overall_score"] == 90.0

@pytest.mark.anyio
async def test_analytics_and_monitoring_engines(db_session: AsyncSession):
    # Run hybrid ranking to seed ranking results in DB
    from app.services.agents.ranking_agent import ranking_agent
    job_id, cand_id = await seed_test_job_and_candidate(db_session)
    await db_session.commit()

    context = {"db": db_session, "candidate_ids": [cand_id], "top_k_rerank": 0}
    await ranking_agent.initialize()
    await ranking_agent.execute(job_id, context)
    await db_session.commit()

    # 1. Run AnalyticsEngine
    analytics_service = AnalyticsEngine(db_session)
    res = await analytics_service.generate_hiring_analytics(job_id)
    assert res["total_evaluated"] >= 1
    assert res["average_match_score"] > 0.0
    assert "hiring_funnel" in res
    assert "distributions" in res

    # 2. Run MonitoringService
    monitoring_service = MonitoringService(db_session)
    health = await monitoring_service.get_system_health()
    assert "status" in health
    assert "components" in health
    assert "metrics" in health
    assert health["components"]["database"] == "healthy"

    stats = await monitoring_service.get_ai_monitoring_stats()
    assert "timestamp" in stats
    assert "agents_status" in stats
    assert "resources" in stats

@pytest.mark.anyio
async def test_dashboard_apis_flow(client: AsyncClient, db_session: AsyncSession):
    job_id, cand_id = await seed_test_job_and_candidate(db_session)
    await db_session.commit()

    # Run ranking first so stats are populated
    from app.services.agents.ranking_agent import ranking_agent
    context = {"db": db_session, "candidate_ids": [cand_id], "top_k_rerank": 0}
    await ranking_agent.initialize()
    await ranking_agent.execute(job_id, context)
    await db_session.commit()

    # 1. Test GET /dashboard
    res = await client.get("/dashboard")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "total_jobs" in res.json()["data"]

    # 2. Test GET /dashboard/analytics
    res = await client.get(f"/dashboard/analytics?job_id={job_id}")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["total_evaluated"] >= 1

    # 3. Test GET /dashboard/monitoring
    res = await client.get("/dashboard/monitoring")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "agents_status" in res.json()["data"]

    # 4. Test GET /dashboard/health
    res = await client.get("/dashboard/health")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 5. Test GET /dashboard/sessions
    res = await client.get(f"/dashboard/sessions?job_id={job_id}")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert len(res.json()["data"]) >= 1

    # 6. Test POST /dashboard/preferences
    pref_res = await client.post("/dashboard/preferences", json={
        "ranking_weights": {"semantic": 0.4},
        "top_k": 10
    })
    assert pref_res.status_code == 200
    assert pref_res.json()["success"] is True
    assert pref_res.json()["data"]["preferences"]["top_k"] == 10

    # 7. Test GET /dashboard/history
    res = await client.get("/dashboard/history")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 8. Test GET /dashboard/reports
    res = await client.get("/dashboard/reports")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert len(res.json()["data"]) > 0

    # 9. Test GET /dashboard/exports
    res = await client.get(f"/dashboard/exports?job_id={job_id}&format=json")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert "export_url" in res.json()["data"]
