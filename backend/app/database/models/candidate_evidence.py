from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.database.models.candidate import Candidate

class CandidateEvidence(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "candidate_evidence"

    candidate_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )

    skill_verification: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    timeline: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    potential_metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    risk_analysis: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    evidence_graph: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    trace: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    confidence_scores: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    candidate: Mapped[Candidate] = relationship("Candidate", lazy="selectin")
