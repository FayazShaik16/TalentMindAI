from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")

class ResponseMetadata(BaseModel):
    """
    Metadata attached to every standard API response.
    """
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    request_id: str | None = None

class EnvelopeResponse(BaseModel, Generic[DataT]):
    """
    Top-level envelope representing a successful operation response.
    """
    success: bool = Field(default=True)
    data: DataT
    meta: ResponseMetadata = Field(default_factory=ResponseMetadata)

class PaginatedMetadata(ResponseMetadata):
    """
    Top-level metadata containing offset and counts for list results.
    """
    total: int
    skip: int
    limit: int

class PaginatedResponse(BaseModel, Generic[DataT]):
    """
    Top-level envelope wrapping list results.
    """
    success: bool = Field(default=True)
    data: list[DataT]
    meta: PaginatedMetadata

class ErrorDetail(BaseModel):
    """
    Details of the error occurred.
    """
    code: str
    message: str
    details: Any = None

class ErrorResponse(BaseModel):
    """
    Top-level envelope representing a failed operation response.
    """
    success: bool = Field(default=False)
    error: ErrorDetail
    meta: ResponseMetadata = Field(default_factory=ResponseMetadata)
