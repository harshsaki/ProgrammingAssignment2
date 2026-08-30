"""Optional Claude-powered polish pass.

Everything upstream (resume_builder, cover_letter_builder) already produces
a complete, factual, tailored draft with no network calls. This module is a
pure quality upgrade: if ANTHROPIC_API_KEY is set and
generation.use_llm_enhancement is true in config, it asks Claude to tighten
phrasing and make the cover letter read naturally -- without inventing new
facts, metrics, or claims. If the API isn't available, callers get the
untouched draft back, so the pipeline never hard-depends on this.
"""

from __future__ import annotations

import os

_SYSTEM_PROMPT = (
    "You polish job-application text for phrasing, flow, and tone. "
    "You MUST NOT invent, exaggerate, or add any fact, number, skill, or "
    "claim that is not already present in the input. Only improve wording, "
    "concision, and natural phrasing. Return only the rewritten text, no "
    "commentary."
)


def _client(model: str):
    try:
        import anthropic
    except ImportError:
        return None, None
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, None
    return anthropic.Anthropic(api_key=api_key), model


def polish_text(text: str, instruction: str, model: str = "claude-sonnet-5") -> str:
    client, model = _client(model)
    if client is None:
        return text
    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"{instruction}\n\n---\n{text}"}],
        )
        polished = "".join(block.text for block in response.content if block.type == "text").strip()
        return polished or text
    except Exception:
        # Never let an LLM/network hiccup break the pipeline -- fall back to
        # the deterministic draft, which is already a valid application.
        return text


def polish_cover_letter(cover_letter_text: str, model: str = "claude-sonnet-5") -> str:
    return polish_text(
        cover_letter_text,
        "Rewrite this cover letter so it reads naturally and persuasively, "
        "keeping every fact, number, and claim exactly as given. Keep the "
        "paragraph structure and length similar.",
        model=model,
    )


def polish_summary(summary_text: str, model: str = "claude-sonnet-5") -> str:
    return polish_text(
        summary_text,
        "Rewrite this resume professional-summary paragraph to flow "
        "naturally as one tight paragraph, keeping every fact and number "
        "exactly as given.",
        model=model,
    )
