import uuid
from datetime import datetime, timezone
from typing import Annotated
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Define a reusable UUID primary key type annotation
pk_uuid = Annotated[
    uuid.UUID,
    mapped_column(primary_key=True, default=uuid.uuid4, index=True)
]

class Base(DeclarativeBase):
    """
    Base declarative model class for all SQLAlchemy entities.
    """
    pass

class TimestampMixin:
    """
    Adds created_at and updated_at timestamp columns to database entities.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

class SoftDeleteMixin:
    """
    Enables soft delete logic on database tables.
    """
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, nullable=True)

class AuditMixin:
    """
    Enables creator and modifier user tracking on database tables.
    """
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
