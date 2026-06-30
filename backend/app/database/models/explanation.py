from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.database.models.candidate import Candidate
from app.database.models.job import JobDescription

class JobCandidateExplanation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "job_candidate_explanation"

    job_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("job_description.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )
    
    candidate_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )

    # Recruiter explanation package
    explanation_package: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Matching disaggregated breakdown matrix
    match_breakdown: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Immutable audit trail inputs
    audit_trail: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Performance log trace
    trace: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    job: Mapped[JobDescription] = relationship("JobDescription", lazy="selectin")
    candidate: Mapped[Candidate] = relationship("Candidate", lazy="selectin")
