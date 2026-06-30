from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.database.models.job import JobDescription

class JobCandidateRanking(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "job_candidate_ranking"

    job_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("job_description.id", ondelete="CASCADE"),
        primary_key=True,
        index=True
    )
    # List of ranked candidates with scores and explanations
    rankings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Process trace log
    trace: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Execution telemetry/observability metrics
    statistics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    job: Mapped[JobDescription] = relationship("JobDescription", lazy="selectin")
