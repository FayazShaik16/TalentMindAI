from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

class JobAnalyzeRequest(BaseModel):
    raw_text: str = Field(..., min_length=20, description="The raw unstructured job description text.")
    id: Optional[str] = Field(None, description="Optional job ID. If not provided, a deterministic hash of the text is generated.")

class JobParseRequest(BaseModel):
    raw_text: str = Field(..., min_length=20, description="The raw unstructured job description text to parse.")

class JobFeatureSchema(BaseModel):
    required_experience: float
    preferred_experience: float
    leadership_required: bool
    ai_experience: bool
    cloud_experience: bool
    blockchain_experience: bool
    cybersecurity_experience: bool
    full_stack_experience: bool
    management_exposure: bool
    startup_preference: bool
    enterprise_preference: bool
    remote_compatibility: str

class JobSkillsSchema(BaseModel):
    primary_skills: List[str]
    secondary_skills: List[str]
    programming_languages: List[str]
    tools: List[str]
    frameworks: List[str]
    cloud_platforms: List[str]
    soft_skills: List[str]
    certifications: List[str]

class JobIntentProfileSchema(BaseModel):
    title: str
    department: str
    seniority: str
    employment_type: str
    experience_required_years: float
    education: List[str]
    skills: JobSkillsSchema
    industry: str
    location: str
    remote_compatibility: str
    salary: Optional[Dict[str, Any]] = None
    classified_skills: List[Dict[str, Any]] = Field(default_factory=list)
    engineered_features: Optional[JobFeatureSchema] = None

class JobResponse(BaseModel):
    id: str
    raw_text: str
    title: str
    department: Optional[str] = None
    seniority: Optional[str] = None
    experience_required: Optional[float] = None
    employment_type: Optional[str] = None
    remote_type: Optional[str] = None
    intent_profile: JobIntentProfileSchema
    intent_graph: Dict[str, Any]
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
