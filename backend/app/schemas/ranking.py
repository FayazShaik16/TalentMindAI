from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class RankingRunRequest(BaseModel):
    job_id: str = Field(..., description="Job Description ID to rank candidates against.")
    candidate_ids: Optional[List[str]] = Field(None, description="Optional subset list of Candidate IDs to rank. If omitted, ranks all.")
    weights: Optional[Dict[str, float]] = Field(None, description="Optional override weights for the 15 scoring dimensions.")
    top_k_rerank: Optional[int] = Field(None, description="Optional top K candidates to rerank using Cross-Encoder.")

class RecommendationRequest(BaseModel):
    job_id: str = Field(..., description="Job Description ID.")
    candidate_id: str = Field(..., description="Candidate ID to get recommendation for.")

class ScoringDimensionResponse(BaseModel):
    raw_score: float
    normalized_score: float
    confidence: float
    weight: float
    explanation: str

class CandidateRankingResponse(BaseModel):
    rank: int
    candidate_id: str
    first_name: str
    last_name: str
    overall_score: float
    hiring_confidence: float
    recommendation: str
    reasoning_summary: str
    evidence_summary: str
    risk_summary: str
    missing_skills: List[str]
    growth_potential: float
    interview_recommendation: str
    scoring_dimensions: Dict[str, ScoringDimensionResponse]

class RankingResponse(BaseModel):
    job_id: str
    rankings: List[CandidateRankingResponse]
    trace: List[Dict[str, Any]]
    statistics: Dict[str, Any]
