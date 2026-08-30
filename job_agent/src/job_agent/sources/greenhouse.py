"""Greenhouse job source adapter.

Uses Greenhouse's public, unauthenticated job board API
(https://developers.greenhouse.io/job-board.html) -- this is the same feed
that powers each company's own public careers page, so reading it carries no
ToS risk. Only Greenhouse boards you list in config are queried.
"""

from __future__ import annotations

import re
import sys

import requests

from ..models import JobPosting
from .base import JobSource

API_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "").strip()


class GreenhouseSource(JobSource):
    name = "greenhouse"

    def __init__(self, boards: list[str], country_filter: str | None = None):
        self.boards = boards
        self.country_filter = country_filter

    def search(self) -> list[JobPosting]:
        postings: list[JobPosting] = []
        for board in self.boards:
            try:
                resp = requests.get(API_URL.format(board=board), timeout=20)
                resp.raise_for_status()
            except requests.RequestException as exc:
                print(f"[greenhouse] failed to fetch board '{board}': {exc}", file=sys.stderr)
                continue
            for job in resp.json().get("jobs", []):
                location = (job.get("location") or {}).get("name", "") or ""
                if self.country_filter and self.country_filter.lower() not in location.lower():
                    continue
                postings.append(
                    JobPosting(
                        source=self.name,
                        external_id=str(job["id"]),
                        title=job.get("title", ""),
                        company=board,
                        location=location,
                        description=_strip_html(job.get("content", "")),
                        apply_url=job.get("absolute_url", ""),
                        remote="remote" in location.lower(),
                    )
                )
        return postings
