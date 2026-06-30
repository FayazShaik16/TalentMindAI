from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

class WorkspacePreferencesRequest(BaseModel):
    ranking_weights: Dict[str, float] = Field(default_factory=dict)
    embedding_model: Optional[str] = None
    reranker_model: Optional[str] = None
    top_k: Optional[int] = None
    similarity_metric: Optional[str] = None
    thresholds: Optional[Dict[str, float]] = None
    export_preferences: Optional[Dict[str, Any]] = None

class WorkspacePreferencesResponse(BaseModel):
    recruiter_id: str
    preferences: Dict[str, Any]

class WorkspaceResponse(BaseModel):
    recruiter_id: str
    preferences: Dict[str, Any]
    search_history: List[Dict[str, Any]]
    saved_candidates: List[str]
    saved_jobs: List[str]
    folders: Dict[str, List[str]]
    tags: Dict[str, List[str]]
    notes: Dict[str, str]

class JobSessionResponse(BaseModel):
    session_id: str
    job_id: str
    ranking_version: int
    candidate_snapshot: List[Dict[str, Any]]
    ai_version: str
    status: str
    history: List[Dict[str, Any]]
    created_at: datetime

class RecruiterActivityResponse(BaseModel):
    id: int
    recruiter_id: str
    action_type: str
    details: Dict[str, Any]
    duration_ms: int
    created_at: datetime
