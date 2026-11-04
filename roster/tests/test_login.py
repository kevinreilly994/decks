import pytest
from django.contrib.auth.models import User

from .factories import make_dj


@pytest.mark.django_db
def test_login_page_renders_branding(client):
    resp = client.get("/login/")
    assert resp.status_code == 200
    assert b"booking room for house music" in resp.content
    assert b"DECKS" in resp.content


@pytest.mark.django_db
def test_unauthenticated_redirects_to_branded_login(client):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login/" in resp["Location"]
    assert "/admin/" not in resp["Location"]


@pytest.mark.django_db
def test_login_then_access_directory(client):
    User.objects.create_user("buyer", password="pw-12345!")
    make_dj(name="Nova Kane")
    resp = client.post("/login/", {"username": "buyer", "password": "pw-12345!"})
    assert resp.status_code == 302
    page = client.get("/")
    assert page.status_code == 200
    assert b"Nova Kane" in page.content


@pytest.mark.django_db
def test_logout_requires_post_and_redirects(client):
    User.objects.create_user("buyer", password="pw-12345!")
    client.login(username="buyer", password="pw-12345!")
    resp = client.post("/logout/")
    assert resp.status_code == 302
    assert client.get("/").status_code == 302  # protected again
