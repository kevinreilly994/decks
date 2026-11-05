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


@pytest.mark.django_db
def test_shortlist_toggle_blocks_open_redirect(buyer_client):
    dj = make_dj()
    resp = buyer_client.post(f"/shortlist/toggle/{dj.id}/", {"next": "https://evil.example/x"})
    assert resp.status_code == 302
    assert "evil.example" not in resp["Location"]


@pytest.mark.django_db
def test_directory_renders_next_show_via_prefetch(buyer_client):
    make_dj(name="Nova Kane", confirmed_shows=1)  # creates show "Show 0"
    resp = buyer_client.get("/")
    assert resp.status_code == 200
    assert b"Show 0" in resp.content


@pytest.mark.django_db
def test_directory_query_count_is_constant(buyer_client, django_assert_max_num_queries):
    for i in range(10):
        make_dj(name=f"DJ {i}", confirmed_shows=2)
    # With Prefetch + prefetch-aware helpers this must NOT scale with DJ count.
    with django_assert_max_num_queries(12):
        resp = buyer_client.get("/")
    assert resp.status_code == 200
