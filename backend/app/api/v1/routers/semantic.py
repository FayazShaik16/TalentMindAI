import time
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.config import settings
from app.api.v1.dependencies.db import get_db
from app.api.v1.dependencies.auth import get_current_user
from app.schemas.responses import EnvelopeResponse
from app.database.repositories.candidate import CandidateRepository
from app.database.models.candidate import Candidate
from app.api.v1.routers.dataset import map_entity_to_profile
from app.services.embedding_service import embedding_service
from app.services.search_engine import search_engine
from app.providers.vector.faiss import FAISSProvider

router = APIRouter(prefix="/api/v1/semantic", tags=["Semantic Intelligence Engine"])

# Request/Response schemas for endpoint validation
class SearchRequest(BaseModel):
    query: str = Field(..., description="Recruiter text search prompt.")
    collection: str = Field("summary", description="Candidate sub-vector space: summary, career, projects, skills, education.")
    limit: int = Field(10, ge=1, le=1000, description="Top-K candidates threshold.")
    filter_metadata: dict[str, Any] | None = Field(None, description="Metadata filters (years_experience, location, skills, education).")

class IndexCandidateRequest(BaseModel):
    candidate_id: str = Field(..., description="ID of candidate to build vectors for.")

async def index_candidate_profile(candidate: Candidate, db: AsyncSession, provider: FAISSProvider) -> bool:
    """
    Helper function to generate embeddings for a candidate and write them to the FAISS collections.
    """
    profile = map_entity_to_profile(candidate)
    
    # 1. Generate embeddings (checks persistent SQLite cache)
    embeddings = await embedding_service.get_candidate_embeddings(profile)
    
    # 2. Map metadata payload for pre-filtering
    payload = {
        "candidate_id": profile.id,
        "first_name": profile.personal_info.first_name,
        "last_name": profile.personal_info.last_name,
        "email": profile.personal_info.email,
        "phone": profile.personal_info.phone,
        "location": profile.personal_info.location,
        "years_experience": profile.engineered_features.years_experience,
        "skills": [s.normalized_name or s.name for s in profile.skills],
        "education": profile.engineered_features.education_level,
        "domains": [p.domain for p in profile.projects if p.domain],
        "current_company": profile.experiences[-1].company_name if profile.experiences else None,
        "availability": True
    }
    
    # 3. Upsert to FAISS collections
    for e_type, vector in embeddings.items():
        await provider.upsert(
            collection_name=e_type,
            ids=[profile.id],
            embeddings=[vector],
            payloads=[payload]
        )
    return True

@router.post("/embeddings/build", response_model=EnvelopeResponse[dict])
async def build_embeddings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generates embeddings and builds FAISS indexes for all candidates not currently cached/indexed.
    """
    start_time = time.perf_counter()
    repo = CandidateRepository(db)
    candidates = await repo.get_all() # Retrieval of all candidate records
    
    provider = FAISSProvider()
    processed_count = 0
    
    for cand in candidates:
        await index_candidate_profile(cand, db, provider)
        processed_count += 1
        
    duration = time.perf_counter() - start_time
    
    return EnvelopeResponse(
        data={
            "status": "success",
            "total_candidates": len(candidates),
            "processed_count": processed_count,
            "duration_sec": round(duration, 3)
        }
    )

@router.post("/embeddings/rebuild", response_model=EnvelopeResponse[dict])
async def rebuild_embeddings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Deletes all index files and clears the cache, then executes a fresh vector build.
    """
    start_time = time.perf_counter()
    
    # 1. Clear embedding cache
    embedding_service.clear_cache()
    
    # 2. Clear FAISS index files
    provider = FAISSProvider()
    collections = ["summary", "career", "projects", "skills", "education"]
    for col in collections:
        await provider.clear_collection(col)
        
    # 3. Retrieve and re-index candidates
    repo = CandidateRepository(db)
    candidates = await repo.get_all()
    
    processed_count = 0
    for cand in candidates:
        await index_candidate_profile(cand, db, provider)
        processed_count += 1
        
    duration = time.perf_counter() - start_time
    
    return EnvelopeResponse(
        data={
            "status": "success",
            "message": "Rebuild completed from scratch.",
            "total_candidates": len(candidates),
            "processed_count": processed_count,
            "duration_sec": round(duration, 3)
        }
    )

@router.get("/embeddings/status", response_model=EnvelopeResponse[dict])
async def get_embeddings_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns indexing and model configuration status.
    """
    provider = FAISSProvider()
    collections = ["summary", "career", "projects", "skills", "education"]
    collection_stats = {}
    
    for col in collections:
        stats = await provider.get_statistics(col)
        collection_stats[col] = stats
        
    # Get SQLite cache count
    cache_count = 0
    try:
        import sqlite3
        with sqlite3.connect(embedding_service.db_path) as conn:
            cursor = conn.execute("SELECT count(*) FROM cache")
            cache_count = cursor.fetchone()[0]
    except Exception:
        pass

    return EnvelopeResponse(
        data={
            "active_model": settings.EMBEDDING_MODEL,
            "dimension": settings.EMBEDDING_DIMENSION,
            "provider": settings.EMBEDDING_PROVIDER,
            "cache_entries_count": cache_count,
            "collections": collection_stats
        }
    )

@router.get("/embeddings/models", response_model=EnvelopeResponse[dict])
async def get_supported_models(
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieves supported text embedding models.
    """
    return EnvelopeResponse(
        data={
            "active_model": settings.EMBEDDING_MODEL,
            "supported_models": [
                {
                    "name": "BAAI/bge-small-en-v1.5",
                    "dimension": 384,
                    "description": "Fast and lightweight local embeddings."
                },
                {
                    "name": "BAAI/bge-base-en-v1.5",
                    "dimension": 768,
                    "description": "Standard high-performance local embeddings (Default)."
                },
                {
                    "name": "BAAI/bge-large-en-v1.5",
                    "dimension": 1024,
                    "description": "Deep context semantic embeddings."
                },
                {
                    "name": "Jina Embeddings v3",
                    "dimension": 1024,
                    "description": "Multi-lingual large context embeddings."
                }
            ]
        }
    )

@router.post("/search", response_model=EnvelopeResponse[dict])
async def post_semantic_search(
    req: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Runs Top-K similarity vector queries on a sub-index with optional pre-filtering.
    """
    results = await search_engine.search(
        query=req.query,
        collection_name=req.collection,
        limit=req.limit,
        filter_metadata=req.filter_metadata
    )
    return EnvelopeResponse(data=results)

@router.post("/index", response_model=EnvelopeResponse[dict])
async def index_candidate(
    req: IndexCandidateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually indexes or updates vector embeddings for a single candidate profile.
    """
    repo = CandidateRepository(db)
    cand = await repo.get_candidate_profile(req.candidate_id)
    if not cand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {req.candidate_id} not found."
        )
        
    provider = FAISSProvider()
    await index_candidate_profile(cand, db, provider)
    
    return EnvelopeResponse(
        data={
            "status": "success",
            "candidate_id": req.candidate_id,
            "message": "Candidate vectors indexed successfully."
        }
    )

@router.get("/statistics", response_model=EnvelopeResponse[dict])
async def get_semantic_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Returns diagnostic statistics across FAISS vector store.
    """
    provider = FAISSProvider()
    collections = ["summary", "career", "projects", "skills", "education"]
    stats = {}
    
    for col in collections:
        col_stats = await provider.get_statistics(col)
        stats[col] = col_stats
        
    return EnvelopeResponse(data=stats)


# Root endpoints requested in the prompt
root_router = APIRouter(tags=["Semantic Retrieval Engine Root Endpoints"])

@root_router.post("/embeddings/build", response_model=EnvelopeResponse[dict])
async def build_embeddings_root(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Exposes POST /embeddings/build at the root level.
    """
    return await build_embeddings(db, current_user)

@root_router.post("/semantic/search", response_model=EnvelopeResponse[dict])
async def post_semantic_search_root(
    req: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Exposes POST /semantic/search at the root level.
    """
    return await post_semantic_search(req, current_user)

@root_router.get("/semantic/status", response_model=EnvelopeResponse[dict])
async def get_embeddings_status_root(
    current_user: dict = Depends(get_current_user)
):
    """
    Exposes GET /semantic/status at the root level.
    """
    return await get_embeddings_status(current_user)

