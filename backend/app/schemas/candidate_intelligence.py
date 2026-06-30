from pydantic import BaseModel, Field
from typing import Any, Dict, List
from datetime import datetime

class CandidateAnalyzeRequest(BaseModel):
    candidate_id: str = Field(..., description="ID of the Candidate to run Career Intelligence analysis on.")

class CandidateIntelligenceResponse(BaseModel):
    candidate_id: str
    professional_summary: str
    career_intelligence: Dict[str, Any]
    technical_intelligence: Dict[str, Any]
    leadership_intelligence: Dict[str, Any]
    project_intelligence: Dict[str, Any]
    domain_intelligence: Dict[str, Any]
    career_growth: Dict[str, Any]
    specializations: List[str]
    behavior_placeholder: Dict[str, Any]
    knowledge_graph: Dict[str, Any]
    confidence_scores: Dict[str, float]
    trace: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
