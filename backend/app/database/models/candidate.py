import uuid
from sqlalchemy import ForeignKey, String, Text, Integer, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin, SoftDeleteMixin

class Candidate(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "candidate"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Database relations
    experiences: Mapped[list["Experience"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    educations: Mapped[list["Education"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    certifications: Mapped[list["Certification"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan", lazy="selectin"
    )
    metadata_record: Mapped["CandidateMetadata | None"] = relationship(
        back_populates="candidate", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    features: Mapped["EngineeredFeature | None"] = relationship(
        back_populates="candidate", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )

class Experience(Base):
    __tablename__ = "experience"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), index=True, nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    candidate: Mapped[Candidate] = relationship(back_populates="experiences")

class Project(Base):
    __tablename__ = "project"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responsibilities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)

    candidate: Mapped[Candidate] = relationship(back_populates="projects")

class Education(Base):
    __tablename__ = "education"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), index=True, nullable=False
    )
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(100), nullable=True)

    candidate: Mapped[Candidate] = relationship(back_populates="educations")

class Skill(Base):
    __tablename__ = "skill"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hierarchy_path: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="skills")

class Certification(Base):
    __tablename__ = "certification"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuing_organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiration_date: Mapped[str | None] = mapped_column(String(100), nullable=True)

    candidate: Mapped[Candidate] = relationship(back_populates="certifications")

class CandidateMetadata(Base):
    __tablename__ = "candidate_metadata"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    file_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    raw_payload_checksum: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processing_duration_sec: Mapped[float] = mapped_column(Float, default=0.0)

    candidate: Mapped[Candidate] = relationship(back_populates="metadata_record")

class EngineeredFeature(Base):
    __tablename__ = "engineered_feature"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[str] = mapped_column(
        ForeignKey("candidate.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    years_experience: Mapped[float] = mapped_column(Float, default=0.0)
    distinct_companies: Mapped[int] = mapped_column(Integer, default=0)
    average_tenure: Mapped[float] = mapped_column(Float, default=0.0)
    career_stability: Mapped[float] = mapped_column(Float, default=0.0)
    project_count: Mapped[int] = mapped_column(Integer, default=0)
    certification_count: Mapped[int] = mapped_column(Integer, default=0)
    education_level: Mapped[str | None] = mapped_column(String(255), nullable=True)
    technology_diversity: Mapped[int] = mapped_column(Integer, default=0)
    domain_diversity: Mapped[int] = mapped_column(Integer, default=0)
    leadership_score: Mapped[int] = mapped_column(Integer, default=0)
    cloud_score: Mapped[int] = mapped_column(Integer, default=0)
    ai_score: Mapped[int] = mapped_column(Integer, default=0)
    blockchain_score: Mapped[int] = mapped_column(Integer, default=0)
    cybersecurity_score: Mapped[int] = mapped_column(Integer, default=0)

    candidate: Mapped[Candidate] = relationship(back_populates="features")
