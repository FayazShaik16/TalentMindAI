from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List
import os

from app.api.v1.dependencies.db import get_db
from app.api.v1.dependencies.auth import get_current_user
from app.schemas.responses import EnvelopeResponse
from app.schemas.explanation import (
    ExplanationPackageResponse, StrengthResponse, WeaknessResponse,
    CandidateCompareRequest, AuditTrailResponse
)
from app.database.repositories.explanation import ExplanationRepository
from app.database.repositories.job import JobRepository
from app.database.repositories.candidate import CandidateRepository
from app.database.models.explanation import JobCandidateExplanation
from app.api.v1.routers.candidate_intelligence import sanitize_for_json
from app.services.explainability.comparison import CandidateComparisonEngine, DecisionIntelligenceEngine
from app.services.explainability.pdf_exporter import SimplePDFExporter
from app.services.agents.orchestrator import orchestrator
from app.core.logging.logging import logger

router = APIRouter(tags=["Explainability Engine & Recruiter Decision Intelligence"])

@router.get("/explain/{job_id}", response_model=EnvelopeResponse[List[ExplanationPackageResponse]])
async def get_job_explanations(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get full explainability packages for all candidates ranked under a job ID.
    If explanations are not calculated yet, runs the explainability pipeline first.
    """
    repo = ExplanationRepository(db)
    exps = await repo.get_all_for_job(job_id)
    
    if not exps:
        # Run explainability pipeline lazily
        logger.info("api_lazy_explainability_invocation", job_id=job_id)
        from app.services.agents.explainability_agent import explainability_agent
        await explainability_agent.initialize()
        
        context = {"db": db}
        try:
            final_output, _, _ = await orchestrator.execute_pipeline(
                pipeline=["explainability"],
                initial_input=job_id,
                context=context
            )
            await db.commit()
            exps = await repo.get_all_for_job(job_id)
        except Exception as e:
            logger.exception("api_explainability_pipeline_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI Explainability execution failed: {str(e)}"
            )

    return EnvelopeResponse(data=[ExplanationPackageResponse(**e.explanation_package) for e in exps])

@router.get("/candidate/{id}/explanation", response_model=EnvelopeResponse[ExplanationPackageResponse])
async def get_candidate_explanation(
    id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get recruiter explanation package for a candidate under a specific job.
    """
    repo = ExplanationRepository(db)
    exp = await repo.get_explanation(job_id, id)
    if not exp:
        # Try running explainability for this candidate specifically
        from app.services.agents.explainability_agent import explainability_agent
        await explainability_agent.initialize()
        
        context = {"db": db, "candidate_ids": [id]}
        try:
            await orchestrator.execute_pipeline(
                pipeline=["explainability"],
                initial_input=job_id,
                context=context
            )
            await db.commit()
            exp = await repo.get_explanation(job_id, id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate candidate explanation: {str(e)}"
            )

    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Explanation for candidate ID '{id}' under job ID '{job_id}' not found."
        )
        
    return EnvelopeResponse(data=ExplanationPackageResponse(**exp.explanation_package))

@router.get("/candidate/{id}/strengths", response_model=EnvelopeResponse[List[StrengthResponse]])
async def get_candidate_strengths(
    id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get ranked technical, leadership and career strengths for a candidate.
    """
    env_res = await get_candidate_explanation(id, job_id, db, current_user)
    return EnvelopeResponse(data=env_res.data.strengths)

@router.get("/candidate/{id}/weaknesses", response_model=EnvelopeResponse[List[WeaknessResponse]])
async def get_candidate_weaknesses(
    id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get identified gaps and risks for a candidate.
    """
    env_res = await get_candidate_explanation(id, job_id, db, current_user)
    return EnvelopeResponse(data=env_res.data.weaknesses)

@router.get("/candidate/{id}/recommendation", response_model=EnvelopeResponse[List[Dict[str, Any]]])
async def get_candidate_interview_plan(
    id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get custom interview focus areas and focus questions.
    """
    env_res = await get_candidate_explanation(id, job_id, db, current_user)
    # Map back the interview_recommendation field
    return EnvelopeResponse(data=[{"topic": a.topic, "questions": a.questions} for a in env_res.data.interview_recommendation])

@router.post("/compare", response_model=EnvelopeResponse[Dict[str, Any]])
async def compare_candidates(
    payload: CandidateCompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Side-by-side comparison of candidate profiles, strengths, missing skills, and scoring breakdowns.
    Also compiles differentiators (Decision Intelligence) between Candidate A and Candidate B.
    """
    repo = ExplanationRepository(db)
    cand_repo = CandidateRepository(db)
    
    packages = []
    for cid in payload.candidate_ids:
        exp = await repo.get_explanation(payload.job_id, cid)
        if not exp:
            # Generate lazily
            from app.services.agents.explainability_agent import explainability_agent
            await explainability_agent.initialize()
            context = {"db": db, "candidate_ids": [cid]}
            await orchestrator.execute_pipeline(
                pipeline=["explainability"],
                initial_input=payload.job_id,
                context=context
            )
            await db.commit()
            exp = await repo.get_explanation(payload.job_id, cid)
            
        if exp:
            cand_profile = await cand_repo.get_candidate_profile(cid)
            pkg = dict(exp.explanation_package)
            pkg["match_breakdown"] = exp.match_breakdown
            pkg["overall_score"] = exp.audit_trail.get("overall_score", 50.0)
            pkg["recommendation"] = exp.audit_trail.get("recommendation", "Interview")
            pkg["personal_info"] = {"first_name": cand_profile.first_name, "last_name": cand_profile.last_name} if cand_profile else {}
            packages.append(pkg)

    if not packages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explanations for the specified candidates under this job description not found."
        )

    # 1. Generate side-by-side matrix
    comp_engine = CandidateComparisonEngine()
    comparison_res = comp_engine.compare(packages)

    # 2. Add decision intelligence differentiators for top 2 candidates if possible
    differentiators_res = None
    if len(packages) >= 2:
        di_engine = DecisionIntelligenceEngine()
        # Compare first candidate with second candidate
        differentiators_res = di_engine.generate_differentiators(packages[0], packages[1])

    result = {
        "job_id": payload.job_id,
        "comparison": comparison_res["comparison_matrix"],
        "decision_intelligence": differentiators_res
    }
    
    return EnvelopeResponse(data=result)

@router.get("/audit/{job_id}", response_model=EnvelopeResponse[List[AuditTrailResponse]])
async def get_job_audit_trails(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get immutable audit trails detailing raw scores, weights, penalties, and inputs for job description decision.
    """
    repo = ExplanationRepository(db)
    exps = await repo.get_all_for_job(job_id)
    
    if not exps:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit logs for Job ID '{job_id}' not found. Trigger ranking/run first."
        )
        
    audit_trails = [AuditTrailResponse(**e.audit_trail) for e in exps]
    return EnvelopeResponse(data=audit_trails)

@router.get("/candidate/{id}/report-pdf")
async def get_recruiter_report_pdf(
    id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate and download Recruiter Report PDF.
    """
    repo = ExplanationRepository(db)
    exp = await repo.get_explanation(job_id, id)
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Explanation package not found. Run ranking first."
        )

    pkg = exp.explanation_package
    
    # Resolve job details
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id)
    job_title = job.title if job else "Software Engineer"
    
    # Resolve candidate details
    cand_repo = CandidateRepository(db)
    cand = await cand_repo.get_candidate_profile(id)
    cand_name = f"{cand.first_name} {cand.last_name}" if cand else "Candidate Profile"

    # Export report path
    os.makedirs("exports", exist_ok=True)
    pdf_path = f"exports/recruiter_report_{job_id}_{id}.pdf"
    
    exporter = SimplePDFExporter()
    exporter.generate_candidate_report(
        filepath=pdf_path,
        title=f"{cand_name} - {job_title}",
        narrative=pkg["overall_summary"],
        strengths=pkg["strengths"],
        weaknesses=pkg["weaknesses"],
        interview_plan={"interview_focus_areas": pkg["interview_recommendation"]}
    )

    return FileResponse(
        path=pdf_path,
        filename=f"recruiter_report_{job_id}_{id}.pdf",
        media_type="application/pdf"
    )
