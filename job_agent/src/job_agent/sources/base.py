from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import JobPosting


class JobSource(ABC):
    """Interface every job source adapter implements. Keeping this thin
    means adding a new source (e.g. a company's own careers API) is a
    single new file, no changes to the orchestrator."""

    name: str

    @abstractmethod
    def search(self) -> list[JobPosting]:
        """Return normalized JobPosting objects matching this source's
        configured criteria. Must not raise on an empty/no-match result --
        return an empty list instead."""
        raise NotImplementedError
