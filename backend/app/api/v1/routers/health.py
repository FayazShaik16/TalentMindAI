import os
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.dependencies.db import get_db
from app.schemas.responses import EnvelopeResponse
from app.telemetry.metrics import telemetry
from app.core.config.config import settings
from app.database.repositories.candidate import CandidateRepository
from app.api.v1.routers.dataset import map_entity_to_profile

router = APIRouter()

@router.get("/", response_model=EnvelopeResponse[dict[str, str]])
async def root():
    """
    Service landing description endpoint.
    """
    return EnvelopeResponse(
        data={
            "name": "TalentMind AI API",
            "description": "Candidate Intelligence Platform backend service foundation.",
            "status": "operational"
        }
    )

@router.get("/health", response_model=EnvelopeResponse[dict])
async def health(db: AsyncSession = Depends(get_db)):
    """
    Returns structural system details and database check status.
    """
    db_alive = await telemetry.check_database(db)
    system_stats = telemetry.get_system_metrics()

    status_str = "healthy" if db_alive else "degraded"

    return EnvelopeResponse(
        data={
            "status": status_str,
            "database_connected": db_alive,
            "system_metrics": system_stats
        }
    )

@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    """
    Ready check to confirm database connection parameters. Returns 503 on database failure.
    """
    db_alive = await telemetry.check_database(db)
    if not db_alive:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is degraded"
        )
    return {"status": "ready"}

@router.get("/live")
async def live():
    """
    Liveness check to confirm the web server is running.
    """
    return {"status": "alive"}

@router.get("/version", response_model=EnvelopeResponse[dict[str, str]])
async def version():
    """
    Returns active software release version tags.
    """
    return EnvelopeResponse(
        data={
            "version": "0.1.0",
            "api_version": "v1"
        }
    )

@router.get("/metrics", response_model=EnvelopeResponse[dict])
async def metrics():
    """
    Gathers process telemetry and error statistics.
    """
    return EnvelopeResponse(data=telemetry.get_system_metrics())

@router.get("/system/status", response_model=EnvelopeResponse[dict])
async def system_status(db: AsyncSession = Depends(get_db)):
    """
    Returns system status details and database check status.
    """
    return await health(db)

@router.post("/dataset/upload", response_model=EnvelopeResponse[dict[str, str]])
async def upload_dataset_root(
    file: UploadFile = File(...)
):
    """
    Root alias for dataset uploading.
    """
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
    return EnvelopeResponse(
        data={"filepath": dest_path, "status": "Uploaded successfully."}
    )

@router.get("/candidate/{candidate_id}", response_model=EnvelopeResponse[dict])
async def get_candidate_root(
    candidate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Root alias for candidate retrieval.
    """
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

@router.get("/candidate/{candidate_id}/profile", response_model=EnvelopeResponse[Any])
async def get_candidate_profile_root(
    candidate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Root alias for candidate profile retrieval.
    """
    repo = CandidateRepository(db)
    c = await repo.get_candidate_profile(candidate_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return EnvelopeResponse(data=map_entity_to_profile(c))


