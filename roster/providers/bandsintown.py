"""Bandsintown provider (Phase 3).

Reads BANDSINTOWN_APP_ID from settings and maps a DJ (by bandsintown_artist, or
the DJ name) to upcoming events -> ShowDTO. Requires `requests` (lazy import).
"""
from __future__ import annotations

from datetime import date, datetime
from urllib.parse import quote

from django.conf import settings

from .base import DataProvider, EngagementDTO, ReleaseDTO, ShowDTO

API = "https://rest.bandsintown.com"


def _parse_dt(value):
    if not value:
        return date.today()
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return date.today()


class BandsintownProvider(DataProvider):
    name = "bandsintown"

    def __init__(self, session=None):
        self._session = session

    @staticmethod
    def is_configured() -> bool:
        return bool(getattr(settings, "BANDSINTOWN_APP_ID", ""))

    def _client(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
        return self._session

    def _artist_name(self, dj) -> str:
        return dj.bandsintown_artist or dj.name

    def fetch_shows(self, dj) -> list[ShowDTO]:
        name = quote(self._artist_name(dj), safe="")
        resp = self._client().get(
            f"{API}/artists/{name}/events",
            params={"app_id": settings.BANDSINTOWN_APP_ID, "date": "upcoming"},
            timeout=15,
        )
        resp.raise_for_status()
        events = resp.json()
        if not isinstance(events, list):
            return []
        out = []
        for event in events:
            venue = event.get("venue", {})
            city = ", ".join(
                part for part in (venue.get("city"), venue.get("country")) if part
            )
            out.append(ShowDTO(
                date=_parse_dt(event.get("datetime")),
                event_name=venue.get("name") or "Live show",
                venue_city=city or "TBA",
                status="confirmed",
            ))
        return out

    def fetch_releases(self, dj) -> list[ReleaseDTO]:
        return []

    def fetch_engagement(self, dj) -> EngagementDTO | None:
        return None
