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
def test_spotify_releases_empty_when_no_albums():
    dj = make_dj()
    dj.spotify_artist_id = "abc123"
    dj.save()
    provider = SpotifyProvider(session=FakeSpotifySession(), token="tok")
    assert provider.fetch_releases(dj) == []


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
def test_sync_roster_skips_unconfigured_providers(settings):
    settings.SPOTIFY_CLIENT_ID = ""
    settings.SPOTIFY_CLIENT_SECRET = ""
    settings.BANDSINTOWN_APP_ID = ""
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


class FakeAlbumsSession:
    def post(self, *a, **k):
        return FakeResp({"access_token": "tok"})

    def get(self, url, headers=None, timeout=None):
        return FakeResp({"items": [
            {"name": "Night One", "release_date": "2025-06-01", "album_type": "single",
             "external_urls": {"spotify": "http://x"}},
            {"name": "Night One", "release_date": "2025-06-01", "album_type": "single",
             "external_urls": {"spotify": "http://x"}},
            {"name": "Day Two", "release_date": "2024-01-01", "album_type": "album",
             "external_urls": {"spotify": "http://y"}},
        ]})


@pytest.mark.django_db
def test_spotify_releases_from_albums_dedup_and_sorted():
    dj = make_dj()
    dj.spotify_artist_id = "abc"
    dj.save()
    rels = SpotifyProvider(session=FakeAlbumsSession(), token="tok").fetch_releases(dj)
    assert [r.title for r in rels] == ["Night One", "Day Two"]
    assert rels[0].released_on.year == 2025


@pytest.mark.django_db
def test_spotify_engagement_is_none_now():
    dj = make_dj()
    dj.spotify_artist_id = "abc"
    dj.save()
    assert SpotifyProvider(session=FakeAlbumsSession(), token="tok").fetch_engagement(dj) is None


@pytest.mark.django_db
def test_sync_providers_action_without_creds(client, settings):
    from django.contrib.auth.models import User
    settings.SPOTIFY_CLIENT_ID = ""
    settings.SPOTIFY_CLIENT_SECRET = ""
    settings.BANDSINTOWN_APP_ID = ""
    User.objects.create_superuser("adm2", "a2@x.com", "pw-12345!")
    client.force_login(User.objects.get(username="adm2"))
    dj = make_dj()
    resp = client.post(
        "/admin/roster/dj/",
        {"action": "sync_providers", "_selected_action": [str(dj.id)]},
        follow=True,
    )
    assert resp.status_code == 200
    assert dj.releases.count() == 0


def test_s3_storage_backend_importable():
    import importlib
    assert importlib.import_module("storages.backends.s3") is not None
