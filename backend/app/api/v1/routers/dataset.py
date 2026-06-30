import os
import gzip
import json
import csv
import time
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.config.config import settings
from app.api.v1.dependencies.db import get_db
from app.api.v1.dependencies.auth import get_current_user
from app.schemas.responses import EnvelopeResponse
from app.schemas.candidate import (
    CandidateProfile, PersonalInfo, ExperienceDetail, ProjectDetail,
    EducationDetail, SkillDetail, CertificationDetail, BehaviorSignals,
    CandidateMetadata, EngineeredFeatures
)
from app.database.repositories.candidate import CandidateRepository
from app.database.models.candidate import Candidate, EngineeredFeature, Skill
from app.database.models.dataset_management import Dataset, DatasetVersion, ImportHistory, EmbeddingMetadata, IndexMetadata
from app.services.dataset_management_service import dataset_mgmt_service, progress_tracker, map_entity_to_profile
from app.services.pipeline import pipeline

router = APIRouter(prefix="/api/v1/dataset", tags=["Dataset Operations"])
root_router = APIRouter(prefix="/dataset", tags=["Dataset Operations Root Endpoints"])

# ----------------- UPLOAD ENDPOINT -----------------
@router.post("/upload", response_model=EnvelopeResponse[dict[str, Any]])
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    dest_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    
    try:
        with open(dest_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

    # Perform validation
    is_valid, error_msg = dataset_mgmt_service.validate_file(dest_path)
    if not is_valid:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Estimate candidate count
    estimate = 0
    try:
        if dest_path.endswith(".gz"):
            with gzip.open(dest_path, "rt", encoding="utf-8") as f:
                estimate = sum(1 for line in f if line.strip())
        elif dest_path.endswith(".csv"):
            with open(dest_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                estimate = sum(1 for _ in reader)
        else:
            with open(dest_path, "r", encoding="utf-8") as f:
                estimate = sum(1 for line in f if line.strip())
    except Exception:
        estimate = 0

    return EnvelopeResponse(
        data={
            "filepath": dest_path,
            "filename": file.filename,
            "file_size": os.path.getsize(dest_path),
            "estimated_candidates": estimate,
            "status": "validation_success"
        }
    )

# ----------------- PROCESS ENDPOINT (SYNCHRONOUS COMPATIBILITY) -----------------
@router.post("/process", response_model=EnvelopeResponse[dict[str, Any]])
async def process_dataset(
    filepath: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path is invalid or does not exist."
        )

    # 1. Parse file to count records
    records = []
    try:
        ext = os.path.splitext(filepath)[1].lower()
        if filepath.endswith(".jsonl.gz"):
            ext = ".jsonl.gz"

        if ext == ".jsonl.gz":
            with gzip.open(filepath, "rt", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        elif ext == ".jsonl":
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        elif ext == ".csv":
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                records = [dict(row) for row in reader]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse file: {str(e)}"
        )

    total_records = len(records)

    # 2. Run the import pipeline synchronously
    dataset_name = os.path.basename(filepath)
    await dataset_mgmt_service._run_import(filepath, dataset_name, db)

    return EnvelopeResponse(
        data={
            "total_records": total_records,
            "successful_inserts": total_records
        }
    )

# ----------------- IMPORT ENDPOINT -----------------
@router.post("/import", response_model=EnvelopeResponse[dict[str, str]])
async def import_dataset(
    background_tasks: BackgroundTasks,
    payload: dict,
    current_user: dict = Depends(get_current_user)
):
    filepath = payload.get("filepath")
    dataset_name = payload.get("dataset_name") or os.path.basename(filepath)

    if not filepath or not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File path is invalid or does not exist."
        )

    # Trigger async pipeline in background task
    background_tasks.add_task(dataset_mgmt_service.import_pipeline, filepath, dataset_name)

    return EnvelopeResponse(
        data={"status": "processing", "message": "Import pipeline triggered successfully."}
    )

# ----------------- EMBEDDINGS ENDPOINT -----------------
@router.post("/build-embeddings", response_model=EnvelopeResponse[dict[str, str]])
async def build_embeddings(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Find active dataset
    result = await db.execute(select(Dataset).order_by(desc(Dataset.created_at)).limit(1))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No dataset uploaded yet.")

    # Trigger import/embedding build pipeline
    background_tasks.add_task(dataset_mgmt_service.import_pipeline, dataset.file_path, dataset.name)
    
    return EnvelopeResponse(
        data={"status": "processing", "message": "Embedding building triggered successfully."}
    )

# ----------------- VECTOR INDEX ENDPOINT -----------------
@router.post("/build-index", response_model=EnvelopeResponse[dict[str, str]])
async def build_index(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(select(Dataset).order_by(desc(Dataset.created_at)).limit(1))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No dataset uploaded yet.")

    background_tasks.add_task(dataset_mgmt_service.import_pipeline, dataset.file_path, dataset.name)
    
    return EnvelopeResponse(
        data={"status": "processing", "message": "Vector indexing triggered successfully."}
    )

# ----------------- STATUS ENDPOINT -----------------
@router.get("/status", response_model=EnvelopeResponse[dict[str, Any]])
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Fetch active dataset details
    res = await db.execute(select(Dataset).order_by(desc(Dataset.created_at)).limit(1))
    dataset = res.scalar_one_or_none()
    
    dataset_status = {
        "loaded": False,
        "name": None,
        "upload_date": None,
        "total_candidates": 0,
        "embeddings_generated": 0,
        "vector_index": "Not Ready",
        "storage_size": "0 KB",
        "status": "No Dataset"
    }

    if dataset:
        dataset_status["loaded"] = dataset.status == "ready"
        dataset_status["name"] = dataset.name
        dataset_status["upload_date"] = dataset.created_at.strftime("%Y-%m-%d %H:%M:%S") if dataset.created_at else None
        dataset_status["total_candidates"] = dataset.total_candidates
        dataset_status["embeddings_generated"] = dataset.embeddings_generated
        
        # Check FAISS index
        res_idx = await db.execute(select(IndexMetadata).order_by(desc(IndexMetadata.updated_at)).limit(1))
        idx_meta = res_idx.scalar_one_or_none()
        if idx_meta and idx_meta.status == "ready":
            dataset_status["vector_index"] = "Ready"
        else:
            dataset_status["vector_index"] = "Not Ready"

        # Format file size
        size_bytes = dataset.file_size
        if size_bytes > 1024 * 1024:
            dataset_status["storage_size"] = f"{round(size_bytes / (1024 * 1024), 2)} MB"
        else:
            dataset_status["storage_size"] = f"{round(size_bytes / 1024, 2)} KB"
        
        dataset_status["status"] = "Ready for Analysis" if dataset.status == "ready" else "Processing"

    progress = progress_tracker.get_state()

    status_str = "complete"
    if dataset:
        if dataset.status == "ready":
            status_str = "complete"
        elif dataset.status == "processing":
            status_str = "processing"
        elif dataset.status == "failed":
            status_str = "failed"
    
    last_uploaded_file = dataset.file_path if dataset else None

    return EnvelopeResponse(
        data={
            "status": status_str,
            "last_uploaded_file": last_uploaded_file,
            "dataset": dataset_status,
            "progress": progress
        }
    )

# ----------------- HISTORY ENDPOINT -----------------
@router.get("/history", response_model=EnvelopeResponse[list[dict]])
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    res = await db.execute(select(ImportHistory).order_by(desc(ImportHistory.created_at)).limit(50))
    history = res.scalars().all()
    
    return EnvelopeResponse(
        data=[
            {
                "id": h.id,
                "filename": h.filename,
                "file_size": h.file_size,
                "total_records": h.total_records,
                "successful_records": h.successful_records,
                "failed_records": h.failed_records,
                "duration_sec": round(h.duration_sec, 2),
                "status": h.status,
                "error_message": h.error_message,
                "created_at": h.created_at.strftime("%Y-%m-%d %H:%M:%S") if h.created_at else None
            }
            for h in history
        ]
    )

# ----------------- STATISTICS ENDPOINT -----------------
@router.get("/statistics", response_model=EnvelopeResponse[dict[str, Any]])
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = CandidateRepository(db)
    base_stats = await repo.get_dataset_analytics()

    # Calculate education distribution
    edu_query = select(
        EngineeredFeature.education_level,
        func.count(EngineeredFeature.id).label("count")
    ).group_by(EngineeredFeature.education_level)
    edu_res = await db.execute(edu_query)
    
    edu_dist = {}
    for row in edu_res.all():
        level = row[0] or "Unknown"
        edu_dist[level] = row[1]

    # Calculate experience distribution
    exp_ranges = {
        "Junior (0-2 yrs)": 0,
        "Mid (3-5 yrs)": 0,
        "Senior (6-9 yrs)": 0,
        "Lead (10+ yrs)": 0
    }
    
    exp_query = select(EngineeredFeature.years_experience)
    exp_res = await db.execute(exp_query)
    for exp in exp_res.scalars().all():
        years = float(exp or 0.0)
        if years <= 2:
            exp_ranges["Junior (0-2 yrs)"] += 1
        elif years <= 5:
            exp_ranges["Mid (3-5 yrs)"] += 1
        elif years <= 9:
            exp_ranges["Senior (6-9 yrs)"] += 1
        else:
            exp_ranges["Lead (10+ yrs)"] += 1

    # Unique skills count
    skills_count = await db.scalar(select(func.count(func.distinct(Skill.normalized_name)))) or 0

    return EnvelopeResponse(
        data={
            "total_candidates": base_stats["total_candidates"],
            "average_experience": base_stats["average_experience_years"],
            "unique_skills_count": skills_count,
            "education_distribution": edu_dist,
            "experience_distribution": exp_ranges,
            "top_skills": base_stats["top_skills"]
        }
    )

# ----------------- RESET ENDPOINT -----------------
@router.delete("/reset", response_model=EnvelopeResponse[dict[str, str]])
async def reset_dataset(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    await dataset_mgmt_service.reset_dataset(db)
    return EnvelopeResponse(data={"status": "success", "message": "All datasets and vector indexes have been cleared."})


# ----------------- BASE LISTING ENDPOINTS -----------------
@router.get("/candidates", response_model=EnvelopeResponse[dict])
async def list_candidates(
    page: int = 1,
    page_size: int = 50,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Paginated, lightweight candidate listing.
    Uses raw SQL projections to avoid loading full ORM objects with all relationships.
    """
    # Clamp page_size to a reasonable range
    page_size = max(1, min(page_size, 200))
    offset = (max(1, page) - 1) * page_size

    # Build base query for candidates joined with features
    base_q = (
        select(
            Candidate.id,
            Candidate.first_name,
            Candidate.last_name,
            Candidate.email,
            Candidate.phone,
            Candidate.location,
            EngineeredFeature.years_experience,
            EngineeredFeature.education_level,
        )
        .outerjoin(EngineeredFeature, EngineeredFeature.candidate_id == Candidate.id)
    )

    # Optional search filter
    if search.strip():
        search_term = f"%{search.strip().lower()}%"
        from sqlalchemy import or_
        base_q = base_q.where(
            or_(
                func.lower(Candidate.first_name).like(search_term),
                func.lower(Candidate.last_name).like(search_term),
                func.lower(Candidate.id).like(search_term),
                func.lower(Candidate.location).like(search_term),
            )
        )

    # Total count (without pagination)
    count_q = select(func.count()).select_from(base_q.subquery())
    total = await db.scalar(count_q) or 0

    # Paginated rows
    rows_q = base_q.order_by(Candidate.id).offset(offset).limit(page_size)
    result = await db.execute(rows_q)
    rows = result.all()

    # Batch-fetch skills for only these candidate IDs
    cand_ids = [r[0] for r in rows]
    skills_map: dict[str, list[str]] = {cid: [] for cid in cand_ids}
    if cand_ids:
        skills_q = select(Skill.candidate_id, Skill.name).where(Skill.candidate_id.in_(cand_ids))
        skills_result = await db.execute(skills_q)
        for row in skills_result.all():
            skills_map[row[0]].append(row[1])

    candidates_list = [
        {
            "id": r[0],
            "first_name": r[1],
            "last_name": r[2],
            "email": r[3],
            "phone": r[4],
            "location": r[5],
            "years_experience": r[6] if r[6] is not None else 0.0,
            "education": r[7],
            "skills": skills_map.get(r[0], []),
        }
        for r in rows
    ]

    return EnvelopeResponse(data={
        "candidates": candidates_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),  # ceiling division
    })

@router.get("/candidate/{candidate_id}", response_model=EnvelopeResponse[dict])
async def get_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = CandidateRepository(db)
    c = await repo.get_candidate_profile(candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return EnvelopeResponse(
        data={
            "id": c.id,
            "first_name": c.first_name,
            "last_name": c.last_name,
            "email": c.email,
            "phone": c.phone,
            "location": c.location
        }
    )

@router.get("/candidate/{candidate_id}/profile", response_model=EnvelopeResponse[CandidateProfile])
async def get_candidate_profile(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = CandidateRepository(db)
    c = await repo.get_candidate_profile(candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return EnvelopeResponse(data=map_entity_to_profile(c))

@router.get("/candidate/{candidate_id}/career", response_model=EnvelopeResponse[list[ExperienceDetail]])
async def get_candidate_career(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = CandidateRepository(db)
    c = await repo.get_candidate_profile(candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    profile = map_entity_to_profile(c)
    return EnvelopeResponse(data=profile.experiences)

@router.get("/candidate/{candidate_id}/projects", response_model=EnvelopeResponse[list[ProjectDetail]])
async def get_candidate_projects(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = CandidateRepository(db)
    c = await repo.get_candidate_profile(candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    profile = map_entity_to_profile(c)
    return EnvelopeResponse(data=profile.projects)

@router.get("/candidate/{candidate_id}/skills", response_model=EnvelopeResponse[list[SkillDetail]])
async def get_candidate_skills(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = CandidateRepository(db)
    c = await repo.get_candidate_profile(candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    profile = map_entity_to_profile(c)
    return EnvelopeResponse(data=profile.skills)


# Expose root endpoints mapped to the exact same handlers
@root_router.post("/upload")
async def upload_dataset_root(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    return await upload_dataset(file, current_user)

@root_router.post("/process")
async def process_dataset_root(filepath: str, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await process_dataset(filepath, db, current_user)

@root_router.post("/import")
async def import_dataset_root(background_tasks: BackgroundTasks, payload: dict, current_user: dict = Depends(get_current_user)):
    return await import_dataset(background_tasks, payload, current_user)

@root_router.post("/build-embeddings")
async def build_embeddings_root(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await build_embeddings(background_tasks, db, current_user)

@root_router.post("/build-index")
async def build_index_root(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await build_index(background_tasks, db, current_user)

@root_router.get("/status")
async def get_status_root(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await get_status(db, current_user)

@root_router.get("/history")
async def get_history_root(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await get_history(db, current_user)

@root_router.get("/statistics")
async def get_statistics_root(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await get_statistics(db, current_user)

@root_router.delete("/reset")
async def reset_dataset_root(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return await reset_dataset(db, current_user)
