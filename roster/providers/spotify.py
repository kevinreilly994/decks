"""Spotify provider (Phase 3).

Client Credentials flow. Reads SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET from
settings and maps a DJ (by spotify_artist_id) to follower count + top-track
releases. Requires the `requests` package, imported lazily so the module loads
without it (and so tests can inject a fake session).
"""
from __future__ import annotations

import base64
from urllib.parse import quote
from datetime import date, datetime

from django.conf import settings

from .base import DataProvider, EngagementDTO, ReleaseDTO, ShowDTO

TOKEN_URL = "https://accounts.spotify.com/api/token"
API = "https://api.spotify.com/v1"


def _parse_date(value):
    if not value:
        return date.today()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return date.today()


class SpotifyProvider(DataProvider):
    name = "spotify"

    def __init__(self, session=None, token=None):
        self._session = session
        self._token = token

    @staticmethod
    def is_configured() -> bool:
        return bool(
            getattr(settings, "SPOTIFY_CLIENT_ID", "")
            and getattr(settings, "SPOTIFY_CLIENT_SECRET", "")
        )

    def _client(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
        return self._session

    def _access_token(self) -> str:
        if self._token:
            return self._token
        raw = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
        auth = base64.b64encode(raw.encode()).decode()
        resp = self._client().post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth}"},
            timeout=15,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _get(self, path: str):
        resp = self._client().get(
            f"{API}{path}",
            headers={"Authorization": f"Bearer {self._access_token()}"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def fetch_shows(self, dj) -> list[ShowDTO]:
        return []  # Spotify has no show data; see BandsintownProvider.

    def fetch_releases(self, dj) -> list[ReleaseDTO]:
        if not dj.spotify_artist_id:
            return []
        # top-tracks is restricted for API apps; use the albums endpoint instead.
        aid = quote(dj.spotify_artist_id, safe="")
        data = self._get(f"/artists/{aid}/albums?market=US&limit=10")
        seen = set()
        out = []
        items = sorted(
            data.get("items", []),
            key=lambda a: a.get("release_date", ""),
            reverse=True,
        )
        for album in items:
            if album.get("album_type") not in ("single", "album"):
                continue
            title = album.get("name", "")
            key = title.lower()
            if not title or key in seen:
                continue
            seen.add(key)
            out.append(ReleaseDTO(
                title=title,
                released_on=_parse_date(album.get("release_date")),
                label=album.get("album_type", ""),
                url=album.get("external_urls", {}).get("spotify", ""),
            ))
            if len(out) >= 6:
                break
        return out

    def fetch_engagement(self, dj) -> EngagementDTO | None:
        # Spotify's API no longer exposes follower/listener counts to this app tier.
        return None
