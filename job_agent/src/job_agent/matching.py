"""Scores job postings against a candidate profile.

Deliberately simple and inspectable (no ML model, no external calls) so you
can see exactly why a job was or wasn't selected -- that transparency
matters more than a marginally smarter score when you're trusting this to
pick what gets your name on it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import JobPosting, MatchResult

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/-]{1,}")

_SENIORITY_TIERS = {
    "intern": 0, "junior": 1, "associate": 2, "mid": 3, "senior": 5,
    "staff": 7, "principal": 8, "lead": 6, "director": 9, "head": 9, "vp": 10,
    "vice president": 10, "chief": 11,
}


def _tokenize(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text or "")}


def _flatten_skills(skills: dict[str, list[str]]) -> list[str]:
    return [s for group in skills.values() for s in group]


def _seniority_tier(text: str) -> int | None:
    text_l = text.lower()
    best = None
    for word, tier in _SENIORITY_TIERS.items():
        if word in text_l:
            best = tier if best is None else max(best, tier)
    return best


@dataclass
class MatchConfig:
    target_titles: list[str]
    keywords_any: list[str]
    min_years_experience: int
    min_match_score: float
    country: str


def score_job(job: JobPosting, profile: dict, cfg: MatchConfig) -> MatchResult:
    reasons: list[str] = []
    jd_tokens = _tokenize(job.title + " " + job.description)

    # --- Title relevance (0-0.4) ---
    title_hits = [t for t in cfg.target_titles if t.lower() in job.title.lower()]
    title_score = min(len(title_hits), 2) / 2 * 0.4
    if title_hits:
        reasons.append(f"Title matches target role(s): {', '.join(title_hits)}")

    # --- Skill/keyword overlap (0-0.4) ---
    skill_vocab = {s.lower() for s in _flatten_skills(profile.get("skills", {}))}
    skill_vocab |= {k.lower() for k in cfg.keywords_any}
    matched_keywords = sorted(
        {kw for kw in skill_vocab if kw in job.description.lower() or kw in job.title.lower()}
    )
    keyword_score = min(len(matched_keywords), 10) / 10 * 0.4
    if matched_keywords:
        reasons.append(f"{len(matched_keywords)} matching skills/keywords found in JD")

    # --- Seniority fit (0-0.2) ---
    seniority_score = 0.0
    job_tier = _seniority_tier(job.title)
    if job_tier is not None:
        years = profile.get("years_experience", 0)
        candidate_tier_floor = 5 if years >= 8 else 3
        if job_tier >= candidate_tier_floor:
            seniority_score = 0.2
            reasons.append("Seniority level appears aligned with candidate experience")
        else:
            reasons.append("Role appears more junior than candidate's experience level")

    score = round(title_score + keyword_score + seniority_score, 3)

    # --- Location gate (hard filter reflected in reasons, not score) ---
    if cfg.country and cfg.country.lower() not in (job.location or "").lower():
        if not job.remote:
            reasons.append(f"Location '{job.location}' does not mention '{cfg.country}' -- verify manually")

    return MatchResult(job=job, score=score, matched_keywords=matched_keywords, reasons=reasons)


def rank_jobs(jobs: list[JobPosting], profile: dict, cfg: MatchConfig) -> list[MatchResult]:
    scored = [score_job(job, profile, cfg) for job in jobs]
    scored = [m for m in scored if m.score >= cfg.min_match_score]
    scored.sort(key=lambda m: m.score, reverse=True)
    return scored
