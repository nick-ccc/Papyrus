import asyncio
import logging
from collections.abc import Callable

from fastapi import APIRouter, HTTPException
from langchain_core.language_models import BaseChatModel

from papyrus_agent.schemas.health import (
    HealthStatus,
    LLMHealthResponse,
    SystemHealthResponse,
)
from papyrus_agent.utils.llm import (
    get_document_llm,
    get_vision_llm,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


async def check_llm(
    name: str,
    factory: Callable[[], BaseChatModel],
) -> LLMHealthResponse:
    try:
        llm = factory()

        response = await asyncio.wait_for(
            llm.ainvoke("Reply with exactly: OK"),
            timeout=15,
        )

        if not response.content:
            raise RuntimeError("LLM returned an empty response.")

        return LLMHealthResponse(
            name=name,
            status=HealthStatus.HEALTHY,
        )

    except Exception as exc:
        logger.exception("%s LLM health check failed", name)

        return LLMHealthResponse(
            name=name,
            status=HealthStatus.UNHEALTHY,
            error=str(exc),
        )

@router.get("/vision", response_model=LLMHealthResponse)
async def vision_health():
    result = await check_llm("vision", get_vision_llm)

    if result.status == HealthStatus.UNHEALTHY:
        raise HTTPException(
            status_code=503,
            detail=result.model_dump(mode="json"),
        )

    return result


@router.get("/document", response_model=LLMHealthResponse)
async def document_health():
    result = await check_llm("document", get_document_llm)

    if result.status == HealthStatus.UNHEALTHY:
        raise HTTPException(
            status_code=503,
            detail=result.model_dump(mode="json"),
        )

    return result


@router.get("/llm", response_model=SystemHealthResponse)
async def llm_health():
    vision, document = await asyncio.gather(
        check_llm("vision", get_vision_llm),
        check_llm("document", get_document_llm),
    )

    health_status = (
        HealthStatus.HEALTHY
        if (
            vision.status == HealthStatus.HEALTHY
            and document.status == HealthStatus.HEALTHY
        )
        else HealthStatus.DEGRADED
    )

    result = SystemHealthResponse(
        status=health_status,
        vision=vision,
        document=document,
    )

    if health_status == HealthStatus.DEGRADED:
        raise HTTPException(
            status_code=503,
            detail=result.model_dump(mode="json"),
        )

    return result

