from __future__ import annotations

from typing import Any


def extract_text_parts(value: Any) -> list[str]:
    """
    Best-effort extraction of text deltas from various streaming payload shapes.

    This helper is provider-agnostic: different LLM providers (and even OpenAI endpoints)
    may represent "content" as:
    - a plain string
    - a list of strings
    - a list of typed dict parts, e.g. {"type": "...", "text": "..."}
    - a nested dict shape, e.g. {"text": {"value": "..."}}
    """

    out: list[str] = []
    if isinstance(value, str):
        if value:
            out.append(value)
        return out
    if isinstance(value, list):
        for part in value:
            if isinstance(part, str):
                if part:
                    out.append(part)
                continue
            if not isinstance(part, dict):
                continue
            # Common shapes:
            # - {"type": "text", "text": "..."}
            # - {"type": "output_text", "text": "..."}
            # - {"text": {"value": "..."}}  (nested)
            txt = part.get("text")
            if isinstance(txt, str) and txt:
                out.append(txt)
                continue
            if isinstance(txt, dict):
                v = txt.get("value")
                if isinstance(v, str) and v:
                    out.append(v)
                    continue
            alt = part.get("content")
            if isinstance(alt, str) and alt:
                out.append(alt)
                continue
        return out
    return out

