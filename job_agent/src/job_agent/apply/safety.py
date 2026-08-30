"""Guardrails that sit between the orchestrator and any apply engine.

These exist because unattended browser automation submitting real job
applications is a hard-to-reverse, externally-visible action. Getting the
routing wrong (e.g. auto-submitting to LinkedIn) risks the candidate's
account getting flagged or banned, or blasting a low-quality application
that actively hurts their chances. So the checks here are enforced in code,
not just documented in config comments.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import JobPosting
from ..storage import ApplicationsLog

# Sources that must NEVER be auto-submitted, no matter what config says.
# LinkedIn's ToS and anti-automation detection make this a bright line.
HARD_NO_AUTO_SUBMIT = {"linkedin"}


class ApplyGuard:
    def __init__(
        self,
        log: ApplicationsLog,
        auto_submit_sources: list[str],
        max_applications_per_day: int,
        dry_run: bool,
    ):
        self.log = log
        self.auto_submit_sources = set(auto_submit_sources) - HARD_NO_AUTO_SUBMIT
        self.max_applications_per_day = max_applications_per_day
        self.dry_run = dry_run

    def can_auto_submit(self, job: JobPosting) -> tuple[bool, str]:
        if job.source in HARD_NO_AUTO_SUBMIT:
            return False, f"{job.source} is never auto-submitted (ToS/anti-automation risk)"
        if job.source not in self.auto_submit_sources:
            return False, f"{job.source} is not in auto_submit_sources"
        today_prefix = datetime.now(timezone.utc).date().isoformat()
        count_today = self.log.daily_count(today_prefix)
        if count_today >= self.max_applications_per_day:
            return False, f"Daily application cap reached ({count_today}/{self.max_applications_per_day})"
        return True, "ok"
