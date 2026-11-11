from pathlib import Path
from pydantic import BaseModel, Field

class VisionRequest(BaseModel):
    prompt: str = "Describe this image."
    image_paths: list[Path] = Field(min_length=1)

class DocumentRequest(BaseModel):
    prompt: str = Field(min_length=1)

class LLMResponse(BaseModel):
    response: str



