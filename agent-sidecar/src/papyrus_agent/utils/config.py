from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Settings for agentic flow and LLM providers."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PAPYRUS_",
        extra="ignore",
    )

    vision_provider: str = "ollama"
    vision_model: str = "qwen2.5vl"
    vision_base_url: str = "http://localhost:11434"
    vision_api_key: SecretStr | None = None

    document_provider: str = "ollama"
    document_model: str = "qwen2.5vl"
    document_base_url: str = "http://localhost:11434"
    document_api_key: SecretStr | None = None

settings = Settings()

