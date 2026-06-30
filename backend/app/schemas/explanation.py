from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class CandidateCompareRequest(BaseModel):
    job_id: str = Field(..., description="Job Description ID to compare candidates under.")
    candidate_ids: List[str] = Field(..., min_length=2, description="List of Candidate IDs to compare side-by-side.")

class StrengthResponse(BaseModel):
    name: str
    category: str
    evidence: str
    impact: str

class WeaknessResponse(BaseModel):
    name: str
    category: str
    evidence: str
    severity: str

class MissingSkillItem(BaseModel):
    name: str
    learning_effort: str
    actionable_suggestion: str

class MissingSkillsCategory(BaseModel):
    critical_missing: List[MissingSkillItem]
    important_missing: List[MissingSkillItem]
    nice_to_have_missing: List[MissingSkillItem]

class TransferableSkillResponse(BaseModel):
    missing_skill: str
    transferable_skill: str
    explanation: str

class InterviewFocusAreaResponse(BaseModel):
    topic: str
    questions: List[str]

class ExplanationPackageResponse(BaseModel):
    candidate_id: str
    overall_summary: str
    match_percentage: float
    hiring_confidence: float
    strengths: List[StrengthResponse]
    weaknesses: List[WeaknessResponse]
    missing_skills: MissingSkillsCategory
    transferable_skills: List[TransferableSkillResponse]
    career_highlights: List[str]
    evidence_summary: str
    risk_summary: str
    interview_recommendation: List[InterviewFocusAreaResponse]
    improvement_suggestions: List[str]

class AuditTrailResponse(BaseModel):
    job_id: str
    candidate_id: str
    overall_score: float
    hiring_confidence: float
    recommendation: str
    weights_applied: Dict[str, float]
    penalties_applied: float
    evidence_anchors: Dict[str, int]
