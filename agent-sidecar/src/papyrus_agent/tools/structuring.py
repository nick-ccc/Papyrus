
from pathlib import Path

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from papyrus_agent.utils.llm import get_document_llm
from papyrus_agent.utils.templates import template_registry

LATEX_SYSTEM_PROMPT : str = """
You are an expert document structuring and LaTeX generation engine.
Your task is to transform OCR-transcribed content into a complete
LaTeX document using the supplied LaTeX template.

Requirements:
- Follow the supplied template's structure, formatting, and conventions.
- Populate the template using information from the source document.
- Preserve original meaning, technical terminology, and equations.
- Preserve tables, references, headings, and lists where applicable.
- Do not invent information or fabricate missing content.
- Escape LaTeX special characters where appropriate.
- Preserve existing LaTeX commands and template definitions.
- Do not compile or execute LaTeX.
- Return only the complete LaTeX source.
- Do not include Markdown code fences or explanations.
"""

class LaTeXDocument(BaseModel):
    latex_source: str
    warnings: list[str] = Field(default_factory=list)


@tool
def generate_latex_from_template(
    extracted_text: str,
    template_id: str,
) -> LaTeXDocument:
    """
    Generate a complete LaTeX document by organizing OCR-transcribed
    text according to a selected LaTeX template.

    Returns LaTeX source only. Does not compile or execute it.
    """

    if not extracted_text.strip():
        raise ValueError("Extracted document text cannot be empty.")

    template = template_registry.get(template_id)
 
    if template is None:
        raise ValueError(f"Unknown template: {template_id}")

    template_source = Path(template.template_path).read_text(
        encoding="utf-8"
    )

    llm = get_document_llm()

    response = llm.invoke([
        SystemMessage(),
        HumanMessage(content=f"""
LATEX TEMPLATE:
{template_source}

SOURCE DOCUMENT TEXT:
{extracted_text}

Generate the completed LaTeX document.
"""),
    ])

    latex_source = response.content

    if not isinstance(latex_source, str):
        raise RuntimeError(
            "Document LLM returned unexpected content."
        )

    return LaTeXDocument(
        latex_source=latex_source.strip(),
    )

@tool
def generate_latex(
    extracted_text: str,
) -> LaTeXDocument:
    """
    Generate a complete LaTeX document from OCR-transcribed text
    without using a predefined template.

    Returns LaTeX source only. Does not compile or execute it.
    """

    if not extracted_text.strip():
        raise ValueError("Extracted document text cannot be empty.")

    llm = get_document_llm()

    response = llm.invoke([
        SystemMessage(content=LATEX_SYSTEM_PROMPT),
        HumanMessage(content=f"""
SOURCE DOCUMENT TEXT:
{extracted_text}

Generate a complete LaTeX document using an appropriate
document structure and formatting.
"""),
    ])

    latex_source = response.content

    if not isinstance(latex_source, str):
        raise RuntimeError(
            "Document LLM returned unexpected content."
        )

    return LaTeXDocument(
        latex_source=latex_source.strip(),
    )

