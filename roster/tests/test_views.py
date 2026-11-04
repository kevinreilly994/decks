import pytest
from django.contrib.auth.models import User

from roster.scoring import recompute_all

from .factories import make_dj


@pytest.fixture
def buyer_client(client, db):
    User.objects.create_user("buyer", password="pw-12345!")
    client.login(username="buyer", password="pw-12345!")
    return client


@pytest.mark.django_db
def test_directory_requires_login(client):
    assert client.get("/").status_code == 302


@pytest.mark.django_db
def test_directory_lists_djs(buyer_client):
    make_dj(name="Nova Kane")
    resp = buyer_client.get("/")
    assert resp.status_code == 200
    assert b"Nova Kane" in resp.content


@pytest.mark.django_db
def test_directory_genre_filter(buyer_client):
    make_dj(name="Nova Kane", genre="Melodic House")
    make_dj(name="Dexter Vale", genre="Tech House")
    resp = buyer_client.get("/?genre=tech-house")
    assert b"Dexter Vale" in resp.content
    assert b"Nova Kane" not in resp.content


@pytest.mark.django_db
def test_dj_detail_renders(buyer_client):
    dj = make_dj(name="Nova Kane")
    resp = buyer_client.get(f"/dj/{dj.slug}/")
    assert resp.status_code == 200
    assert b"Nova Kane" in resp.content


@pytest.mark.django_db
def test_leaderboard_renders(buyer_client):
    make_dj()
    recompute_all()
    assert buyer_client.get("/leaderboard/").status_code == 200


@pytest.mark.django_db
def test_shortlist_toggle_adds_then_lists(buyer_client):
    dj = make_dj(name="Nova Kane")
    r = buyer_client.post(f"/shortlist/toggle/{dj.id}/", {"next": "/shortlist/"})
    assert r.status_code == 302
    page = buyer_client.get("/shortlist/")
    assert b"Nova Kane" in page.content
