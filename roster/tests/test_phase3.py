from datetime import date
from io import StringIO

import pytest
from django.core.management import call_command

from roster.providers import available_providers, sync_dj
from roster.providers.bandsintown import BandsintownProvider
from roster.providers.base import DataProvider, EngagementDTO, ReleaseDTO, ShowDTO
from roster.providers.spotify import SpotifyProvider

from .factories import make_dj


class FakeResp:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class FakeSpotifySession:
    def post(self, *a, **k):
        return FakeResp({"access_token": "tok"})

    def get(self, url, headers=None, timeout=None):
        if "top-tracks" in url:
            return FakeResp({"tracks": [{
                "name": "Solstice",
                "album": {"name": "Afterlife", "release_date": "2025-06-01"},
                "external_urls": {"spotify": "http://x"},
            }]})
        return FakeResp({"followers": {"total": 3_410_000}})


class FakeBITSession:
    def get(self, url, params=None, timeout=None):
        return FakeResp([{
            "datetime": "2026-12-06T22:00:00",
            "venue": {"name": "Printworks", "city": "London", "country": "UK"},
        }])


def test_registry_has_live_providers():
    assert {"spotify", "bandsintown"} <= set(available_providers())


@pytest.mark.django_db
def test_spotify_maps_releases_and_followers():
    dj = make_dj()
    dj.spotify_artist_id = "abc123"
    dj.save()
    provider = SpotifyProvider(session=FakeSpotifySession(), token="tok")
    releases = provider.fetch_releases(dj)
    assert releases[0].title == "Solstice"
    assert releases[0].released_on == date(2025, 6, 1)
    assert provider.fetch_engagement(dj).spotify_monthly == 3_410_000


@pytest.mark.django_db
def test_bandsintown_maps_shows():
    dj = make_dj()
    shows = BandsintownProvider(session=FakeBITSession()).fetch_shows(dj)
    assert shows[0].event_name == "Printworks"
    assert shows[0].venue_city == "London, UK"
    assert shows[0].status == "confirmed"


class StubProvider(DataProvider):
    name = "stub"

    def fetch_shows(self, dj):
        return [ShowDTO(date(2026, 12, 6), "Printworks", "London, UK", "confirmed")]

    def fetch_releases(self, dj):
        return [ReleaseDTO("Solstice", date(2025, 6, 1), "Afterlife")]

    def fetch_engagement(self, dj):
        return EngagementDTO(date(2026, 11, 2), spotify_monthly=123)


@pytest.mark.django_db
def test_sync_dj_creates_rows_stamped_by_provider():
    dj = make_dj()
    counts = sync_dj(dj, StubProvider())
    assert counts == {"shows": 1, "releases": 1, "engagement": 1}
    assert dj.shows.filter(source="stub").count() == 1
    assert dj.releases.filter(source="stub").count() == 1
    assert dj.snapshots.filter(captured_on=date(2026, 11, 2)).exists()


@pytest.mark.django_db
def test_sync_roster_skips_unconfigured_providers():
    make_dj()
    out = StringIO()
    call_command("sync_roster", stdout=out)
    assert "nothing synced" in out.getvalue().lower()


@pytest.mark.django_db
def test_sync_roster_dry_run_writes_nothing():
    dj = make_dj()
    out = StringIO()
    call_command("sync_roster", "--provider", "manual", dry_run=True, stdout=out)
    assert "dry-run" in out.getvalue().lower()
    assert dj.shows.count() == 0


@pytest.mark.django_db
def test_sync_roster_reports_unknown_provider():
    make_dj()
    err = StringIO()
    call_command("sync_roster", "--provider", "nope", stdout=StringIO(), stderr=err)
    assert "unknown provider" in err.getvalue().lower()


def test_sparkline_needs_two_points():
    from roster.charts import sparkline
    assert sparkline([5]) is None
    assert sparkline([]) is None


def test_sparkline_builds_points():
    from roster.charts import sparkline
    sp = sparkline([1, 2, 3, 4])
    assert sp is not None
    assert sp["line"].count(",") == 4
    assert sp["width"] and sp["height"]
