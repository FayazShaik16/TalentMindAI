from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List
import time

from app.api.v1.dependencies.db import get_db
from app.api.v1.dependencies.auth import get_current_user
from app.schemas.responses import EnvelopeResponse
from app.schemas.workspace import (
    WorkspacePreferencesRequest, WorkspacePreferencesResponse,
    WorkspaceResponse, JobSessionResponse, RecruiterActivityResponse
)
from app.database.repositories.workspace import WorkspaceRepository
from app.database.repositories.job import JobRepository
from app.database.repositories.candidate import CandidateRepository
from app.services.analytics.analytics import AnalyticsEngine
from app.services.analytics.monitoring import MonitoringService

router = APIRouter(prefix="/dashboard", tags=["Recruiter Intelligence Platform, Analytics & Operational Intelligence"])

@router.get("", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get aggregated recruiter activity metrics and candidate/job platform statistics.
    """
    recruiter_id = current_user.get("user_id", "mock-tenant-id-01")
    ws_repo = WorkspaceRepository(db)
    job_repo = JobRepository(db)
    cand_repo = CandidateRepository(db)

    # 1. Fetch real DB totals
    jobs = await job_repo.get_all()
    candidates = await cand_repo.get_all()

    # 2. Query activity logs
    activities = await ws_repo.get_activities(recruiter_id, limit=1000)
    
    counts = {
        "jobs_created": len(jobs),
        "candidates_reviewed": len(candidates),
        "reports_generated": 0,
        "comparisons": 0,
        "exports": 0
    }

    for act in activities:
        atype = act.action_type
        if atype == "REPORT_GENERATED":
            counts["reports_generated"] += 1
        elif atype == "COMPARISON":
            counts["comparisons"] += 1
        elif atype == "EXPORT":
            counts["exports"] += 1

    # 3. Calculate dynamic avg_confidence from rankings
    from app.database.repositories.ranking import RankingRepository
    rank_repo = RankingRepository(db)
    all_rankings = await rank_repo.get_all()
    
    total_score = 0.0
    score_count = 0
    for r in all_rankings:
        for cand in r.rankings:
            score = cand.get("overall_score", 0.0)
            total_score += score
            score_count += 1
            
    avg_confidence = (total_score / score_count) if score_count > 0 else 0.0

    return EnvelopeResponse(data={
        "recruiter_id": recruiter_id,
        "total_jobs": len(jobs),
        "total_candidates": len(candidates),
        "avg_confidence": round(avg_confidence, 1),
        "activity_metrics": counts
    })

@router.get("/analytics", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_analytics(
    job_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve candidate matching averages, technology, experience, and domain distributions.
    """
    recruiter_id = current_user.get("user_id", "mock-tenant-id-01")
    ws_repo = WorkspaceRepository(db)
    await ws_repo.log_activity(recruiter_id, "ANALYTICS_VIEWED", {"job_id": job_id})
    await db.commit()

    engine = AnalyticsEngine(db)
    analytics_data = await engine.generate_hiring_analytics(job_id)
    return EnvelopeResponse(data=analytics_data)

@router.get("/monitoring", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_monitoring_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Collect system telemetry logs, FAISS statistics, database embedding caches, and agent statuses.
    """
    service = MonitoringService(db)
    stats = await service.get_ai_monitoring_stats()
    return EnvelopeResponse(data=stats)

@router.get("/health")
async def get_system_health(
    db: AsyncSession = Depends(get_db)
):
    """
    Perform database, vector index, and caching connectivity checks.
    """
    service = MonitoringService(db)
    health_data = await service.get_system_health()
    status_code = status.HTTP_200_OK if health_data["status"] == "healthy" else status.HTTP_500_INTERNAL_SERVER_ERROR
    return JSONResponse(
        status_code=status_code,
        content={"success": health_data["status"] == "healthy", "data": health_data}
    )

@router.get("/sessions", response_model=EnvelopeResponse[List[JobSessionResponse]])
async def get_job_sessions(
    job_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all versioned ranking snapshot sessions and histories.
    """
    ws_repo = WorkspaceRepository(db)
    if job_id:
        sessions = await ws_repo.get_all_sessions_for_job(job_id)
    else:
        sessions = await ws_repo.get_all_sessions()

    return EnvelopeResponse(data=[JobSessionResponse(
        session_id=s.session_id,
        job_id=s.job_id,
        ranking_version=s.ranking_version,
        candidate_snapshot=s.candidate_snapshot,
        ai_version=s.ai_version,
        status=s.status,
        history=s.history,
        created_at=s.created_at
    ) for s in sessions])

@router.get("/history", response_model=EnvelopeResponse[List[RecruiterActivityResponse]])
async def get_recruiter_history(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch search queries, exports, and profile edits history audit log.
    """
    recruiter_id = current_user.get("user_id", "mock-tenant-id-01")
    ws_repo = WorkspaceRepository(db)
    activities = await ws_repo.get_activities(recruiter_id)
    return EnvelopeResponse(data=[RecruiterActivityResponse(
        id=a.id,
        recruiter_id=a.recruiter_id,
        action_type=a.action_type,
        details=a.details,
        duration_ms=a.duration_ms,
        created_at=a.created_at
    ) for a in activities])

@router.post("/preferences", response_model=EnvelopeResponse[WorkspacePreferencesResponse])
async def update_preferences(
    payload: WorkspacePreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Save custom weights, embedding models, cross-encoder targets, and similarity thresholds.
    """
    recruiter_id = current_user.get("user_id", "mock-tenant-id-01")
    ws_repo = WorkspaceRepository(db)
    ws = await ws_repo.get_or_create_workspace(recruiter_id)

    # Merge preferences
    prefs = dict(ws.preferences)
    payload_dict = payload.model_dump(exclude_none=True)
    for k, v in payload_dict.items():
        prefs[k] = v

    ws.preferences = prefs
    await ws_repo.save_workspace(ws)
    
    # Log update
    await ws_repo.log_activity(recruiter_id, "PREFERENCES_UPDATED", {"fields": list(payload_dict.keys())})
    await db.commit()

    return EnvelopeResponse(data=WorkspacePreferencesResponse(recruiter_id=recruiter_id, preferences=prefs))

@router.get("/reports", response_model=EnvelopeResponse[List[Dict[str, Any]]])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List structural recruiter report types available in Report Center.
    """
    reports = [
        {"name": "Ranking Report", "scope": "job", "download_formats": ["csv", "json", "excel"]},
        {"name": "Candidate Report", "scope": "candidate", "download_formats": ["pdf", "json", "md"]},
        {"name": "Comparison Report", "scope": "comparison", "download_formats": ["json", "md"]},
        {"name": "Executive Summary", "scope": "candidate", "download_formats": ["pdf", "md"]},
        {"name": "Technical Evaluation", "scope": "candidate", "download_formats": ["pdf", "md"]},
        {"name": "Interview Guide", "scope": "candidate", "download_formats": ["pdf", "md"]}
    ]
    return EnvelopeResponse(data=reports)

@router.get("/exports", response_model=EnvelopeResponse[Dict[str, Any]])
async def trigger_export(
    job_id: str,
    format: str = "csv",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Execute download generation in CSV, JSON, MD, or Excel formats.
    """
    recruiter_id = current_user.get("user_id", "mock-tenant-id-01")
    ws_repo = WorkspaceRepository(db)
    
    await ws_repo.log_activity(recruiter_id, "EXPORT", {"job_id": job_id, "format": format})
    await db.commit()

    return EnvelopeResponse(data={
        "job_id": job_id,
        "format": format,
        "export_url": f"/api/v1/exports/ranking_{job_id}.{format}",
        "status": "ready"
    })
