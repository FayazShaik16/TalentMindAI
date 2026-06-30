from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

class PersonalInfo(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None

class ExperienceDetail(BaseModel):
    company_name: str
    job_title: str
    start_date: str | datetime | None = None
    end_date: str | datetime | None = None
    description: str | None = None
    is_current: bool = False

class ProjectDetail(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    domain: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    duration_months: int | None = None

class EducationDetail(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | datetime | None = None
    end_date: str | datetime | None = None

class SkillDetail(BaseModel):
    name: str
    normalized_name: str | None = None
    category: str | None = None
    hierarchy_path: list[str] = Field(default_factory=list)

class CertificationDetail(BaseModel):
    name: str
    issuing_organization: str | None = None
    issue_date: str | datetime | None = None
    expiration_date: str | datetime | None = None

class BehaviorSignals(BaseModel):
    working_style: str | None = None
    leadership_exposure: bool = False
    average_tenure_years: float = 0.0
    career_stability_score: float = 0.0

class EngineeredFeatures(BaseModel):
    years_experience: float = 0.0
    distinct_companies: int = 0
    average_tenure: float = 0.0
    career_stability: float = 0.0
    project_count: int = 0
    certification_count: int = 0
    education_level: str | None = None
    technology_diversity: int = 0
    domain_diversity: int = 0
    leadership_score: int = 0
    cloud_score: int = 0
    ai_score: int = 0
    blockchain_score: int = 0
    cybersecurity_score: int = 0

class CandidateMetadata(BaseModel):
    file_hash: str | None = None
    version: int = 1
    raw_payload_checksum: str | None = None
    processing_duration_sec: float = 0.0

class CandidateProfile(BaseModel):
    id: str
    personal_info: PersonalInfo
    experiences: list[ExperienceDetail] = Field(default_factory=list)
    projects: list[ProjectDetail] = Field(default_factory=list)
    educations: list[EducationDetail] = Field(default_factory=list)
    skills: list[SkillDetail] = Field(default_factory=list)
    certifications: list[CertificationDetail] = Field(default_factory=list)
    behavior_signals: BehaviorSignals = Field(default_factory=BehaviorSignals)
    metadata: CandidateMetadata = Field(default_factory=CandidateMetadata)
    engineered_features: EngineeredFeatures = Field(default_factory=EngineeredFeatures)
