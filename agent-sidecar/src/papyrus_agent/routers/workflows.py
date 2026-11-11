import uuid
import logging
from typing import Any, Self, cast
from pathlib import Path

from pydantic import (
    BaseModel, 
    Field, 
    model_validator,
)
from fastapi import (
    APIRouter, 
    HTTPException,
    BackgroundTasks,
    status,
)

from papyrus_agent.requests import DocumentStatus
from papyrus_agent.utils.templates import template_registry
from papyrus_agent.workflows.document_workflow import (
    DocumentState,
    document_graph,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["Workflows"])

class DocumentRequest(BaseModel):
    """Request for document processing."""
    image_paths: list[Path] = Field(default_factory=list)
    extracted_text: str | None = None
    template: str | None = None

    @model_validator(mode="after")
    def validate_input(self) -> Self:
        has_text = bool(self.extracted_text and self.extracted_text.strip())

        if not self.image_paths and not has_text:
            raise ValueError(
                "Provide image_paths or extracted_text."
            )

        if self.image_paths and has_text:
            raise ValueError(
                "Provide either image_paths or extracted_text, not both. "
                "Clear extracted_text (null or \"\") to process the images."
            )
        return self


class DocumentResponse(BaseModel):
    """Document processing status and generated output."""

    id: uuid.UUID
    status: DocumentStatus
    latex_source: str | None = None
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


# Temporary in-memory task storage.
documents: dict[str, dict[str, Any]] = {}


async def process_document(
    document_id: str,
    request: DocumentRequest,
) -> None:
    """Execute the document processing workflow."""

    documents[document_id]["status"] = DocumentStatus.PROCESSING

    try:
        # LangGraph returns the final state as a dict at runtime.
        result = cast(dict[str, Any], await document_graph.ainvoke(
            DocumentState(
                image_paths=[str(path) for path in request.image_paths],
                extracted_text=request.extracted_text or "",
                template_id=request.template,
            )
        ))

        if not result.get("latex_source"):
            raise RuntimeError("Workflow finished without LaTeX output.")

        documents[document_id].update({
            "status": DocumentStatus.COMPLETED,
            "latex_source": result["latex_source"],
            "warnings": result.get("warnings", []),
        })

    except Exception as exc:
        logger.exception(
            "Document processing failed: %s",
            document_id,
        )

        documents[document_id].update({
            "status": DocumentStatus.FAILED,
            "error": str(exc),
        })


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_documents(
    request: DocumentRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Start document processing and return an internal ID."""

    if request.template and template_registry.get(request.template) is None:
        available = ", ".join(template_registry.ids()) or "none"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Unknown template: {request.template!r}. "
                f"Available templates: {available}"
            ),
        )

    missing = [str(path) for path in request.image_paths if not path.is_file()]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found: {', '.join(missing)}",
        )

    document_id = str(uuid.uuid4())

    documents[document_id] = {
        "id": document_id,
        "status": DocumentStatus.PENDING,
        "latex_source": None,
        "warnings": [],
        "error": None,
    }

    background_tasks.add_task(
        process_document,
        document_id,
        request,
    )

    return documents[document_id]

@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
)
async def get_document_status(document_id: uuid.UUID) -> dict[str, Any]:
    """Retrieve document processing status and generated LaTeX."""

    document = documents.get(str(document_id))

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document

