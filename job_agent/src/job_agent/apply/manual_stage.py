"""Stages a generated application for manual review/submission.

Used for every source that isn't eligible for auto-submit (Indeed,
LinkedIn, and any Greenhouse/Lever posting that fails the auto-submit
guard). Copies the tailored PDFs into outbox/<company>__<title>/ alongside
a note.txt with the apply URL and match reasons, so submitting by hand is a
five-minute task instead of starting from scratch.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from ..models import ApplicationRecord, GeneratedApplication
from .base import ApplyEngine


def _slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:60]


class ManualStageEngine(ApplyEngine):
    def __init__(self, outbox_dir: str | Path):
        self.outbox_dir = Path(outbox_dir)

    def submit(self, application: GeneratedApplication, dry_run: bool) -> ApplicationRecord:
        job = application.job
        folder = self.outbox_dir / f"{_slug(job.company)}__{_slug(job.title)}__{_slug(job.external_id)}"
        folder.mkdir(parents=True, exist_ok=True)

        shutil.copy(application.resume_pdf_path, folder / "resume.pdf")
        shutil.copy(application.cover_letter_pdf_path, folder / "cover_letter.pdf")

        note = (
            f"Company: {job.company}\n"
            f"Title: {job.title}\n"
            f"Apply URL: {job.apply_url}\n"
            f"Source: {job.source}\n"
            f"Match score: {application.match.score}\n"
            f"Match reasons:\n" + "\n".join(f"  - {r}" for r in application.match.reasons) + "\n\n"
            "This application was NOT auto-submitted. Review the resume and "
            "cover letter above, then apply manually at the URL above.\n"
        )
        (folder / "note.txt").write_text(note)

        return ApplicationRecord(job=job, status="staged", detail=f"Staged at {folder}")
