"""Indeed job source adapter.

Indeed does not offer a general-purpose public search API, and scraping
indeed.com directly is against its Terms of Service and is aggressively
detected. Instead, this adapter reads a JSON file you populate by running
the Indeed MCP connector tools from an interactive Claude Code session:

    mcp__Indeed__search_jobs(query="...", location="India")
    mcp__Indeed__get_job_details(job_id=...)

Save the results to data/indeed_jobs.json (path configurable) as a list of
objects shaped like:

[
  {
    "id": "abc123",
    "title": "AI Product Manager",
    "company": "Example Corp",
    "location": "Bengaluru, Karnataka",
    "description": "full job description text...",
    "url": "https://www.indeed.com/viewjob?jk=abc123",
    "posted_at": "2026-08-20",
    "salary_text": "25-40 LPA"
  },
  ...
]

Indeed postings are always routed to stage_only in the orchestrator
(generate + tailor, never auto-submitted) -- see config.yaml.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..models import JobPosting
from .base import JobSource


class IndeedImportSource(JobSource):
    name = "indeed"

    def __init__(self, import_file: str | Path):
        self.import_file = Path(import_file)

    def search(self) -> list[JobPosting]:
        if not self.import_file.exists():
            return []
        raw = json.loads(self.import_file.read_text() or "[]")
        postings = []
        for job in raw:
            postings.append(
                JobPosting(
                    source=self.name,
                    external_id=str(job.get("id") or job.get("url")),
                    title=job.get("title", ""),
                    company=job.get("company", ""),
                    location=job.get("location", ""),
                    description=job.get("description", ""),
                    apply_url=job.get("url", ""),
                    posted_at=job.get("posted_at"),
                    salary_text=job.get("salary_text"),
                    remote="remote" in (job.get("location", "") or "").lower(),
                )
            )
        return postings
