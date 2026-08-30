"""Builds a tailored resume (as a plain dict, source-agnostic of PDF vs
other rendering) for a specific job posting.

Strategy for maximizing interview callbacks without fabricating anything:
  1. Never invent experience, titles, dates, or metrics -- only reorder and
     select from what's already in profile.json.
  2. Put the most JD-relevant skill categories and bullets first (recruiters
     and ATS parsers weight earlier content more).
  3. Tailor the summary's opening line to name the target role/company and
     surface the JD keywords the candidate genuinely has.
"""

from __future__ import annotations

import re

from ..models import JobPosting
from .keywords import extract_keywords

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/-]{1,}")


def _overlap_score(bullet: str, jd_tokens: set[str]) -> int:
    bullet_tokens = {w.lower() for w in _WORD_RE.findall(bullet)}
    return len(bullet_tokens & jd_tokens)


def build_tailored_resume(profile: dict, job: JobPosting, max_bullets_per_role: int = 5) -> dict:
    jd_tokens = {w.lower() for w in _WORD_RE.findall(job.title + " " + job.description)}
    all_skill_terms = [s for group in profile["skills"].values() for s in group]
    matched_keywords = extract_keywords(job.description, known_vocab=all_skill_terms, top_n=12)

    # Reorder skill categories: those with more JD-matched terms come first.
    def category_relevance(items: list[str]) -> int:
        return sum(1 for item in items if item.lower() in {k.lower() for k in matched_keywords})

    skills_ordered = dict(
        sorted(profile["skills"].items(), key=lambda kv: category_relevance(kv[1]), reverse=True)
    )
    # Within each category, matched terms first.
    matched_lower = {k.lower() for k in matched_keywords}
    for category, items in skills_ordered.items():
        skills_ordered[category] = sorted(
            items, key=lambda it: it.lower() not in matched_lower
        )

    # Select/reorder bullets per role by JD overlap, keep roles in original
    # (reverse-chronological) order -- never reorder work history itself.
    experience = []
    for role in profile["experience"]:
        ranked_bullets = sorted(role["bullets"], key=lambda b: _overlap_score(b, jd_tokens), reverse=True)
        top_bullets = ranked_bullets[:max_bullets_per_role]
        # Restore original relative order among the selected bullets so the
        # narrative still reads naturally (chronological within the role).
        top_bullets_ordered = [b for b in role["bullets"] if b in top_bullets]
        experience.append({**role, "bullets": top_bullets_ordered})

    top_matched = matched_keywords[:5]
    tailor_clause = f" Targeting the {job.title} role at {job.company}" if job.title else ""
    if top_matched:
        tailor_clause += f", bringing direct hands-on depth in {', '.join(top_matched)}."
    else:
        tailor_clause += "."

    tailored_summary = profile["summary"] + tailor_clause

    return {
        "name": profile["name"],
        "headline": profile["headline"],
        "location": profile["location"],
        "phone": profile["phone"],
        "email": profile["email"],
        "linkedin": profile["linkedin"],
        "summary": tailored_summary,
        "skills": skills_ordered,
        "experience": experience,
        "projects": profile.get("projects", []),
        "certifications": profile.get("certifications", []),
        "honors": profile.get("honors", []),
        "education": profile.get("education", []),
        "languages": profile.get("languages", []),
        "matched_keywords": matched_keywords,
    }
