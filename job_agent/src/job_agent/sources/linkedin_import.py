"""LinkedIn job source adapter.

LinkedIn has no public job-search API and its Terms of Service explicitly
prohibit automated scraping and automated ("Easy Apply") submissions from
anything but their own client. Attempting either risks getting your account
restricted or banned. So this adapter deliberately does the same thing as
indeed_import.py: it reads a JSON file you populate manually (copy/paste
job postings you found by browsing LinkedIn yourself), rather than
automating any interaction with linkedin.com.

Populate data/linkedin_jobs.json as a list of objects:

[
  {
    "id": "linkedin-job-id-or-url",
    "title": "Head of AI",
    "company": "Example Corp",
    "location": "Bengaluru, Karnataka, India",
    "description": "full job description text...",
    "url": "https://www.linkedin.com/jobs/view/...."
  },
  ...
]

LinkedIn postings are ALWAYS stage_only -- the orchestrator will refuse to
route them to an auto-submit apply engine regardless of config.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..models import JobPosting
from .base import JobSource


class LinkedInImportSource(JobSource):
    name = "linkedin"

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
                    remote="remote" in (job.get("location", "") or "").lower(),
                )
            )
        return postings
