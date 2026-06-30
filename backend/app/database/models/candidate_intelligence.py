from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.database.models.candidate import Candidate

class CandidateIntelligence(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "candidate_intelligence"

    candidate_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("candidate.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )
    professional_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Inferred structured intelligence categories
    career_intelligence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    technical_intelligence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    leadership_intelligence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    project_intelligence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    domain_intelligence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    career_growth: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    specializations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    knowledge_graph: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Trace telemetry and confidence matrix
    trace: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    confidence_scores: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relational mapping back to Candidate (without modifying Candidate)
    candidate: Mapped[Candidate] = relationship("Candidate", lazy="selectin")
