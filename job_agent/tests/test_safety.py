import tempfile
from pathlib import Path

from job_agent.apply.safety import ApplyGuard
from job_agent.models import JobPosting
from job_agent.storage import ApplicationsLog


def make_job(source: str) -> JobPosting:
    return JobPosting(
        source=source, external_id="1", title="Head of AI", company="Acme",
        location="India", description="", apply_url="https://example.com",
    )


def test_linkedin_is_never_auto_submittable_even_if_misconfigured():
    with tempfile.TemporaryDirectory() as tmp:
        log = ApplicationsLog(Path(tmp) / "log.csv")
        # Deliberately misconfigured to include linkedin -- guard must still block it.
        guard = ApplyGuard(log, auto_submit_sources=["linkedin", "greenhouse"], max_applications_per_day=10, dry_run=True)
        ok, reason = guard.can_auto_submit(make_job("linkedin"))
        assert ok is False
        assert "never" in reason.lower()


def test_source_not_in_allowlist_is_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        log = ApplicationsLog(Path(tmp) / "log.csv")
        guard = ApplyGuard(log, auto_submit_sources=["greenhouse"], max_applications_per_day=10, dry_run=True)
        ok, _ = guard.can_auto_submit(make_job("indeed"))
        assert ok is False


def test_allowed_source_within_cap_is_permitted():
    with tempfile.TemporaryDirectory() as tmp:
        log = ApplicationsLog(Path(tmp) / "log.csv")
        guard = ApplyGuard(log, auto_submit_sources=["greenhouse"], max_applications_per_day=10, dry_run=True)
        ok, _ = guard.can_auto_submit(make_job("greenhouse"))
        assert ok is True
