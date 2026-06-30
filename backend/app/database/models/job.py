from sqlalchemy import String, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database.models.base import Base, TimestampMixin, SoftDeleteMixin

class JobDescription(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "job_description"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_required: Mapped[float | None] = mapped_column(Float, nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_type: Mapped[str | None] = mapped_column(String(255), nullable=True) # Remote, Hybrid, Onsite

    # Structured parsing results
    intent_profile: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    intent_graph: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    trace: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    confidence_scores: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
