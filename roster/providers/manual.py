"""ManualProvider: the Phase 1 default.

Data is curated by hand in the admin, so this provider reports nothing to sync and
never overwrites manual entries. It exists to prove the seam end to end.
"""
from __future__ import annotations

from .base import DataProvider, EngagementDTO, ReleaseDTO, ShowDTO


class ManualProvider(DataProvider):
    name = "manual"

    def fetch_shows(self, dj) -> list[ShowDTO]:
        return []

    def fetch_releases(self, dj) -> list[ReleaseDTO]:
        return []

    def fetch_engagement(self, dj) -> EngagementDTO | None:
        return None
