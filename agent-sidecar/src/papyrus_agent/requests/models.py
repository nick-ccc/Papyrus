"""Define models for requests between sidecar and main rust process"""
import uuid
from datetime import datetime, timezone
from typing import Any, Literal
from enum import StrEnum

from pydantic import BaseModel, Field

class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Request(BaseModel):
    """Request being sent by the sidecar to Rust which has sole authority on DB transactions"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    protocol_version: Literal[1] = 1

class Response(BaseModel):
    """Response back on success"""
    id: uuid.UUID
    status: Literal["success", "error"]
    data: dict[str, Any] | None = None
    error: str | None = None
