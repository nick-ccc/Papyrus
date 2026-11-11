import uuid
import logging
from typing import Any
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
from papyrus_agent.workflows.document_workflow import document_graph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["Workflows"])

class DocumentRequest(BaseModel):
    """Request for document processing."""
    image_paths: list[Path] = Field(default_factory=list)
    extracted_text: str | None = None
    template: str | None = None

    @model_validator(mode="after")
    def validate_input(self):
        if not self.image_paths and not (
            self.extracted_text and self.extracted_text.strip()
        ):
            raise ValueError(
                "Provide image_paths or extracted_text."
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
        result = await document_graph.ainvoke({
            "image_paths": [
                str(path) for path in request.image_paths
            ],
            "extracted_text": request.extracted_text or "",
            "template_id": request.template,
        })

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
):
    """Start document processing and return an internal ID."""

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
async def get_document_status(document_id: uuid.UUID):
    """Retrieve document processing status and generated LaTeX."""

    document = documents.get(str(document_id))

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document

