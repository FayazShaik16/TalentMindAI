from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List
from datetime import datetime, timezone

from app.api.v1.dependencies.db import get_db
from app.api.v1.dependencies.auth import get_current_user
from app.schemas.responses import EnvelopeResponse
from app.schemas.job import JobAnalyzeRequest, JobParseRequest, JobResponse, JobIntentProfileSchema
from app.database.repositories.job import JobRepository
from app.database.models.job import JobDescription
from app.services.agents.orchestrator import orchestrator
from app.services.intent_parser import intent_parser
from app.core.logging.logging import logger
from app.utils.document_parser import parse_document

router = APIRouter(prefix="/jobs", tags=["Job Intelligence"])

def map_db_to_response(db_job: JobDescription) -> JobResponse:
    """
    Map database JobDescription model to JobResponse Pydantic schema.
    """
    # Enforce timezone or standard datetime handling
    created = db_job.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    updated = db_job.updated_at
    if updated and updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
        
    return JobResponse(
        id=db_job.id,
        raw_text=db_job.raw_text,
        title=db_job.title,
        department=db_job.department,
        seniority=db_job.seniority,
        experience_required=db_job.experience_required,
        employment_type=db_job.employment_type,
        remote_type=db_job.remote_type,
        intent_profile=JobIntentProfileSchema(**db_job.intent_profile),
        intent_graph=db_job.intent_graph,
        trace=db_job.trace,
        confidence_scores={k: float(v) for k, v in db_job.confidence_scores.items()},
        created_at=created,
        updated_at=updated
    )

@router.post("/analyze", response_model=EnvelopeResponse[JobResponse])
async def analyze_job(
    payload: JobAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Runs the full Job Intelligence Agent pipeline through the Orchestrator,
    generating intent profiles, graphs, embeddings, and saves to database.
    """
    logger.info("api_analyze_job_start", job_id=payload.id)
    
    # 1. Run the agent pipeline
    context = {"job_id": payload.id}
    try:
        # We execute the "job_intelligence" agent in the orchestrator pipeline
        final_output, updated_context, pipeline_trace = await orchestrator.execute_pipeline(
            pipeline=["job_intelligence"],
            initial_input=payload.raw_text,
            context=context
        )
    except Exception as e:
        logger.error("api_analyze_job_pipeline_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Pipeline failed: {str(e)}"
        )

    # 2. Persist profile results
    repo = JobRepository(db)
    job_model = JobDescription(
        id=final_output["job_id"],
        raw_text=final_output["raw_text"],
        title=final_output["title"],
        department=final_output["department"],
        seniority=final_output["seniority"],
        experience_required=final_output["experience_required"],
        employment_type=final_output["employment_type"],
        remote_type=final_output["remote_type"],
        intent_profile=final_output["intent_profile"],
        intent_graph=final_output["intent_graph"],
        trace=pipeline_trace, # Store Orchestrator execution trace
        confidence_scores=final_output["confidence_scores"]
    )
    
    try:
        saved_job = await repo.upsert_job_description(job_model)
        await db.commit()
    except Exception as e:
        logger.error("api_analyze_job_save_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist job description analysis."
        )

    response_data = map_db_to_response(saved_job)
    return EnvelopeResponse(data=response_data)

@router.post("/parse", response_model=EnvelopeResponse[Dict[str, Any]])
async def parse_job(
    payload: JobParseRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Quickly structures the raw job description without saving or running vector embedding.
    """
    try:
        parsed_res = await intent_parser.parse(payload.raw_text)
        return EnvelopeResponse(data=parsed_res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intent parser failed: {str(e)}"
        )

@router.post("/parse-file", response_model=EnvelopeResponse[Dict[str, Any]])
async def parse_job_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Parses an uploaded job description file (PDF, DOCX, TXT, MD) and extracts the raw text.
    """
    try:
        content = await file.read()
        parsed_text = parse_document(file.filename or "", content)
        return EnvelopeResponse(data={"text": parsed_text})
    except Exception as e:
        logger.error("api_parse_job_file_failed", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse file: {str(e)}"
        )

@router.get("", response_model=EnvelopeResponse[List[JobResponse]])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all processed job descriptions in the database.
    """
    repo = JobRepository(db)
    jobs = await repo.get_all()
    return EnvelopeResponse(data=[map_db_to_response(j) for j in jobs])

@router.get("/{id}", response_model=EnvelopeResponse[JobResponse])
async def get_job(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch a fully processed job profile by ID.
    """
    repo = JobRepository(db)
    job = await repo.get_job_description(id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{id}' not found."
        )
    return EnvelopeResponse(data=map_db_to_response(job))

@router.get("/{id}/intent", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_job_intent(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch the recruiter intent profile of a job description by ID.
    """
    repo = JobRepository(db)
    job = await repo.get_job_description(id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{id}' not found."
        )
    return EnvelopeResponse(data=job.intent_profile)

@router.get("/{id}/graph", response_model=EnvelopeResponse[Dict[str, Any]])
async def get_job_graph(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch the semantic recruiter intent graph of a job description by ID.
    """
    repo = JobRepository(db)
    job = await repo.get_job_description(id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{id}' not found."
        )
    return EnvelopeResponse(data=job.intent_graph)

@router.get("/{id}/trace", response_model=EnvelopeResponse[List[Dict[str, Any]]])
async def get_job_trace(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch the execution pipeline trace of a job description by ID.
    """
    repo = JobRepository(db)
    job = await repo.get_job_description(id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job description with ID '{id}' not found."
        )
    return EnvelopeResponse(data=job.trace)
