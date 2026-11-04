"""Maps provider DTOs onto the roster models.

Manual data is never clobbered: rows are keyed by natural fields and stamped with
the provider name so a later real provider only updates its own rows.
"""
from __future__ import annotations

from .base import DataProvider
from ..models import EngagementSnapshot, Release, Show


def sync_dj(dj, provider: DataProvider) -> dict[str, int]:
    counts = {"shows": 0, "releases": 0, "engagement": 0}

    for s in provider.fetch_shows(dj):
        Show.objects.update_or_create(
            dj=dj, event_name=s.event_name, date=s.date,
            defaults={"venue_city": s.venue_city, "status": s.status, "source": provider.name},
        )
        counts["shows"] += 1

    for r in provider.fetch_releases(dj):
        Release.objects.update_or_create(
            dj=dj, title=r.title,
            defaults={"released_on": r.released_on, "label": r.label,
                      "play_count": r.play_count, "url": r.url, "source": provider.name},
        )
        counts["releases"] += 1

    eng = provider.fetch_engagement(dj)
    if eng:
        EngagementSnapshot.objects.update_or_create(
            dj=dj, captured_on=eng.captured_on,
            defaults={"spotify_monthly": eng.spotify_monthly,
                      "instagram_followers": eng.instagram_followers,
                      "tiktok_followers": eng.tiktok_followers,
                      "soundcloud_followers": eng.soundcloud_followers,
                      "engagement_rate": eng.engagement_rate, "source": provider.name},
        )
        counts["engagement"] += 1

    return counts
