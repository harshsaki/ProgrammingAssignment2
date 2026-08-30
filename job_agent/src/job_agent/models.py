from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class JobPosting:
    """A normalized job posting, regardless of which source it came from."""

    source: str                  # "greenhouse" | "lever" | "indeed" | "linkedin"
    external_id: str             # source-specific unique id (used for dedup)
    title: str
    company: str
    location: str
    description: str
    apply_url: str
    posted_at: str | None = None
    salary_text: str | None = None
    remote: bool = False

    @property
    def dedup_key(self) -> str:
        return f"{self.source}:{self.external_id}"


@dataclass
class MatchResult:
    job: JobPosting
    score: float
    matched_keywords: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


@dataclass
class GeneratedApplication:
    job: JobPosting
    match: MatchResult
    resume_pdf_path: str
    cover_letter_pdf_path: str
    tailored_summary: str


@dataclass
class ApplicationRecord:
    job: JobPosting
    status: str                  # "staged" | "submitted" | "dry_run" | "skipped" | "failed"
    detail: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
