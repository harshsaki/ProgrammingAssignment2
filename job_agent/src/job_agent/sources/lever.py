"""Lever job source adapter.

Uses Lever's public postings API (https://api.lever.co/v0/postings/<slug>),
the same read-only feed that powers each company's public jobs.lever.co
page. Only Lever company slugs you list in config are queried.
"""

from __future__ import annotations

import sys

import requests

from ..models import JobPosting
from .base import JobSource

API_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


class LeverSource(JobSource):
    name = "lever"

    def __init__(self, boards: list[str], country_filter: str | None = None):
        self.boards = boards
        self.country_filter = country_filter

    def search(self) -> list[JobPosting]:
        postings: list[JobPosting] = []
        for slug in self.boards:
            try:
                resp = requests.get(API_URL.format(slug=slug), timeout=20)
                resp.raise_for_status()
            except requests.RequestException as exc:
                print(f"[lever] failed to fetch board '{slug}': {exc}", file=sys.stderr)
                continue
            for job in resp.json():
                categories = job.get("categories", {}) or {}
                location = categories.get("location", "") or ""
                if self.country_filter and self.country_filter.lower() not in location.lower():
                    continue
                description = job.get("descriptionPlain") or job.get("description") or ""
                postings.append(
                    JobPosting(
                        source=self.name,
                        external_id=str(job["id"]),
                        title=job.get("text", ""),
                        company=slug,
                        location=location,
                        description=description,
                        apply_url=job.get("applyUrl") or job.get("hostedUrl", ""),
                        remote="remote" in location.lower(),
                    )
                )
        return postings
