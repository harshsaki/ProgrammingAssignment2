"""Playwright-driven apply engine for Greenhouse job postings.

Greenhouse's default embedded application form uses fairly consistent
field names across companies (first_name, last_name, email, phone, a
resume file input, and often a free-text cover-letter field). Custom
questions beyond that vary per company and are NOT auto-answered here --
if the form has required custom questions this engine can't fill, it backs
off to staging instead of submitting a partial/broken application.

dry_run=True (the config default) fills the form and stops immediately
before the submit click, logging exactly what it would have done.
"""

from __future__ import annotations

from ..models import ApplicationRecord, GeneratedApplication
from .base import ApplyEngine
from .browser_common import FieldFillResult, launch_page, try_fill, try_upload

_FIRST_NAME_SELECTORS = ["#first_name", "input[name='job_application[first_name]']"]
_LAST_NAME_SELECTORS = ["#last_name", "input[name='job_application[last_name]']"]
_EMAIL_SELECTORS = ["#email", "input[name='job_application[email]']"]
_PHONE_SELECTORS = ["#phone", "input[name='job_application[phone]']"]
_RESUME_SELECTORS = ["#resume", "input[type='file'][name*='resume']"]
_COVER_LETTER_FILE_SELECTORS = ["#cover_letter", "input[type='file'][name*='cover_letter']"]
_SUBMIT_SELECTORS = ["#submit_app", "button[type='submit']"]


class GreenhouseApplyEngine(ApplyEngine):
    def __init__(self, applicant: dict, headless: bool = True):
        """applicant: {"first_name", "last_name", "email", "phone"}"""
        self.applicant = applicant
        self.headless = headless

    def submit(self, application: GeneratedApplication, dry_run: bool) -> ApplicationRecord:
        job = application.job
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return ApplicationRecord(
                job=job, status="failed",
                detail="playwright not installed; run `pip install playwright && playwright install chromium`",
            )

        result = FieldFillResult()
        try:
            with sync_playwright() as p:
                browser, page = launch_page(p, headless=self.headless)
                try:
                    page.goto(job.apply_url, timeout=30000, wait_until="domcontentloaded")
                    try_fill(page, _FIRST_NAME_SELECTORS, self.applicant["first_name"], result, "first_name")
                    try_fill(page, _LAST_NAME_SELECTORS, self.applicant["last_name"], result, "last_name")
                    try_fill(page, _EMAIL_SELECTORS, self.applicant["email"], result, "email")
                    try_fill(page, _PHONE_SELECTORS, self.applicant.get("phone", ""), result, "phone")
                    try_upload(page, _RESUME_SELECTORS, application.resume_pdf_path, result, "resume")
                    try_upload(
                        page, _COVER_LETTER_FILE_SELECTORS, application.cover_letter_pdf_path,
                        result, "cover_letter",
                    )

                    required_ok = {"first_name", "last_name", "email", "resume"} <= set(result.filled)

                    if dry_run:
                        return ApplicationRecord(
                            job=job, status="dry_run",
                            detail=f"DRY RUN -- would submit. filled={result.filled} failed={result.failed}",
                        )
                    if not required_ok:
                        return ApplicationRecord(
                            job=job, status="skipped",
                            detail=(
                                "Required fields could not be auto-filled "
                                f"(filled={result.filled}, failed={result.failed}); staging instead"
                            ),
                        )
                    for sel in _SUBMIT_SELECTORS:
                        locator = page.locator(sel).first
                        if locator.count() > 0:
                            locator.click(timeout=5000)
                            page.wait_for_timeout(2000)
                            return ApplicationRecord(
                                job=job, status="submitted",
                                detail=f"Submitted via Greenhouse. filled={result.filled}",
                            )
                    return ApplicationRecord(
                        job=job, status="skipped",
                        detail="Could not locate a submit button; staging instead",
                    )
                finally:
                    browser.close()
        except Exception as exc:
            return ApplicationRecord(job=job, status="failed", detail=f"Error during apply: {exc}")
