class LLMHealthResponse(BaseModel):
    name: str
    status: Literal["healthy", "unhealthy"]
    model: str | None = None
    error: str | None = None


class SystemHealthResponse(BaseModel):
    status: Literal["healthy", "degraded"]
    vision: LLMHealthResponse
    document: LLMHealthResponse


