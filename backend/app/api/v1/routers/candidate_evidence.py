import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List
from datetime import datetime, timezone

from app.api.v1.dependencies.db import get_db
from app.api.v1.dependencies.auth import get_current_user
from app.schemas.responses import EnvelopeResponse
from app.schemas.candidate_evidence import CandidateVerifyRequest, CandidateEvidenceResponse
from app.database.repositories.candidate import CandidateRepository
from app.database.repositories.candidate_evidence import CandidateEvidenceRepository
from app.database.models.candidate_evidence import CandidateEvidence
from app.api.v1.routers.candidate_intelligence import sanitize_for_json
from app.services.agents.orchestrator import orchestrator
from app.core.logging.logging import logger

router = APIRouter(tags=["Candidate Evidence Verification Engine"])

def map_db_to_response(db_ev: CandidateEvidence) -> CandidateEvidenceResponse:
    created = db_ev.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    updated = db_ev.updated_at
    if updated and updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)

    return CandidateEvidenceResponse(
        candidate_id=db_ev.candidate_id,
        skill_verification=db_ev.skill_verification,
        timeline=db_ev.timeline,
        potential_metrics=db_ev.potential_metrics,
        risk_analysis=db_ev.risk_analysis,
        evidence_graph=db_ev.evidence_graph,
        confidence_scores={k: float(v) for k, v in db_ev.confidence_scores.items()},
        trace=db_ev.trace,
        created_at=created,
        updated_at=updated
    )

@router.post("/evidence/verify", response_model=EnvelopeResponse[CandidateEvidenceResponse])
async def verify_candidate(
    payload: CandidateVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Executes Candidate Evidence Verification Agent to audit claimed skills,
    generate chronological timelines, identify resume risks, and build evidence graphs.
    """
    logger.info("api_verify_candidate_start", candidate_id=payload.candidate_id)

    # 1. Verify candidate exists
    cand_repo = CandidateRepository(db)
    cand = await cand_repo.get_candidate_profile(payload.candidate_id)
    if not cand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID '{payload.candidate_id}' not found."
        )

    # 2. Run orchestrator agent pipeline
    context = {"db": db, "candidate_id": payload.candidate_id}
    # Ensure Agent is loaded
    from app.services.agents.evidence_agent import evidence_verification_agent
    await evidence_verification_agent.initialize()

    try:
        final_output, updated_context, pipeline_trace = await orchestrator.execute_pipeline(
            pipeline=["evidence_verification"],
            initial_input=payload.candidate_id,
            context=context
        )
    except Exception as e:
        logger.error("api_verify_candidate_pipeline_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Pipeline failed: {str(e)}"
        )

    # 3. Persist evidence records
    repo = CandidateEvidenceRepository(db)
    clean_output = sanitize_for_json(final_output)

    ev_model = CandidateEvidence(
        candidate_id=clean_output["candidate_id"],
        skill_verification=clean_output["skill_verification"],
        timeline=clean_output["timeline"],
        potential_metrics=clean_output["potential_metrics"],
        risk_analysis=clean_output["risk_analysis"],
        evidence_graph=clean_output["evidence_graph"],
        trace=clean_output["trace"],
        confidence_scores=clean_output["confidence_scores"]
    )

    try:
        saved_ev = await repo.upsert_candidate_evidence(ev_model)
        await db.commit()
    except Exception as e:
        logger.error("api_verify_candidate_save_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist candidate evidence verification details."
        )

    response_data = map_db_to_response(saved_ev)
    return EnvelopeResponse(data=response_data)

@router.get("/candidate/{id}/evidence", response_model=EnvelopeResponse[CandidateEvidenceResponse])
async def get_candidate_evidence(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get full career evidence verification profile of a candidate.
    """
    repo = CandidateEvidenceRepository(db)
    ev = await repo.get_candidate_evidence(id)
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate evidence for ID '{id}' not found. Please trigger /evidence/verify first."
        )
    return EnvelopeResponse(data=map_db_to_response(ev))

@router.get("/candidate/{id}/timeline", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_timeline(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get chronological technology and career adoption timelines.
    """
    repo = CandidateEvidenceRepository(db)
    ev = await repo.get_candidate_evidence(id)
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate evidence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=ev.timeline)

@router.get("/candidate/{id}/potential", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_potential(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get candidate continuous learning rates, Innovation Potentials, and readiness.
    """
    repo = CandidateEvidenceRepository(db)
    ev = await repo.get_candidate_evidence(id)
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate evidence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=ev.potential_metrics)

@router.get("/candidate/{id}/risk", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_risk(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get candidate CV anomalies and stuffing/inflation risk reports.
    """
    repo = CandidateEvidenceRepository(db)
    ev = await repo.get_candidate_evidence(id)
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate evidence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=ev.risk_analysis)

@router.get("/candidate/{id}/verification", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_verification(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get verified skill details.
    """
    repo = CandidateEvidenceRepository(db)
    ev = await repo.get_candidate_evidence(id)
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate evidence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=ev.skill_verification)

@router.get("/candidate/{id}/evidence-graph", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_evidence_graph(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get evidence verification relational graph nodes and edges.
    """
    repo = CandidateEvidenceRepository(db)
    ev = await repo.get_candidate_evidence(id)
    if not ev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate evidence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=ev.evidence_graph)
