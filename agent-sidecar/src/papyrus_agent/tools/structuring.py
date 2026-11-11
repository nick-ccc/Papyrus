from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from papyrus_agent.utils.llm import get_document_llm
from papyrus_agent.utils.templates import template_registry
from papyrus_agent.utils.text import clean_llm_text

LATEX_SYSTEM_PROMPT : str = """
You are an expert document structuring and LaTeX generation engine.
Your task is to transform OCR-transcribed content into a complete
LaTeX document, using the supplied LaTeX template when one is provided.

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


def _generate(extracted_text: str, template_source: str | None) -> LaTeXDocument:
    llm = get_document_llm()

    if template_source:
        user_prompt = f"""
LATEX TEMPLATE:
{template_source}

SOURCE DOCUMENT TEXT:
{extracted_text}

Generate the completed LaTeX document.
"""
    else:
        user_prompt = f"""
SOURCE DOCUMENT TEXT:
{extracted_text}

Generate a complete LaTeX document using an appropriate
document structure and formatting.
"""

    response = llm.invoke([
        SystemMessage(content=LATEX_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    latex_source = clean_llm_text(response.content)

    if not latex_source:
        raise RuntimeError("Document LLM returned an empty response.")

    warnings: list[str] = []

    if "\\documentclass" not in latex_source:
        warnings.append("Generated LaTeX is missing \\documentclass.")

    if "\\begin{document}" not in latex_source:
        warnings.append("Generated LaTeX is missing \\begin{document}.")

    return LaTeXDocument(latex_source=latex_source, warnings=warnings)


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
        available = ", ".join(template_registry.ids()) or "none"
        raise ValueError(
            f"Unknown template: {template_id!r}. Available: {available}"
        )

    template_source = template.read()
    template_warnings: list[str] = []

    if not template_source.strip():
        template_warnings.append(
            f"Template {template_id!r} is empty; generated without a template."
        )

    result = _generate(extracted_text, template_source.strip() or None)
    result.warnings = [*template_warnings, *result.warnings]

    return result

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

    return _generate(extracted_text, None)
