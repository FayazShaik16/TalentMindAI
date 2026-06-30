import time
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List
from datetime import datetime, timezone

from app.api.v1.dependencies.db import get_db
from app.api.v1.dependencies.auth import get_current_user
from app.schemas.responses import EnvelopeResponse
from app.schemas.candidate_intelligence import CandidateAnalyzeRequest, CandidateIntelligenceResponse
from app.database.repositories.candidate import CandidateRepository
from app.database.repositories.candidate_intelligence import CandidateIntelligenceRepository
from app.database.models.candidate_intelligence import CandidateIntelligence
from app.services.agents.orchestrator import orchestrator
from app.core.logging.logging import logger

router = APIRouter(prefix="/candidate", tags=["Candidate Career Intelligence"])

def sanitize_for_json(val: Any) -> Any:
    """
    Recursively converts numpy numbers and sets to standard Python types for JSON compatibility.
    """
    if isinstance(val, dict):
        return {k: sanitize_for_json(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [sanitize_for_json(v) for v in val]
    elif isinstance(val, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(val)
    elif isinstance(val, (np.floating, np.float64, np.float32, np.float16)):
        return float(val)
    elif isinstance(val, (np.bool_, bool)):
        return bool(val)
    elif isinstance(val, set):
        return list(val)
    return val

def map_db_to_response(db_intel: CandidateIntelligence) -> CandidateIntelligenceResponse:
    created = db_intel.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    updated = db_intel.updated_at
    if updated and updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)

    return CandidateIntelligenceResponse(
        candidate_id=db_intel.candidate_id,
        professional_summary=db_intel.professional_summary or "",
        career_intelligence=db_intel.career_intelligence,
        technical_intelligence=db_intel.technical_intelligence,
        leadership_intelligence=db_intel.leadership_intelligence,
        project_intelligence=db_intel.project_intelligence,
        domain_intelligence=db_intel.domain_intelligence,
        career_growth=db_intel.career_growth,
        specializations=db_intel.specializations,
        behavior_placeholder=db_intel.career_intelligence.get("behavior_placeholder", {}),
        knowledge_graph=db_intel.knowledge_graph,
        confidence_scores={k: float(v) for k, v in db_intel.confidence_scores.items()},
        trace=db_intel.trace,
        created_at=created,
        updated_at=updated
    )

@router.post("/analyze", response_model=EnvelopeResponse[CandidateIntelligenceResponse])
async def analyze_candidate(
    payload: CandidateAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Runs Candidate Intelligence Agent to analyze career progression, technology depth,
    leadership, and project complexity, saving results to CandidateIntelligence table.
    """
    logger.info("api_analyze_candidate_start", candidate_id=payload.candidate_id)

    # 1. Verify candidate exists in database
    cand_repo = CandidateRepository(db)
    cand = await cand_repo.get_candidate_profile(payload.candidate_id)
    if not cand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID '{payload.candidate_id}' not found."
        )

    # 2. Run orchestrator agent pipeline
    context = {"db": db, "candidate_id": payload.candidate_id}
    # Ensure Candidate agent is loaded (imported)
    from app.services.agents.candidate_agent import candidate_agent
    await candidate_agent.initialize()

    try:
        final_output, updated_context, pipeline_trace = await orchestrator.execute_pipeline(
            pipeline=["candidate_intelligence"],
            initial_input=payload.candidate_id,
            context=context
        )
    except Exception as e:
        logger.error("api_analyze_candidate_pipeline_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Pipeline failed: {str(e)}"
        )

    # 3. Persist intelligence records
    repo = CandidateIntelligenceRepository(db)
    
    # Sanitize dictionary values to protect SQLite from Numpy float/bool serialization errors
    clean_output = sanitize_for_json(final_output)

    intel_model = CandidateIntelligence(
        candidate_id=clean_output["candidate_id"],
        professional_summary=clean_output["professional_summary"],
        career_intelligence=clean_output["career_intelligence"],
        technical_intelligence=clean_output["technical_intelligence"],
        leadership_intelligence=clean_output["leadership_intelligence"],
        project_intelligence=clean_output["project_intelligence"],
        domain_intelligence=clean_output["domain_intelligence"],
        career_growth=clean_output["career_growth"],
        specializations=clean_output["specializations"],
        knowledge_graph=clean_output["knowledge_graph"],
        trace=clean_output["trace"],
        confidence_scores=clean_output["confidence_scores"]
    )

    try:
        saved_intel = await repo.upsert_candidate_intelligence(intel_model)
        await db.commit()
    except Exception as e:
        logger.error("api_analyze_candidate_save_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist candidate career intelligence details."
        )

    response_data = map_db_to_response(saved_intel)
    return EnvelopeResponse(data=response_data)

@router.get("/{id}/intelligence", response_model=EnvelopeResponse[CandidateIntelligenceResponse])
async def get_candidate_intelligence(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get full career intelligence profile of a candidate.
    """
    repo = CandidateIntelligenceRepository(db)
    intel = await repo.get_candidate_intelligence(id)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate intelligence for ID '{id}' not found. Please trigger analysis first."
        )
    return EnvelopeResponse(data=map_db_to_response(intel))

@router.get("/{id}/knowledge-graph", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_knowledge_graph(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get Candidate Knowledge Graph relations.
    """
    repo = CandidateIntelligenceRepository(db)
    intel = await repo.get_candidate_intelligence(id)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate intelligence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=intel.knowledge_graph)

@router.get("/{id}/career-analysis", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_career_analysis(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get candidate career progression details.
    """
    repo = CandidateIntelligenceRepository(db)
    intel = await repo.get_candidate_intelligence(id)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate intelligence for ID '{id}' not found."
        )
    return EnvelopeResponse(data={
        "career_intelligence": intel.career_intelligence,
        "career_growth": intel.career_growth,
        "specializations": intel.specializations
    })

@router.get("/{id}/technical-analysis", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_technical_analysis(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get candidate skill proficiency details.
    """
    repo = CandidateIntelligenceRepository(db)
    intel = await repo.get_candidate_intelligence(id)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate intelligence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=intel.technical_intelligence)

@router.get("/{id}/leadership-analysis", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_leadership_analysis(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get candidate leadership metrics and evidence.
    """
    repo = CandidateIntelligenceRepository(db)
    intel = await repo.get_candidate_intelligence(id)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate intelligence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=intel.leadership_intelligence)

@router.get("/{id}/projects-analysis", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_projects_analysis(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get candidate project ratings and details.
    """
    repo = CandidateIntelligenceRepository(db)
    intel = await repo.get_candidate_intelligence(id)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate intelligence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=intel.project_intelligence)

@router.get("/{id}/domains", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_candidate_domains(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get candidate industry vertical details.
    """
    repo = CandidateIntelligenceRepository(db)
    intel = await repo.get_candidate_intelligence(id)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate intelligence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=intel.domain_intelligence)

@router.get("/{id}/trace", response_model=EnvelopeResponse[List[Dict[str, Any]]])
async def get_candidate_trace(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get candidate agent execution trace.
    """
    repo = CandidateIntelligenceRepository(db)
    intel = await repo.get_candidate_intelligence(id)
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate intelligence for ID '{id}' not found."
        )
    return EnvelopeResponse(data=intel.trace)
