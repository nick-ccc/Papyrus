"""Tool calling for Optical Character Recognition (OCR) on one or more documents"""
import base64
# import numpy as np
# import tempfile
# import os
# import cv2
import mimetypes
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from pydantic import BaseModel, Field

from papyrus_agent.utils.llm import get_vision_llm
from papyrus_agent.utils.text import (
    extract_json_object,
    message_text,
    strip_code_fences,
    strip_reasoning,
)


class OCRPageResult(BaseModel):
    page_number: int
    extracted_text: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


class OCRResult(BaseModel):
    pages: list[OCRPageResult]
    full_text: str
    language: str | None = None
    contains_tables: bool = False
    contains_equations: bool = False
    warnings: list[str] = Field(default_factory=list)

OCR_SYSTEM_PROMPT = """
You are a document OCR engine.

Transcribe all visible content accurately.

- Preserve original wording, spelling, punctuation, and capitalization.
- Preserve reading order, paragraphs, headings, and lists.
- Preserve table structure and mathematical expressions.
- Do not summarize, paraphrase, translate, or correct content.
- Never invent missing or illegible text.
- Mark unreadable regions as [ILLEGIBLE].
- Preserve page boundaries and page order.
- Do not duplicate text across pages.
- Estimate transcription confidence between 0.0 and 1.0.

Respond with a single JSON object and nothing else (no Markdown fences,
no commentary), with exactly these fields:
{
  "extracted_text": "<full transcription of the page>",
  "confidence": <number between 0.0 and 1.0>,
  "warnings": ["<short notes such as tables, equations, illegible regions>"]
}
"""

OCR_MAX_ATTEMPTS = 2


class _OCRPageOutput(BaseModel):
    """Page fields the vision model is asked to produce."""

    extracted_text: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: list[str] = Field(default_factory=list)


def _parse_page_output(content: object) -> _OCRPageOutput:
    text = strip_reasoning(message_text(content))
    text = strip_code_fences(text)
    return _OCRPageOutput.model_validate_json(extract_json_object(text))

# TODO - currently unused
# @tool
# def preprocess_image(
#     img_path: str,
#     op: str = "threshold",
#     target_width: int = 1600
# ) -> str:
#     """Preprocess the image to help the OCR process 
#
#     reference: https://github.com/t-redactyl/ocr-llm-agent/blob/main/additions/additions_1_opencv.py
#     """
#     img = cv2.imread(img_path)
#     if img is None:
#         raise ValueError(f"Could not read image at {img_path}")
#
#     # Upscale small images to help OCR
#     if target_width is not None and img.shape[1] < target_width:
#         scale = target_width / img.shape[1]
#         img = cv2.resize(img, None, fx = scale, fy = scale, interpolation = cv2.INTER_CUBIC)
#
#     if op == "threshold":
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         # Gentle denoise and local binarisation to sharpen text
#         gray = cv2.bilateralFilter(gray, 7, 50, 50)
#         out = cv2.adaptiveThreshold(gray,
#                                     255,
#                                     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                                     cv2.THRESH_BINARY,
#                                     31,
#                                     10)
#
#     elif op == "deskew":
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         gray = cv2.bitwise_not(gray)
#         # Otsu to find text pixels
#         _, bw = cv2.threshold(gray,
#                               0,
#                               255,
#                               cv2.THRESH_BINARY | cv2.THRESH_OTSU)
#         coords = np.column_stack(np.where(bw > 0))
#         angle = 0.0
#         if coords.size > 0:
#             rect = cv2.minAreaRect(coords)
#             angle = rect[-1]
#             # Convert OpenCV's angle convention to a proper rotation
#             if angle < -45:
#                 angle = -(90 + angle)
#             else:
#                 angle = -angle
#         # Rotate around centre
#         (h, w) = img.shape[:2]
#         M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
#         out = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
#
#     # Ensure 3-channel PNG for the vision model (it accepts grayscale too, but PNG-3 is universal)
#     if out.ndim == 2:
#         out = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
#
#     # Write to a temporary PNG and return its path
#     tmpdir = tempfile.gettempdir()
#     base = os.path.splitext(os.path.basename(img_path))[0]
#     out_path = os.path.join(tmpdir, f"{base}_proc_{op}.png")
#     cv2.imwrite(out_path, out)
#     return out_path

@tool
def extract_text(img_paths: list[str]) -> OCRResult:
    """Extract and combine text from multiple ordered document page images."""

    if not img_paths:
        raise ValueError("At least one image path is required.")

    vision_llm = get_vision_llm()
    pages: list[OCRPageResult] = []
    document_warnings: list[str] = []

    for page_number, img_path in enumerate(img_paths, start=1):
        try:
            path = Path(img_path)

            if not path.is_file():
                raise FileNotFoundError(f"Image not found: {img_path}")

            mime_type, _ = mimetypes.guess_type(path.name)
            mime_type = mime_type or "image/png"

            image_base64 = base64.b64encode(
                path.read_bytes()
            ).decode("utf-8")

            messages = [
                SystemMessage(content=OCR_SYSTEM_PROMPT),
                HumanMessage(content=[
                    {
                        "type": "text",
                        "text": f"Transcribe document page {page_number}.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}"
                        },
                    },
                ]),
            ]

            output: _OCRPageOutput | None = None
            last_error: Exception | None = None

            for _ in range(OCR_MAX_ATTEMPTS):
                response = vision_llm.invoke(messages)
                try:
                    output = _parse_page_output(response.content)
                    break
                except ValueError as parse_error:
                    last_error = parse_error

            if output is None:
                raise ValueError(
                    f"Vision LLM returned unparseable output: {last_error}"
                )

            pages.append(OCRPageResult(
                page_number=page_number,
                extracted_text=output.extracted_text,
                confidence=output.confidence,
                warnings=output.warnings,
            ))

        except Exception as e:
            raise RuntimeError(
                f"OCR failed on page {page_number} ({img_path}): {e}"
            ) from e

    for page in pages:
        document_warnings.extend(
            f"Page {page.page_number}: {warning}" for warning in page.warnings
        )

    full_text = "\n\n".join(
        f"--- Page {page.page_number} ---\n{page.extracted_text}"
        for page in pages
    )

    return OCRResult(
        pages=pages,
        full_text=full_text,
        warnings=document_warnings,
        contains_tables=any(
            "table" in warning.lower()
            for page in pages
            for warning in page.warnings
        ),
        contains_equations=any(
            "equation" in warning.lower()
            for page in pages
            for warning in page.warnings
        ),
    )

