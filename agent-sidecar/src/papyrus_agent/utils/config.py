from pathlib import Path

from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Settings for agentic flow and LLM providers.

    Values are read from PAPYRUS_* environment variables (see .envrc).
    Models have no default so a missing variable fails at startup instead
    of silently using the wrong model.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PAPYRUS_",
        extra="ignore",
    )

    vision_provider: str = "ollama"
    vision_model: str
    vision_base_url: str = "http://localhost:11434"
    vision_api_key: SecretStr | None = None

    document_provider: str = "ollama"
    document_model: str
    document_base_url: str = "http://localhost:11434"
    document_api_key: SecretStr | None = None

    templates_dir: Path = Path("~/papyrus/templates")

def _load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        prefix = Settings.model_config.get("env_prefix", "")
        lines = [
            f"  - {prefix}{'.'.join(str(p) for p in err['loc']).upper()}: {err['msg']}"
            for err in exc.errors()
        ]
        raise SystemExit(
            "\n"
            "Papyrus agent configuration error\n"
            "=================================\n"
            "The sidecar could not start because required settings are missing "
            "or invalid:\n\n"
            + "\n".join(lines)
            + "\n\n"
            "These are read from PAPYRUS_* environment variables (see "
            "agent-sidecar/.envrc) or from agent-sidecar/.env.\n"
            "If you use direnv, run `direnv allow` in agent-sidecar/ and start "
            "the sidecar from that shell.\n"
            "Otherwise run `set -a; source .envrc; set +a` first, or have the "
            "parent process (e.g. Tauri) pass these variables to the sidecar.\n"
        ) from None


settings = _load_settings()
