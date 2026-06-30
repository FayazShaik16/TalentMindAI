from sqlalchemy import String, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.database.models.job import JobDescription

class RecruiterWorkspace(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "recruiter_workspace"

    recruiter_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    search_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    saved_candidates: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    saved_jobs: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    folders: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    tags: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

class JobSession(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "job_session"

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    job_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("job_description.id", ondelete="CASCADE"),
        index=True
    )
    ranking_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    candidate_snapshot: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    ai_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)
    history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    job: Mapped[JobDescription] = relationship("JobDescription", lazy="selectin")

class RecruiterActivity(Base, TimestampMixin):
    __tablename__ = "recruiter_activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recruiter_id: Mapped[str] = mapped_column(String(255), index=True)
    action_type: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
