from pydantic import BaseModel
from enum import StrEnum


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"

class LLMHealthResponse(BaseModel):
    name: str
    status: HealthStatus
    model: str | None = None
    error: str | None = None


class SystemHealthResponse(BaseModel):
    status: HealthStatus
    vision: LLMHealthResponse
    document: LLMHealthResponse
