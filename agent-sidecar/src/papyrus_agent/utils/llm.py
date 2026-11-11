from pydantic import SecretStr
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from .config import settings


def get_vision_llm() -> BaseChatModel:
    provider = settings.vision_provider.lower()

    if provider == "ollama":
        return ChatOllama(
            model=settings.vision_model,
            base_url=settings.vision_base_url,
        )

    if provider == "openai":
        return ChatOpenAI(
            model=settings.vision_model,
            base_url=settings.vision_base_url,
            api_key=settings.vision_api_key or SecretStr("not-needed"),
        )

    raise ValueError(f"Unsupported vision provider: {provider}")


def get_document_llm() -> BaseChatModel:
    provider = settings.document_provider.lower()

    if provider == "ollama":
        return ChatOllama(
            model=settings.document_model,
            base_url=settings.document_base_url,
        )

    if provider == "openai":
        return ChatOpenAI(
            model=settings.document_model,
            base_url=settings.document_base_url,
            api_key=settings.document_api_key or SecretStr("not-needed"),
        )

    raise ValueError(f"Unsupported document provider: {provider}")

