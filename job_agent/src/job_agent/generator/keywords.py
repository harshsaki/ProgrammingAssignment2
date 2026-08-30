"""Extracts likely ATS keywords from a job description.

ATS (applicant tracking system) keyword matching is one of the highest-
leverage things you control for getting a callback: many systems auto-rank
or auto-reject resumes before a human ever reads them, based on literal
term overlap with the JD. This module finds the terms worth mirroring.
"""

from __future__ import annotations

import re
from collections import Counter

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/-]{1,}")

_STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "our", "are", "will", "have",
    "this", "that", "from", "into", "role", "team", "work", "years", "year",
    "experience", "including", "such", "using", "must", "able", "ability",
    "strong", "excellent", "please", "job", "we", "as", "is", "in", "to",
    "of", "a", "an", "on", "at", "or", "be", "by", "it", "who", "their",
    "them", "they", "can", "all", "new", "more", "other", "any", "than",
    "etc", "including", "across", "about", "within", "per",
}


def extract_keywords(description: str, known_vocab: list[str] | None = None, top_n: int = 20) -> list[str]:
    """Returns up to top_n keywords from the JD, preferring known-vocab
    terms (skills the candidate actually has, so we don't chase buzzwords
    outside their real experience) then falling back to frequent technical-
    looking tokens.
    """
    text_l = description.lower()
    known_vocab = known_vocab or []

    vocab_hits = [term for term in known_vocab if term.lower() in text_l]

    tokens = [w.lower() for w in _WORD_RE.findall(description)]
    freq = Counter(t for t in tokens if t not in _STOPWORDS and len(t) > 2)
    frequent_terms = [term for term, _ in freq.most_common(top_n * 2)]

    ordered: list[str] = []
    seen: set[str] = set()
    for term in vocab_hits + frequent_terms:
        key = term.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(term)
        if len(ordered) >= top_n:
            break
    return ordered
