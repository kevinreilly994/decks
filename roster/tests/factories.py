"""Tiny helpers for building roster objects in tests."""
from datetime import date

from roster.models import DJ, EngagementSnapshot, Genre, Show, ShowStatus


def make_dj(name="Test DJ", genre="Melodic House", spotify=1_000_000, ig=500_000,
            tk=0, sc=0, eng=5.0, confirmed_shows=0):
    g, _ = Genre.objects.get_or_create(name=genre)
    dj = DJ.objects.create(name=name, primary_genre=g, home_base="Testville")
    EngagementSnapshot.objects.create(
        dj=dj, captured_on=date(2026, 11, 1), spotify_monthly=spotify,
        instagram_followers=ig, tiktok_followers=tk, soundcloud_followers=sc,
        engagement_rate=eng,
    )
    for i in range(confirmed_shows):
        Show.objects.create(
            dj=dj, date=date(2026, 12, 1), event_name=f"Show {i}",
            venue_city="City", status=ShowStatus.CONFIRMED,
        )
    return dj
