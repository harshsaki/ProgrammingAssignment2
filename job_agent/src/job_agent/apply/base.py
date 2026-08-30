from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import ApplicationRecord, GeneratedApplication


class ApplyEngine(ABC):
    """Interface for anything that turns a GeneratedApplication into a
    submitted (or staged) application."""

    @abstractmethod
    def submit(self, application: GeneratedApplication, dry_run: bool) -> ApplicationRecord:
        raise NotImplementedError
