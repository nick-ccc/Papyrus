import base64
from pathlib import Path
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
async def test_vision(request: VisionRequest):
    try:
        image_content = []

        for image_path in request.image_paths:
            if not image_path.is_file():
                raise HTTPException(
                    status_code=404,
                    detail=f"Image not found: {image_path}",
                )

            image_content.append({
                "type": "image",
                "base64": image_path.read_bytes(),
                "mime_type": "image/jpeg",
            })

        message = HumanMessage(
            content=[
                {"type": "text", "text": request.prompt},
                *[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:image/jpeg;base64,"
                                f"{base64.b64encode(item["base64"]).decode("utf-8")}"
                            )
                        },
                    }
                    for item in image_content
                ],
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
async def test_text(request: DocumentRequest):
    try:
        llm = get_document_llm()
        result = await llm.ainvoke(request.prompt)

        return LLMResponse(response=extract_response(result.content))

    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


