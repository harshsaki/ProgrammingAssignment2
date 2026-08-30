"""Shared Playwright helpers for the Greenhouse/Lever apply engines.

Both platforms host thousands of differently-themed but structurally
similar forms (companies customize copy/branding, not field names), so a
best-effort fill-by-known-selectors approach with graceful per-field
failure works better here than a bespoke script per company.

Playwright is imported lazily so the rest of the package (search, matching,
resume generation) works fine in environments without it installed / without
browser binaries available -- only `job_agent apply` needs it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FieldFillResult:
    filled: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    @property
    def all_required_ok(self) -> bool:
        return not self.failed


def try_fill(page, selectors: list[str], value: str, result: FieldFillResult, label: str) -> bool:
    for sel in selectors:
        try:
            locator = page.locator(sel).first
            if locator.count() > 0:
                locator.fill(value, timeout=3000)
                result.filled.append(label)
                return True
        except Exception:
            continue
    result.failed.append(label)
    return False


def try_upload(page, selectors: list[str], file_path: str | Path, result: FieldFillResult, label: str) -> bool:
    for sel in selectors:
        try:
            locator = page.locator(sel).first
            if locator.count() > 0:
                locator.set_input_files(str(file_path), timeout=5000)
                result.filled.append(label)
                return True
        except Exception:
            continue
    result.failed.append(label)
    return False


def launch_page(playwright, headless: bool = True):
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    return browser, page
