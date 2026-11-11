import base64
import mimetypes
from typing import Any

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from papyrus_agent.schemas.llm import (
    LLMResponse,
    VisionRequest,
    DocumentRequest,
)
from papyrus_agent.utils.llm import (
    get_document_llm,
    get_vision_llm,
)

router = APIRouter(prefix="/llm", tags=["LLM"])


def extract_response(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "\n".join(
            str(item.get("text", ""))
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )

    raise RuntimeError("Unexpected LLM response format.")


@router.post("/vision", response_model=LLMResponse)
async def test_vision(request: VisionRequest) -> LLMResponse:
    try:
        image_blocks: list[str | dict[str, Any]] = []

        for image_path in request.image_paths:
            if not image_path.is_file():
                raise HTTPException(
                    status_code=404,
                    detail=f"Image not found: {image_path}",
                )

            mime_type, _ = mimetypes.guess_type(image_path.name)
            encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")

            image_blocks.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type or 'image/jpeg'};base64,{encoded}"
                },
            })

        message = HumanMessage(
            content=[
                {"type": "text", "text": request.prompt},
                *image_blocks,
            ]
        )

        llm = get_vision_llm()
        result = await llm.ainvoke([message])

        return LLMResponse(response=extract_response(result.content))

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/text", response_model=LLMResponse)
async def test_text(request: DocumentRequest) -> LLMResponse:
    try:
        llm = get_document_llm()
        result = await llm.ainvoke(request.prompt)

        return LLMResponse(response=extract_response(result.content))

    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


