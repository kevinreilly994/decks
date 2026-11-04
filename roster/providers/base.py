"""Swappable data-provider interface (Phase 1 seam).

Phase 1 ships only ManualProvider. Phase 3+ adds Spotify / Bandsintown / Instagram
providers behind this same contract, so the rest of the app never changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class ShowDTO:
    date: date
    event_name: str
    venue_city: str
    status: str = "offer"


@dataclass
class ReleaseDTO:
    title: str
    released_on: date
    label: str = ""
    play_count: int | None = None
    url: str = ""


@dataclass
class EngagementDTO:
    captured_on: date
    spotify_monthly: int | None = None
    instagram_followers: int | None = None
    tiktok_followers: int | None = None
    soundcloud_followers: int | None = None
    engagement_rate: float | None = None


class DataProvider(ABC):
    name: str = "base"

    @abstractmethod
    def fetch_shows(self, dj) -> list[ShowDTO]: ...

    @abstractmethod
    def fetch_releases(self, dj) -> list[ReleaseDTO]: ...

    @abstractmethod
    def fetch_engagement(self, dj) -> EngagementDTO | None: ...
