from pydantic import BaseModel, ConfigDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from papyrus_agent.tools.ocr import OCRResult, extract_text
from papyrus_agent.tools.structuring import (
    LaTeXDocument,
    generate_latex,
    generate_latex_from_template,
)


class DocumentState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    image_paths: list[str] = []
    extracted_text: str = ""
    template_id: str | None = None

    ocr_result: OCRResult | None = None

    latex_document: LaTeXDocument | None = None
    latex_source: str | None = None
    warnings: list[str] = []


def route_input(state: DocumentState) -> str:
    if state.extracted_text.strip():
        return "generate"

    if state.image_paths:
        return "ocr"

    raise ValueError("Document workflow requires image_paths or extracted_text.")


def ocr_node(state: DocumentState) -> dict[str, OCRResult | str]:
    result: OCRResult = extract_text.invoke({
        "img_paths": state.image_paths,
    })

    if not result.full_text.strip():
        raise ValueError("OCR returned empty document text.")

    return {
        "ocr_result": result,
        "extracted_text": result.full_text,
    }

def generate_latex_node(state: DocumentState) -> dict[str, LaTeXDocument | str | list[str]]: 
    if not state.extracted_text.strip():
        raise ValueError("No extracted document text provided.")

    if state.template_id:
        result: LaTeXDocument = generate_latex_from_template.invoke({
            "extracted_text": state.extracted_text,
            "template_id": state.template_id,
        })
    else:
        result: LaTeXDocument = generate_latex.invoke({
            "extracted_text": state.extracted_text,
        })

    return {
        "latex_document": result,
        "latex_source": result.latex_source,
        "warnings": result.warnings,
    }


def build_document_graph() -> CompiledStateGraph[
    DocumentState,
    None,
    DocumentState,
    DocumentState,
]:
    workflow = StateGraph(DocumentState)

    workflow.add_node("ocr", ocr_node)
    workflow.add_node("generate_latex", generate_latex_node)

    workflow.add_conditional_edges(
        START,
        route_input,
        {
            "ocr": "ocr",
            "generate": "generate_latex",
        },
    )

    workflow.add_edge("ocr", "generate_latex")
    workflow.add_edge("generate_latex", END)

    return workflow.compile()


document_graph = build_document_graph()
