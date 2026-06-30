from pydantic import BaseModel, Field
from typing import Any, Dict, List
from datetime import datetime

class CandidateVerifyRequest(BaseModel):
    candidate_id: str = Field(..., description="ID of the Candidate to run Evidence Verification on.")

class CandidateEvidenceResponse(BaseModel):
    candidate_id: str
    skill_verification: Dict[str, Any]
    timeline: Dict[str, Any]
    potential_metrics: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    evidence_graph: Dict[str, Any]
    confidence_scores: Dict[str, float]
    trace: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
