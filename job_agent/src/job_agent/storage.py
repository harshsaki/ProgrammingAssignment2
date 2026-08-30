"""Lightweight JSON/CSV-backed persistence for dedup tracking and an
applications log. No database server required, deliberately -- this tool is
meant to run as a scheduled local/CI job, not a service."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from .models import ApplicationRecord


class SeenJobsStore:
    """Tracks which job postings we've already processed, so re-runs don't
    generate duplicate applications for the same posting."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seen: set[str] = set()
        if self.path.exists():
            self._seen = set(json.loads(self.path.read_text() or "[]"))

    def has_seen(self, dedup_key: str) -> bool:
        return dedup_key in self._seen

    def mark_seen(self, dedup_key: str) -> None:
        self._seen.add(dedup_key)

    def save(self) -> None:
        self.path.write_text(json.dumps(sorted(self._seen), indent=2))


class ApplicationsLog:
    """Append-only CSV log of every application generated/staged/submitted,
    for tracking your funnel (applied -> callback -> interview)."""

    FIELDS = ["timestamp", "source", "company", "title", "status", "detail", "apply_url"]

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=self.FIELDS).writeheader()

    def append(self, record: ApplicationRecord) -> None:
        with open(self.path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS)
            writer.writerow(
                {
                    "timestamp": record.timestamp,
                    "source": record.job.source,
                    "company": record.job.company,
                    "title": record.job.title,
                    "status": record.status,
                    "detail": record.detail,
                    "apply_url": record.job.apply_url,
                }
            )

    def daily_count(self, day_iso_prefix: str) -> int:
        if not self.path.exists():
            return 0
        count = 0
        with open(self.path, newline="") as f:
            for row in csv.DictReader(f):
                if row["timestamp"].startswith(day_iso_prefix) and row["status"] in (
                    "submitted",
                    "dry_run",
                ):
                    count += 1
        return count
