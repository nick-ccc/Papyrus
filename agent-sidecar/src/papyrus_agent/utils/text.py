"""Helpers for normalizing raw LLM output."""
import re
from typing import Any

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_UNCLOSED_THINK = re.compile(r"^.*?</think>", re.DOTALL | re.IGNORECASE)
_CODE_FENCE = re.compile(
    r"^\s*```[a-zA-Z0-9_-]*\s*\n(?P<body>.*?)\n?```\s*$",
    re.DOTALL,
)


def message_text(content: Any) -> str:
    """Flatten LLM message content (string or list of blocks) into text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)

    raise RuntimeError("Unexpected LLM response format.")


def strip_reasoning(text: str) -> str:
    """Remove <think>...</think> blocks emitted by reasoning models."""
    text = _THINK_BLOCK.sub("", text)
    # Some servers strip the opening tag but leave the closing one.
    text = _UNCLOSED_THINK.sub("", text)
    return text.strip()


def strip_code_fences(text: str) -> str:
    """Unwrap a single surrounding Markdown code fence, if present."""
    match = _CODE_FENCE.match(text)
    return match.group("body").strip() if match else text.strip()


def clean_llm_text(content: Any) -> str:
    """Message content -> plain text without reasoning or code fences."""
    return strip_code_fences(strip_reasoning(message_text(content)))


def extract_json_object(text: str) -> str:
    """Return the outermost {...} span from text, or raise ValueError."""
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end <= start:
        raise ValueError("No JSON object found in LLM response.")

    return text[start : end + 1]
