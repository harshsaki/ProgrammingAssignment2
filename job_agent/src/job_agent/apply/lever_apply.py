"""Playwright-driven apply engine for Lever job postings.

Same approach and same safety posture as greenhouse_apply.py: best-effort
fill of Lever's standard applicant fields, dry_run stops before the submit
click, and any required field it can't fill causes a fall-back to staging
rather than submitting an incomplete application.
"""

from __future__ import annotations

from ..models import ApplicationRecord, GeneratedApplication
from .base import ApplyEngine
from .browser_common import FieldFillResult, launch_page, try_fill, try_upload

_NAME_SELECTORS = ["input[name='name']"]
_EMAIL_SELECTORS = ["input[name='email']"]
_PHONE_SELECTORS = ["input[name='phone']"]
_RESUME_SELECTORS = ["input[name='resume']", "input[type='file']"]
_SUBMIT_SELECTORS = ["button[type='submit']"]


class LeverApplyEngine(ApplyEngine):
    def __init__(self, applicant: dict, headless: bool = True):
        """applicant: {"full_name", "email", "phone"}"""
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
                    try_fill(page, _NAME_SELECTORS, self.applicant["full_name"], result, "full_name")
                    try_fill(page, _EMAIL_SELECTORS, self.applicant["email"], result, "email")
                    try_fill(page, _PHONE_SELECTORS, self.applicant.get("phone", ""), result, "phone")
                    try_upload(page, _RESUME_SELECTORS, application.resume_pdf_path, result, "resume")

                    required_ok = {"full_name", "email", "resume"} <= set(result.filled)

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
                                detail=f"Submitted via Lever. filled={result.filled}",
                            )
                    return ApplicationRecord(
                        job=job, status="skipped",
                        detail="Could not locate a submit button; staging instead",
                    )
                finally:
                    browser.close()
        except Exception as exc:
            return ApplicationRecord(job=job, status="failed", detail=f"Error during apply: {exc}")
